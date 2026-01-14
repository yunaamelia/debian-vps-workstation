"""
Base class for all configuration modules.

Provides the interface that all modules must implement.
"""

import logging
import os
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from configurator.core.dryrun import DryRunManager
from configurator.core.network import NetworkOperationWrapper
from configurator.core.package_cache import PackageCacheManager
from configurator.core.rollback import RollbackManager
from configurator.exceptions import ModuleExecutionError
from configurator.utils.apt_cache import AptCacheIntegration
from configurator.utils.circuit_breaker import CircuitBreakerError, CircuitBreakerManager
from configurator.utils.command import CommandResult, run_command
from configurator.utils.retry import retry


class ConfigurationModule(ABC):
    """
    Abstract base class for all configuration modules.
    """

    # Global lock for APT operations to prevent parallel execution failures
    _APT_LOCK = threading.Lock()

    # Module metadata - override in subclasses
    name: str = "Base Module"
    description: str = "Base configuration module"
    priority: int = 100
    depends_on: List[str] = []
    force_sequential: bool = False  # If True, runs alone in a batch
    mandatory: bool = False  # If True, installation stops on failure

    def __init__(
        self,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
        rollback_manager: Optional[RollbackManager] = None,
        dry_run_manager: Optional["DryRunManager"] = None,
        circuit_breaker_manager: Optional[CircuitBreakerManager] = None,
        package_cache_manager: Optional[PackageCacheManager] = None,
    ):
        """
        Initialize the module.

        Args:
            config: Module-specific configuration
            logger: Logger instance
            rollback_manager: Rollback manager for tracking changes
            dry_run_manager: Manager for dry-run recording
            circuit_breaker_manager: Manager for circuit breakers
            package_cache_manager: Manager for package caching
        """
        self.config = config
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.rollback_manager = rollback_manager or RollbackManager()
        self.dry_run_manager = dry_run_manager
        self.circuit_breaker_manager = circuit_breaker_manager or CircuitBreakerManager()
        self.package_cache_manager = package_cache_manager

        # Initialize APT Cache Integration if manager is available
        self.apt_cache_integration = None
        if self.package_cache_manager:
            self.apt_cache_integration = AptCacheIntegration(
                self.package_cache_manager, self.logger
            )

        # Initialize network wrapper for resilient operations
        self.network = NetworkOperationWrapper(config=config, logger=self.logger)

        # Dry run state
        self.dry_run = dry_run_manager.is_enabled if dry_run_manager else False

        # State tracking
        self.state: Dict[str, Any] = {}
        self.installed_packages: List[str] = []
        self.started_services: List[str] = []

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate prerequisites before installation.

        Check that all requirements are met before attempting installation.
        This might include checking for existing installations, available
        disk space, network connectivity, etc.

        Returns:
            True if ready to install, False otherwise

        Raises:
            PrerequisiteError with helpful message if validation fails
        """

    @abstractmethod
    def configure(self) -> bool:
        """
        Execute configuration/installation.

        This is the main method that performs the actual work.
        Should register rollback actions for any changes made.

        Returns:
            True if successful

        Raises:
            ModuleExecutionError with helpful message on failure
        """

    @abstractmethod
    def verify(self) -> bool:
        """
        Verify installation was successful.

        Check that everything is working correctly after installation.
        This might include checking service status, running test commands,
        verifying file permissions, etc.

        Returns:
            True if verified successfully
        """

    def rollback(self) -> bool:
        """
        Rollback changes made by this module.

        Default implementation uses the rollback manager.
        Override if custom rollback logic is needed.

        Returns:
            True if rollback was successful
        """
        return self.rollback_manager.rollback()

    # Utility methods for subclasses

    def run(
        self,
        command: str,
        check: bool = True,
        rollback_command: Optional[str] = None,
        description: str = "",
        force_execute: bool = False,
        **kwargs: Any,
    ) -> CommandResult:
        """
        Run a shell command.

        Args:
            command: Command content
            check: Raise exception if command fails
            rollback_command: Command to run if this command needs rollback
            description: Description of the command (for logs/UI)
            force_execute: Execute command even in dry-run mode (use checks)
            **kwargs: Additional arguments for run_command
        """
        if description:
            self.logger.debug(f"Running: {description}")
        else:
            self.logger.debug(f"Running: {command}")

        # Dry run check
        if self.dry_run and not force_execute:
            if self.dry_run_manager:
                self.dry_run_manager.record_command(command)
            return CommandResult(command=command, return_code=0, stdout="", stderr="")

        # Default to shell=True to support pipes and redirects unless explicitly disabled
        if "shell" not in kwargs:
            kwargs["shell"] = True

        result = run_command(command, check=check, **kwargs)

        if rollback_command and result.success:
            self.rollback_manager.add_command(
                rollback_command, description=f"Rollback: {description or command}"
            )

        return result

    def install_packages_resilient(self, packages: List[str], update_cache: bool = True) -> bool:
        """
        Install packages with network resilience.

        This is the preferred method for package installation as it includes:
        - Circuit breaker protection
        - Automatic retry with exponential backoff
        - Proper timeout handling
        - Rollback registration

        Args:
            packages: List of package names
            update_cache: Update APT cache first

        Returns:
            True if successful
        """
        if not packages:
            return True

        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_package_install(packages)
            return True

        # Use network wrapper for resilient installation
        with self._APT_LOCK:
            success = self.network.apt_install_with_retry(packages, update_cache)

            if success:
                # Register for rollback
                for package in packages:
                    self.rollback_manager.register_action(
                        f"remove_package_{package}",
                        lambda p=package: self.run(f"apt-get remove -y {p}", check=False),
                    )

                self.installed_packages.extend(packages)

            return success

    @retry(max_retries=20, base_delay=5.0)
    def install_packages(
        self,
        packages: List[str],
        update_cache: bool = True,
    ) -> bool:
        """
        Install APT packages.

        Args:
            packages: List of package names
            update_cache: Run apt-get update first

        Returns:
            True if installation was successful
        """
        if not packages:
            return True

        self.logger.info(f"Installing packages: {', '.join(packages)}")

        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_package_install(packages)
            return True

        # Acquire lock to prevent parallel APT operations
        with self._APT_LOCK:
            if update_cache:
                # Retry apt-get update if another process has the lock
                for retry_attempt in range(3):
                    result = self.run("apt-get update", check=False)
                    if result.return_code == 0:
                        break
                    if (
                        "Could not get lock" in result.stderr
                        or "Could not get lock" in result.stdout
                    ):
                        if retry < 2:
                            self.logger.debug(f"APT lock busy, waiting... (attempt {retry + 1}/3)")
                            import time

                            time.sleep(5)
                        else:
                            self.logger.warning(
                                "APT lock still busy after retries, continuing anyway"
                            )
                    else:
                        break

            # Pre-populate APT cache from our local cache
            if self.apt_cache_integration and not self.dry_run:
                try:
                    self.apt_cache_integration.prepare_apt_cache(packages)
                except Exception as e:
                    self.logger.warning(f"Failed to prepare package cache: {e}")

            # Install packages
            packages_str = " ".join(packages)

            env = os.environ.copy()
            env["DEBIAN_FRONTEND"] = "noninteractive"

            def _install():
                # Retry install if another process has the lock
                for retry_attempt in range(3):
                    result = self.run(
                        f"apt-get install -y {packages_str}",
                        check=False,
                        env=env,
                    )
                    if result.return_code == 0:
                        return result
                    if (
                        "Could not get lock" in result.stderr
                        or "Could not get lock" in result.stdout
                    ):
                        if retry < 2:
                            self.logger.debug(
                                f"APT lock busy during install, waiting... (attempt {retry + 1}/3)"
                            )
                            import time

                            time.sleep(5)
                        else:
                            # Final retry failed, raise error
                            raise ModuleExecutionError(
                                what=f"Cannot install packages: {packages_str}",
                                why="APT/dpkg lock is held by another process",
                                how="Wait for other package operations to complete or run: sudo lsof /var/lib/dpkg/lock-frontend",
                            )
                    else:
                        # Different error, raise it
                        if result.return_code != 0:
                            raise ModuleExecutionError(
                                what=f"Command failed: apt-get install -y {packages_str}",
                                why=f"Exit code: {result.return_code}\n{result.stderr}",
                                how="""Check the command output above for details. You may need to:
1. Check if required packages are installed
2. Verify you have the necessary permissions
3. Check your internet connection""",
                            )
                        return result
                return result

            # Get apt circuit breaker
            breaker = self.circuit_breaker_manager.get_breaker(
                "apt-repository",
                failure_threshold=3,
                timeout=60.0,
            )

            try:
                # Execute through circuit breaker
                result = breaker.call(_install)
            except CircuitBreakerError as e:
                self.logger.debug(f"Circuit breaker open for apt: {e}")

                # Ask user if they want to wait or skip
                if self.config.get("interactive"):
                    import time

                    print(f"\n[!] Circuit breaker is OPEN. Retry in {e.retry_after:.0f}s.")
                    choice = input(f"Wait {e.retry_after:.0f}s and retry? (y/n): ")
                    if choice.lower() == "y":
                        self.logger.info("User requested wait and retry.")
                        time.sleep(e.retry_after)
                        breaker.reset()  # Manual reset
                        # Recursive retry could be dangerous, but for this specific "single package" loop it's okay
                        # IF we assume it returns controlling to the loop.
                        # Actually, we are inside the loop for packages.
                        # We should `continue` the loop if we want to retry THIS package.
                        # But `_install` executes the batch.
                        # Wait, `install_packages` executes `_install` which does `apt-get install` for ALL `packages` at once or one by one?
                        # The code says `packages_str = " ".join(packages)`, so it's a batch.
                        # So simply retrying the same call is what we want.
                        return self.install_packages(packages, update_cache=False)

                raise ModuleExecutionError(
                    what=f"Cannot install packages: {', '.join(packages)}",
                    why="APT repository appears to be down or unreachable",
                    how="""
Try these steps:
1. Check internet connectivity:  ping -c 3 deb.debian.org
2. Check APT sources: cat /etc/apt/sources.list
3. Update package lists: sudo apt-get update
4. Wait and try again (repository might be temporarily down)
5. Manual reset: vps-configurator reset circuit-breaker apt-repository
""",
                )

            if result.success:
                self.installed_packages.extend(packages)
                self.rollback_manager.add_package_remove(
                    packages,
                    description=f"Remove packages: {', '.join(packages)}",
                )

                # Capture downloaded packages to our local cache
                if self.apt_cache_integration and not self.dry_run:
                    try:
                        self.apt_cache_integration.capture_new_packages()
                    except Exception as e:
                        self.logger.warning(f"Failed to update package cache: {e}")

            return result.success

    def enable_service(self, service: str, start: bool = True) -> bool:
        """
        Enable and optionally start a systemd service.

        Args:
            service: Service name
            start: Also start the service

        Returns:
            True if successful
        """
        self.logger.info(f"Enabling service: {service}")

        if self.dry_run:
            if self.dry_run_manager:
                action = "start" if start else "enable"
                self.dry_run_manager.record_service_action(service, action)
            return True

        self.run(f"systemctl enable {service}", check=True)

        if start:
            self.run(f"systemctl start {service}", check=True)
            self.started_services.append(service)
            self.rollback_manager.add_service_stop(service)

        return True

    def restart_service(self, service: str) -> bool:
        """
        Restart a systemd service.

        Args:
            service: Service name

        Returns:
            True if successful
        """
        self.logger.info(f"Restarting service: {service}")

        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_service_action(service, "restart")
            return True

        result = self.run(f"systemctl restart {service}", check=False)
        return result.success

    def is_service_active(self, service: str) -> bool:
        """
        Check if a systemd service is running.

        Args:
            service: Service name

        Returns:
            True if service is active
        """
        # Always run check commands (read-only)
        result = self.run(f"systemctl is-active {service}", check=False, force_execute=True)
        return result.stdout.strip() == "active"

    def command_exists(self, command: str) -> bool:
        """
        Check if a command exists.

        Args:
            command: Command name

        Returns:
            True if command exists
        """
        # Always run check commands
        result = self.run(f"which {command}", check=False, force_execute=True)
        return result.success

    def write_file(
        self, path: str, content: str, mode: str = "w", backup: bool = False, **kwargs
    ) -> None:
        """
        Write content to file (with dry-run support).
        """
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_file_write(path, content)
            return

        from configurator.utils.file import write_file as utils_write_file

        utils_write_file(path, content, mode=mode, backup=backup, **kwargs)

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value
