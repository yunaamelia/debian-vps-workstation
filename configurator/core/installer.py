"""
Installation orchestrator.

Manages the execution order of modules and handles errors.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from configurator.config import ConfigManager
from configurator.core.container import Container
from configurator.core.dependency import DependencyGraph
from configurator.core.dryrun import DryRunManager
from configurator.core.execution.base import ExecutionContext

if TYPE_CHECKING:
    pass


# Sprint 2 Components
from configurator.core.execution.hybrid import HybridExecutor
from configurator.core.hooks.events import HookContext, HookEvent
from configurator.core.hooks.manager import HooksManager
from configurator.core.reporter.base import ReporterInterface
from configurator.core.reporter.console import ConsoleReporter
from configurator.core.rollback import RollbackManager
from configurator.core.state.manager import StateManager
from configurator.core.validator import SystemValidator
from configurator.plugins.loader import PluginManager
from configurator.utils.circuit_breaker import CircuitBreakerManager
from configurator.validators.orchestrator import ValidationOrchestrator

# Fallback to rich reporter if available, else console
try:
    from configurator.core.reporter.rich_reporter import RichProgressReporter

    DEFAULT_REPORTER = RichProgressReporter
except ImportError:
    DEFAULT_REPORTER = ConsoleReporter


class Installer:
    """
    Orchestrates the installation of all enabled modules.
    """

    def __init__(
        self,
        config: ConfigManager,
        logger: Optional[logging.Logger] = None,
        reporter: Optional[ReporterInterface] = None,
        container: Optional[Container] = None,
    ):
        """
        Initialize installer.
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        # Use provided reporter or default to Rich/Console
        self.reporter = reporter or DEFAULT_REPORTER()
        self.container = container or Container()

        # Initialize parallel logging
        from configurator.logger import get_log_manager

        self.log_manager = get_log_manager(
            console_level=logging.DEBUG if config.get("verbose", False) else logging.INFO,
            enable_per_module_logs=config.get("logging.per_module_logs", True),
        )

        # Initialize core services
        self.rollback_manager = RollbackManager(self.logger)
        self.validator = SystemValidator(self.logger)
        self.plugin_manager = PluginManager(self.logger)
        self.dry_run_manager = DryRunManager()
        self.circuit_breaker_manager = CircuitBreakerManager()

        # Sprint 2 Components
        self.hooks_manager = HooksManager()
        self.hybrid_executor = HybridExecutor(
            max_workers=self.config.get("performance.max_workers", 4), logger=self.logger
        )
        self.state_manager = StateManager(logger=self.logger)
        self.validator_orchestrator = ValidationOrchestrator(logger=self.logger)

        self.logger.info("Installer initialized with Sprint 2 components")

        # Initialize Package Cache (Phase 3)
        self.package_cache_manager = None
        if self.config.get("performance.package_cache.enabled", True):
            try:
                from configurator.core.package_cache import PackageCacheManager

                max_size_gb = self.config.get("performance.package_cache.max_size_gb", 10.0)
                self.package_cache_manager = PackageCacheManager(
                    max_size_gb=max_size_gb, logger=self.logger
                )
            except ImportError:
                pass
            except Exception as e:
                self.logger.warning(f"Failed to initialize package cache: {e}")

        # Register services
        self._register_services()

        # Register modules
        self._register_modules()

        # Register validators
        self._register_validators()

    def _register_services(self):
        """Register core services in container."""
        services = {
            "config": lambda: self.config,
            "logger": lambda: self.logger,
            "reporter": lambda: self.reporter,
            "rollback_manager": lambda: self.rollback_manager,
            "validator": lambda: self.validator,
            "hooks_manager": lambda: self.hooks_manager,
            "plugin_manager": lambda: self.plugin_manager,
            "dry_run_manager": lambda: self.dry_run_manager,
            "circuit_breaker_manager": lambda: self.circuit_breaker_manager,
            "package_cache_manager": lambda: self.package_cache_manager,
            "state_manager": lambda: self.state_manager,
        }
        for name, factory in services.items():
            self.container.singleton(name, factory)

    def _register_validators(self):
        """Register validators in orchestrator."""
        try:
            from configurator.validators.tier1_critical.os_version import OSVersionValidator
            from configurator.validators.tier1_critical.python_version import PythonVersionValidator
            from configurator.validators.tier1_critical.root_access import RootAccessValidator
            from configurator.validators.tier2_high.disk_space import DiskSpaceValidator
            from configurator.validators.tier2_high.network import NetworkValidator
            from configurator.validators.tier2_high.ram import RAMValidator

            # Register tier 1
            for v in [OSVersionValidator(), PythonVersionValidator(), RootAccessValidator()]:
                self.validator_orchestrator.register_validator(1, v)

            # Register tier 2
            for v in [RAMValidator(), DiskSpaceValidator(), NetworkValidator()]:
                self.validator_orchestrator.register_validator(2, v)

        except ImportError:
            self.logger.warning("Validators not found, skipping registration")
        except Exception as e:
            self.logger.warning(f"Failed to register validators: {e}")

    def _register_modules(self):
        """Register all available modules."""
        # Helper for lazy loading to verify class existence and typing without runtime impact
        # We perform runtime imports here to strictly control loading order and avoid circularity
        # but the static typing is handled above.

        from configurator.modules.caddy import CaddyModule
        from configurator.modules.cis_compliance import CISComplianceModule
        from configurator.modules.cursor import CursorModule
        from configurator.modules.databases import DatabasesModule
        from configurator.modules.desktop import DesktopModule
        from configurator.modules.devops import DevOpsModule
        from configurator.modules.docker import DockerModule
        from configurator.modules.git import GitModule
        from configurator.modules.golang import GolangModule
        from configurator.modules.java import JavaModule
        from configurator.modules.neovim import NeovimModule
        from configurator.modules.netdata import NetdataModule
        from configurator.modules.nodejs import NodeJSModule
        from configurator.modules.php import PHPModule
        from configurator.modules.python import PythonModule
        from configurator.modules.rbac import RBACModule
        from configurator.modules.rust import RustModule
        from configurator.modules.security import SecurityModule
        from configurator.modules.system import SystemModule
        from configurator.modules.trivy_scanner import TrivyScannerModule
        from configurator.modules.utilities import UtilitiesModule
        from configurator.modules.vscode import VSCodeModule
        from configurator.modules.wireguard import WireGuardModule

        module_classes = {
            "system": SystemModule,
            "security": SecurityModule,
            "cis_compliance": CISComplianceModule,
            "trivy_scanner": TrivyScannerModule,
            "rbac": RBACModule,
            "desktop": DesktopModule,
            "python": PythonModule,
            "nodejs": NodeJSModule,
            "golang": GolangModule,
            "rust": RustModule,
            "java": JavaModule,
            "php": PHPModule,
            "docker": DockerModule,
            "git": GitModule,
            "databases": DatabasesModule,
            "devops": DevOpsModule,
            "utilities": UtilitiesModule,
            "vscode": VSCodeModule,
            "cursor": CursorModule,
            "neovim": NeovimModule,
            "wireguard": WireGuardModule,
            "caddy": CaddyModule,
            "netdata": NetdataModule,
        }

        for name, cls in module_classes.items():
            self.container.factory(
                name,
                lambda c, config, cls=cls: cls(
                    config=config,
                    logger=c.get("logger"),
                    rollback_manager=c.get("rollback_manager"),
                    dry_run_manager=c.get("dry_run_manager"),
                    circuit_breaker_manager=c.get("circuit_breaker_manager"),
                    package_cache_manager=c.get("package_cache_manager"),
                ),
            )

    def install(
        self, skip_validation: bool = False, dry_run: bool = False, parallel: bool = True
    ) -> bool:
        """Run the full installation."""
        try:
            if dry_run:
                self.dry_run_manager.enable()
                self.logger.info("Running in DRY-RUN mode.")

            self.reporter.start()

            # 1. Validation
            if not skip_validation:
                self.reporter.start_phase("System Validation")
                is_interactive = self.config.get("interactive", True)
                success, _ = self.validator_orchestrator.run_validation(interactive=is_interactive)
                if not success:
                    self.reporter.error("System validation failed")
                    return False
                self.reporter.complete_phase(True)

            # 2. Load Plugins & Hooks
            self.plugin_manager.load_plugins()
            self.hooks_manager.execute(HookEvent.BEFORE_INSTALLATION)

            # 2.5 User Provisioning (New)
            prov_user = self.config.get("provisioning.user")
            if prov_user:
                self.reporter.start_phase("User Provisioning")
                self.reporter.update(f"Configuring user {prov_user}...")

                try:
                    from configurator.users.lifecycle_manager import UserLifecycleManager

                    user_manager = UserLifecycleManager(logger=self.logger, dry_run=dry_run)

                    # Create or update user
                    if user_manager.get_user_profile(prov_user):
                        self.logger.info(f"User {prov_user} exists, updating configuration...")
                        # We still want to apply keys/sudo even if user exists
                        # Using create_user implementation which handles idempotent updates implicitly for some parts,
                        # but ideally we might want a dedicated provision method.
                        # For now, we reuse logic or call specific update methods if needed.
                        # However, create_user raises if user exists. We need to handle this.
                        # Let's use a try/except or check first.
                        pass  # Profile updates Logic to be refined or we assume create_user handles "ensure" logic?
                        # Looking at lifecycle_manager.py, create_user raises ValueError if user exists.
                        # We should catch that or check validity.

                    # NOTE: Quick-install logic allows updating.
                    # create_user currently raises. We should treat it as "ensure_user".
                    # For simplicity in this iteration, we try/except or modifying lifecycle logic was safest.
                    # Given we can't easily modify lifecycle again without context switch, let's wrap it in try/catch check.

                    # But wait, quick-install updates password/keys even if user exists.
                    # Use a new helper or just call the specific methods we exposed?
                    # We exposed _inject_ssh_key and _configure_sudo_timeout as internal but accessible.
                    # Best approach: Try create, if fails, apply updates.

                    try:
                        user_manager.create_user(
                            username=prov_user,
                            full_name=prov_user,  # Default to username
                            email=f"{prov_user}@localhost",  # Placeholder
                            role="developer",  # Default role
                            password=self.config.get("provisioning.password"),
                            ssh_key_string=self.config.get("provisioning.ssh_key"),
                            enable_ssh_key=bool(self.config.get("provisioning.ssh_key")),
                            sudo_timeout=self.config.get("provisioning.sudo_timeout"),
                            generate_temp_password=False,
                        )
                        self.reporter.update(f"Created user {prov_user}")
                    except ValueError as e:
                        if "already exists" in str(e):
                            self.logger.info(
                                f"User {prov_user} already exists, updating credentials..."
                            )

                            # Update password if provided
                            pwd = self.config.get("provisioning.password")
                            if pwd and not dry_run:
                                user_manager._set_user_password(prov_user, pwd, force_change=False)

                            # Update SSH key if provided
                            key = self.config.get("provisioning.ssh_key")
                            if key and not dry_run:
                                # Need home dir
                                import pwd as system_pwd

                                try:
                                    home = Path(system_pwd.getpwnam(prov_user).pw_dir)
                                    user_manager._inject_ssh_key(prov_user, key, home)
                                except Exception as e2:
                                    self.logger.warning(f"Could not update SSH key: {e2}")

                            # Update Sudo if provided
                            sudo = self.config.get("provisioning.sudo_timeout")
                            if sudo is not None and not dry_run:
                                user_manager._configure_sudo_timeout(prov_user, sudo)

                            # Ensure RBAC roles and groups are applied (idempotency)
                            if not dry_run:
                                self.logger.info(f"Ensuring RBAC configuration for {prov_user}...")
                                # Re-apply developer role to trigger group syncing/creation
                                user_manager.update_user_role(
                                    prov_user, "developer", updated_by="installer"
                                )

                            self.reporter.update(f"Updated user {prov_user}")
                        else:
                            raise e

                    self.reporter.complete_phase(True)

                except Exception as e:
                    self.logger.error(f"User provisioning failed: {e}")
                    self.reporter.error(f"Failed to configure user {prov_user}: {e}")
                    # Decide if we abort or continue? Quick-install seems to fail on critical errors.
                    return False

            # 3. Build Graph
            enabled_modules = self.config.get_enabled_modules()
            graph = DependencyGraph(self.logger)

            # Populate graph
            from configurator.core.dependencies import COMPLETE_MODULE_DEPENDENCIES

            for module_name in enabled_modules:
                if not self.container.has(module_name):
                    continue

                # Get module instance to check attrs
                # We instantiate early to check dependencies/force_sequential
                # Creating instance is cheap (DI) as long as we don't run it
                config = self._get_module_config(module_name)
                module = self.container.make(module_name, config=config)

                depends_on = getattr(module, "depends_on", []) or COMPLETE_MODULE_DEPENDENCIES.get(
                    module_name, []
                )
                force_sequential = getattr(module, "force_sequential", False)

                graph.add_module(module_name, depends_on, force_sequential)

            graph.validate()
            batches = graph.get_execution_batches()

            # 4. Execute Batches
            execution_results = {}

            def execution_callback(module_name: str, stage: str, data: Dict):
                """Bridge between Executor, Hooks, and Reporter."""
                context = HookContext(
                    event=HookEvent.BEFORE_MODULE_CONFIGURE, module_name=module_name, data=data
                )  # Default event

                if stage == "started":
                    self.reporter.start_phase(module_name)

                elif stage == "validating":
                    self.hooks_manager.execute(HookEvent.BEFORE_MODULE_VALIDATE, context)
                    self.reporter.update("Validating...", module=module_name)

                elif stage == "configuring":
                    self.hooks_manager.execute(HookEvent.BEFORE_MODULE_CONFIGURE, context)
                    self.reporter.update("Configuring...", module=module_name)

                elif stage == "verifying":
                    self.reporter.update("Verifying...", module=module_name)

                elif stage == "completed":
                    self.hooks_manager.execute(HookEvent.AFTER_MODULE_CONFIGURE, context)
                    self.reporter.complete_phase(True, module=module_name)

                elif stage == "failed":
                    self.hooks_manager.execute(HookEvent.ON_MODULE_ERROR, context)
                    self.reporter.complete_phase(False, module=module_name)

            total_batches = len(batches)
            self.logger.info(f"Starting execution of {total_batches} batches")

            for i, batch in enumerate(batches, 1):
                self.logger.info(f"Batch {i}/{total_batches}: {', '.join(batch)}")

                contexts = []
                for module_name in batch:
                    config = self._get_module_config(module_name)
                    module = self.container.make(module_name, config=config)

                    ctx = ExecutionContext(
                        module_name=module_name,
                        module_instance=module,
                        config=config,
                        dry_run=dry_run,
                    )
                    contexts.append(ctx)

                # Execute batch
                results = self.hybrid_executor.execute(contexts, callback=execution_callback)
                execution_results.update(results)

                # Check for critical failures in batch
                if any(not r.success for r in results.values()):
                    self.logger.error("Batch failed. Stopping.")
                    break

            # 5. Summary
            summary_results = {name: res.success for name, res in execution_results.items()}
            self.reporter.show_summary(summary_results)

            success = all(r.success for r in execution_results.values())

            if success:
                self.hooks_manager.execute(HookEvent.AFTER_INSTALLATION)
                self.reporter.show_next_steps(rdp_port=self.config.get("desktop.xrdp_port", 3389))
            else:
                self.hooks_manager.execute(HookEvent.ON_INSTALLATION_ERROR)

            return success

        except Exception as e:
            self.logger.exception("Installation failed")
            self.reporter.error(str(e))
            self.hooks_manager.execute(HookEvent.ON_INSTALLATION_ERROR, error=str(e))
            return False

    def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        paths = [
            f"tools.{module_name}",
            f"tools.editors.{module_name}",
            f"languages.{module_name}",
            f"networking.{module_name}",
            f"monitoring.{module_name}",
            module_name,
        ]
        for path in paths:
            config = self.config.get(path)
            if config is not None:
                module_config = config if isinstance(config, dict) else {"enabled": config}
                if module_name == "security":
                    advanced_security = self.config.get("security_advanced", {})
                    if isinstance(advanced_security, dict) and advanced_security:
                        module_config = {
                            **module_config,
                            "security_advanced": advanced_security,
                        }
                return module_config
        return {}

    def rollback(self) -> bool:
        """Rollback changes."""
        self.hooks_manager.execute(HookEvent.ON_INSTALLATION_ERROR)  # Or explicit rollback event
        success = self.rollback_manager.rollback()
        return success

    def verify(self) -> bool:
        """
        Verify installed components.

        Returns:
            True if all expected components are working
        """
        self.reporter.start_phase("Verification")

        enabled_modules = self.config.get_enabled_modules()
        results = {}

        for module_name in enabled_modules:
            if not self.container.has(module_name):
                continue

            config = self._get_module_config(module_name)
            module = self.container.make(module_name, config=config)

            try:
                success = module.verify()
                results[module_name] = success

                status = "✓" if success else "✗"
                self.reporter.update(f"{status} {module_name}")

            except Exception as e:
                results[module_name] = False
                self.reporter.update(f"✗ {module.name}: {e}")

        self.reporter.complete_phase(success=all(results.values()))
        # Show summary
        self.reporter.show_summary(results)
        return all(results.values())
