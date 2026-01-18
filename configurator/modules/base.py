"""
Base class for all configuration modules.

Provides the interface that all modules must implement.
"""

import logging
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from configurator.core.dryrun import DryRunManager
from configurator.core.network import NetworkOperationWrapper
from configurator.core.package_cache import PackageCacheManager
from configurator.core.rollback import RollbackManager
from configurator.exceptions import ModuleExecutionError
from configurator.observability.metrics import get_metrics
from configurator.observability.structured_logging import StructuredLogger
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

        # Observability
        self.metrics = get_metrics()
        self.structured_logger = StructuredLogger(self.name)

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
                self.rollback_manager.add_package_remove(
                    packages, description=f"Remove packages: {', '.join(packages)}"
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

        # Wrap in loop for retry
        while True:
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
                            if retry_attempt < 2:
                                self.logger.debug(
                                    f"APT lock busy, waiting... (attempt {retry_attempt + 1}/3)"
                                )
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

                def _install(packages_str=packages_str, env=env):
                    # Retry install if another process has the lock or dpkg was interrupted
                    for retry_attempt in range(3):
                        result = self.run(
                            f"apt-get install -y {packages_str}",
                            check=False,
                            env=env,
                        )
                        if result.return_code == 0:
                            return result

                        # Handle APT lock issues
                        if (
                            "Could not get lock" in result.stderr
                            or "Could not get lock" in result.stdout
                        ):
                            if retry_attempt < 2:
                                self.logger.debug(
                                    f"APT lock busy during install, waiting... (attempt {retry_attempt + 1}/3)"
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
                        # Handle dpkg interrupted errors
                        elif (
                            "dpkg was interrupted" in result.stderr
                            or "you must manually run 'dpkg --configure -a'" in result.stderr
                        ):
                            # #region agent log
                            import json

                            try:
                                with open(
                                    "/home/racoon/Desktop/debian-vps-workstation/.cursor/debug.log",
                                    "a",
                                ) as f:
                                    f.write(
                                        json.dumps(
                                            {
                                                "sessionId": "debug-session",
                                                "runId": "dpkg-fix",
                                                "hypothesisId": "B",
                                                "location": "configurator/modules/base.py:_install",
                                                "message": "dpkg interrupted detected",
                                                "data": {
                                                    "retry_attempt": retry_attempt,
                                                    "stderr": result.stderr[:200],
                                                },
                                                "timestamp": int(time.time() * 1000),
                                            }
                                        )
                                        + "\n"
                                    )
                            except Exception:
                                pass
                            # #endregion
                            if retry_attempt == 0:
                                self.logger.info(
                                    "dpkg was interrupted, fixing with 'dpkg --configure -a'..."
                                )
                                self.logger.info(
                                    "Note: This operation may take several minutes without output..."
                                )
                                # #region agent log
                                import json

                                try:
                                    with open(
                                        "/home/racoon/Desktop/debian-vps-workstation/.cursor/debug.log",
                                        "a",
                                    ) as f:
                                        f.write(
                                            json.dumps(
                                                {
                                                    "sessionId": "debug-session",
                                                    "runId": "dpkg-fix",
                                                    "hypothesisId": "B",
                                                    "location": "configurator/modules/base.py:_install",
                                                    "message": "Running dpkg --configure -a",
                                                    "data": {},
                                                    "timestamp": int(time.time() * 1000),
                                                }
                                            )
                                            + "\n"
                                        )
                                except Exception:
                                    pass
                                # #endregion
                                # Run dpkg --configure -a with progress output to avoid timeout
                                fix_result = self.run(
                                    r"dpkg --configure -a 2>&1 | while IFS= read -r line; do echo \"[dpkg-fix] $line\"; done",
                                    check=False,
                                    env=env,
                                )
                                # #region agent log
                                try:
                                    with open(
                                        "/home/racoon/Desktop/debian-vps-workstation/.cursor/debug.log",
                                        "a",
                                    ) as f:
                                        f.write(
                                            json.dumps(
                                                {
                                                    "sessionId": "debug-session",
                                                    "runId": "dpkg-fix",
                                                    "hypothesisId": "B",
                                                    "location": "configurator/modules/base.py:_install",
                                                    "message": "dpkg --configure -a completed",
                                                    "data": {
                                                        "return_code": fix_result.return_code,
                                                        "success": fix_result.return_code == 0,
                                                    },
                                                    "timestamp": int(time.time() * 1000),
                                                }
                                            )
                                            + "\n"
                                        )
                                except Exception:
                                    pass
                                # #endregion
                                if fix_result.return_code == 0:
                                    self.logger.info(
                                        "✓ dpkg configuration fixed, retrying package installation..."
                                    )
                                    continue  # Retry the installation
                                else:
                                    self.logger.warning(
                                        f"dpkg --configure -a failed: {fix_result.stderr}"
                                    )
                            # If fix didn't work or we've already tried, raise error
                            raise ModuleExecutionError(
                                what=f"Cannot install packages: {packages_str}",
                                why=f"dpkg was interrupted and could not be automatically fixed.\n{result.stderr}",
                                how="""Try manually fixing dpkg:
    1. Run: sudo dpkg --configure -a
    2. Run: sudo apt-get install -f
    3. Then retry the installation""",
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
                            # Release lock during wait?
                            # No, logic was to wait then retry.
                            # But if we wait inside the lock, we hold it.
                            # The original request was to replace recursion with loop.
                            # And we can sleep here.
                            time.sleep(e.retry_after)
                            breaker.reset()  # Manual reset
                            continue

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

        # Check if already enabled to avoid symlink conflicts
        if not self.is_service_enabled(service):
            # Handle case where file exists but service is not enabled
            # (happens when install script copies file instead of symlinking)
            enable_result = self.run(f"systemctl enable {service}", check=False)
            if not enable_result.success and "already exists" in enable_result.stderr:
                self.logger.debug(f"Fixing broken service symlink for {service}")
                # Remove the file and retry
                self.run(
                    f"rm -f /etc/systemd/system/multi-user.target.wants/{service}.service",
                    check=False,
                )
                self.run(f"systemctl enable {service}", check=True)
            elif not enable_result.success:
                # Re-raise for other errors
                enable_result.check_returncode()
        else:
            self.logger.debug(f"Service {service} already enabled")

        if start:
            # Check if already running
            if not self.is_service_active(service):
                self.run(f"systemctl start {service}", check=True)
                self.started_services.append(service)
                self.rollback_manager.add_service_stop(service)
            else:
                self.logger.debug(f"Service {service} already running")

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

    def is_service_enabled(self, service: str) -> bool:
        """
        Check if a systemd service is enabled.

        Args:
            service: Service name

        Returns:
            True if service is enabled
        """
        # Always run check commands (read-only)
        result = self.run(f"systemctl is-enabled {service}", check=False, force_execute=True)
        return result.stdout.strip() == "enabled"

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
        self, path: str, content: str, mode: int = 0o644, backup: bool = False, **kwargs
    ) -> None:
        """
        Write content to file (with dry-run support).
        """
        if self.dry_run:
            if self.dry_run_manager:
                self.dry_run_manager.record_file_write(path, content)
            return

        from configurator.utils.file import write_file as utils_write_file

        path_obj = Path(path)
        file_existed = path_obj.exists()

        # If file exists and we are overwriting, we should back it up
        # utils_write_file handles creation of the .bak file if backup=True (default in our check below)
        # But we need to register the restoration of that backup in rollback manager.

        # However, utils_write_file returns the path written. It doesn't return the backup path.
        # So we pre-check existence.

        backup_path = None
        if file_existed:
            # We can predict the backup path or rely on utils backing it up.
            # For robust rollback, we should probably manually backup or use a wrapper that returns backup path.
            # Given constraints, we will assume standard backup location or side-by-side.
            # utils/file.py backup_file uses side-by-side with .bak suffix or timestamp.
            # Let's simplify: if it exists, register a file_restore.
            # But we need the backup file path to restore FROM.
            pass

        # Perform the write
        utils_write_file(path, content, mode=mode, backup=backup, **kwargs)

        # Register rollback
        if not file_existed:
            # If file didn't exist, rollback is to remove it
            self.rollback_manager.add_command(
                f"rm -f {path}", description=f"Remove created file: {path}"
            )
        elif self.rollback_manager:
            # If it did exist, we ideally want to restore it.
            # Since we can't easily get the backup path without changing utils,
            # we will at least log that we modified it.
            # Ideally: implement full backup tracking.
            # Current Best Effort:
            self.logger.debug(f"Modified existing file {path}. Backup should be available.")

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
