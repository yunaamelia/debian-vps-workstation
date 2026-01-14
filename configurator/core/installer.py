"""
Installation orchestrator.

Manages the execution order of modules and handles errors.
"""

import logging
from typing import Any, Dict, Optional, Type

from configurator.config import ConfigManager
from configurator.core.container import Container
from configurator.core.dryrun import DryRunManager
from configurator.core.hooks import HooksManager, HookType
from configurator.core.reporter import ProgressReporter
from configurator.core.rollback import RollbackManager
from configurator.core.validator import SystemValidator
from configurator.exceptions import PrerequisiteError
from configurator.modules.base import ConfigurationModule
from configurator.plugins.loader import PluginManager
from configurator.utils.circuit_breaker import CircuitBreakerManager


class Installer:
    """
    Orchestrates the installation of all enabled modules.

    Responsibilities:
    - Validate system prerequisites
    - Load and order modules by priority
    - Execute modules in order
    - Handle errors and rollback
    - Report progress
    """

    # ... (Module Priority constant remains same) ...
    MODULE_PRIORITY = {
        "system": 10,
        "security": 20,  # Security is mandatory
        "rbac": 25,  # RBAC module
        "desktop": 30,
        "python": 40,
        "nodejs": 41,
        "golang": 42,
        "rust": 43,
        "java": 44,
        "php": 45,
        "docker": 50,
        "git": 51,
        "databases": 52,
        "devops": 53,
        "utilities": 54,
        "vscode": 60,
        "cursor": 61,
        "neovim": 62,
        "wireguard": 70,
        "caddy": 71,
        "netdata": 80,
    }

    def __init__(
        self,
        config: ConfigManager,
        logger: Optional[logging.Logger] = None,
        reporter: Optional[ProgressReporter] = None,
        container: Optional[Container] = None,
    ):
        """
        Initialize installer.

        Args:
            config: Configuration manager
            logger: Logger instance
            reporter: Progress reporter
            container: DI Container instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.reporter = reporter or ProgressReporter()
        self.container = container or Container()

        # Initialize core services
        self.rollback_manager = RollbackManager(self.logger)
        self.validator = SystemValidator(self.logger)
        self.hooks_manager = HooksManager(self.logger)
        self.plugin_manager = PluginManager(self.logger)
        self.dry_run_manager = DryRunManager()
        self.circuit_breaker_manager = CircuitBreakerManager()

        # Initialize Package Cache (Phase 3)
        self.package_cache_manager = None
        if self.config.get("performance.package_cache.enabled", True):
            from configurator.core.package_cache import PackageCacheManager

            max_size_gb = self.config.get("performance.package_cache.max_size_gb", 10.0)
            try:
                self.package_cache_manager = PackageCacheManager(
                    max_size_gb=max_size_gb, logger=self.logger
                )
                self.logger.info(f"Package cache enabled (Max size: {max_size_gb}GB)")
            except Exception as e:
                self.logger.warning(f"Failed to initialize package cache: {e}")

        # Register core services in container
        self.container.singleton("config", lambda: self.config)
        self.container.singleton("logger", lambda: self.logger)
        self.container.singleton("reporter", lambda: self.reporter)
        self.container.singleton("rollback_manager", lambda: self.rollback_manager)
        self.container.singleton("validator", lambda: self.validator)
        self.container.singleton("hooks_manager", lambda: self.hooks_manager)
        self.container.singleton("plugin_manager", lambda: self.plugin_manager)
        self.container.singleton("dry_run_manager", lambda: self.dry_run_manager)
        self.container.singleton("circuit_breaker_manager", lambda: self.circuit_breaker_manager)
        self.container.singleton("package_cache_manager", lambda: self.package_cache_manager)

        # Module registry - maps names to classes/factories
        self._register_modules()

    # ... _register_modules stays same ...
    def _register_modules(self):
        """Register all available modules."""
        # Import modules here to avoid circular imports
        from configurator.modules.caddy import CaddyModule
        from configurator.modules.cursor import CursorModule

        # Additional modules
        from configurator.modules.databases import DatabasesModule
        from configurator.modules.desktop import DesktopModule
        from configurator.modules.devops import DevOpsModule
        from configurator.modules.docker import DockerModule
        from configurator.modules.git import GitModule

        # Phase 6 modules
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
        from configurator.modules.utilities import UtilitiesModule
        from configurator.modules.vscode import VSCodeModule
        from configurator.modules.wireguard import WireGuardModule

        module_classes = {
            # Core
            "system": SystemModule,
            "security": SecurityModule,
            "rbac": RBACModule,
            "desktop": DesktopModule,
            # Languages
            "python": PythonModule,
            "nodejs": NodeJSModule,
            "golang": GolangModule,
            "rust": RustModule,
            "java": JavaModule,
            "php": PHPModule,
            # Tools
            "docker": DockerModule,
            "git": GitModule,
            "databases": DatabasesModule,
            "devops": DevOpsModule,
            "utilities": UtilitiesModule,
            # Editors
            "vscode": VSCodeModule,
            "cursor": CursorModule,
            "neovim": NeovimModule,
            # Networking
            "wireguard": WireGuardModule,
            "caddy": CaddyModule,
            # Monitoring
            "netdata": NetdataModule,
        }

        # Register modules in container
        for name, cls in module_classes.items():
            self._register_module_factory(name, cls)

    def _register_module_factory(self, name: str, cls: Type[ConfigurationModule]):
        """Helper to register a module factory."""
        self.container.factory(
            name,
            lambda c, config: cls(
                config=config,
                logger=c.get("logger"),
                rollback_manager=c.get("rollback_manager"),
                dry_run_manager=c.get("dry_run_manager"),
                circuit_breaker_manager=c.get("circuit_breaker_manager"),
                package_cache_manager=c.get("package_cache_manager"),
            ),
        )

    def install(
        self,
        skip_validation: bool = False,
        dry_run: bool = False,
        parallel: bool = True,
    ) -> bool:
        """
        Run the full installation with optional parallel execution.

        Args:
            skip_validation: Skip system validation
            dry_run: Only show what would be done
            parallel: Enable parallel execution (overrides config if False)

        Returns:
            True if installation was successful
        """
        try:
            # Enable Dry Run if requested
            if dry_run:
                self.dry_run_manager.enable()
                self.logger.info("Running in DRY-RUN mode. No changes will be made.")

            # Show banner
            self.reporter.start()

            # Validate system
            if not skip_validation:
                self.reporter.start_phase("System Validation")
                self.validator.validate_all(strict=True)
                self.reporter.complete_phase(success=True)

            # Load plugins
            self.plugin_manager.load_plugins()

            # Execute pre-install hooks
            self.hooks_manager.execute(HookType.PRE_INSTALL)

            # Get enabled modules
            enabled_modules = self.config.get_enabled_modules()
            self.logger.info(f"Enabled modules: {', '.join(enabled_modules)}")

            results = {}

            # Determine effective parallel setting
            config_parallel = self.config.get("performance.parallel_execution", True)
            use_parallel = parallel and config_parallel

            # If only 1 module, no need for parallel overhead
            if len(enabled_modules) <= 1:
                use_parallel = False

            if use_parallel:
                try:
                    from configurator.core.dependencies import COMPLETE_MODULE_DEPENDENCIES
                    from configurator.core.parallel import DependencyGraph, ParallelModuleExecutor

                    self.logger.info("Initializing parallel execution engine...")

                    # 1. Instantiate all modules
                    module_registry = {}
                    for module_name in enabled_modules:
                        if not self.container.has(module_name):
                            self.logger.warning(f"Module not found: {module_name}")
                            continue

                        module_config = self._get_module_config(module_name)
                        module = self.container.make(module_name, config=module_config)
                        module_registry[module_name] = module

                    # 2. Build Dependency Graph
                    graph = DependencyGraph(logger=self.logger)

                    for name, module in module_registry.items():
                        # Use dependency dict OR module attribute
                        # Default to COMPLETE_MODULE_DEPENDENCIES if available to ensure consistency
                        # But module attribute is the source of truth for custom plugins
                        depends_on = getattr(module, "depends_on", [])
                        force_sequential = getattr(module, "force_sequential", False)

                        # Fallback to centralized dict if module attribute empty (legacy support)
                        if not depends_on:
                            depends_on = COMPLETE_MODULE_DEPENDENCIES.get(name, [])

                        graph.add_module(
                            name, depends_on=depends_on, force_sequential=force_sequential
                        )

                    # 3. Validate Graph
                    graph.validate()

                    # 4. Get batches
                    batches = graph.get_parallel_batches()

                    self.logger.info(f"Parallel execution plan: {len(batches)} batches")
                    for i, batch in enumerate(batches, 1):
                        self.logger.info(f"  Batch {i}: {', '.join(batch)}")

                    # 5. Execute
                    max_workers = self.config.get("performance.max_workers", 3)
                    executor = ParallelModuleExecutor(
                        max_workers=max_workers, logger=self.logger, reporter=self.reporter
                    )

                    def execute_adapter(name: str, instance: ConfigurationModule) -> bool:
                        """Adapter to use existing _execute_module logic with instance"""
                        return self._execute_module_instance(name, instance, dry_run=dry_run)

                    # Execute
                    results = executor.execute_batches(
                        batches, module_registry, execution_handler=execute_adapter
                    )

                    # Log Stats
                    stats = executor.get_execution_stats()
                    total_time = sum(s["duration"] for s in stats.values())
                    self.logger.info(f"Total execution time (sum of threads): {total_time:.1f}s")

                except Exception as e:
                    self.logger.error(
                        f"Parallel execution failed: {e}. Falling back to sequential.",
                        exc_info=True,
                    )
                    use_parallel = False

                    # CORE-001 FIX: Preserve successful results instead of clearing
                    successful_modules = [name for name, success in results.items() if success]
                    if successful_modules:
                        self.logger.info(
                            f"Preserving {len(successful_modules)} successful module results"
                        )
                        self.logger.debug(f"Already completed: {', '.join(successful_modules)}")
                    # Don't clear results - keep them for sequential fallback
                    # results = {}  # ❌ REMOVED - was clearing successful results!
                    self.logger.warning("Restarting remaining modules with sequential execution...")

            if not use_parallel:
                # Sequential fallback
                self.logger.info("Using sequential execution")
                sorted_modules = sorted(
                    enabled_modules, key=lambda m: self.MODULE_PRIORITY.get(m, 100)
                )
                for module_name in sorted_modules:
                    if not self.container.has(module_name):
                        self.logger.warning(f"Module not found: {module_name}")
                        continue

                    # CORE-001 FIX: Skip already-successful modules from parallel fallback
                    if module_name in results and results[module_name]:
                        self.logger.info(f"⏭️  Skipping already-completed module: {module_name}")
                        continue

                    # Execute
                    success = self._execute_module(module_name, dry_run=dry_run)
                    results[module_name] = success

                    if not success and module_name in ("system", "security"):
                        self.logger.error(f"Mandatory module {module_name} failed. Stopping.")
                        break

            # Show summary
            self.reporter.results = results
            self.reporter.show_summary()

            # Show report
            if dry_run:
                self.dry_run_manager.print_report()
                return True

            # Check for failures
            if all(results.values()) and results:
                from configurator.utils.network import get_public_ip

                self.reporter.show_next_steps(
                    rdp_port=self.config.get("desktop.xrdp_port", 3389),
                    public_ip=get_public_ip(),
                )
                return True
            else:
                self.logger.warning("Some modules failed. Check logs for details.")
                return False

        except PrerequisiteError as e:
            self.logger.error(str(e))
            self.hooks_manager.execute(HookType.ON_ERROR)
            return False
        except Exception as e:
            self.logger.exception("Unexpected error during installation")
            self.reporter.error(str(e))

            # CORE-002 FIX: Add rollback confirmation in interactive mode
            if self.rollback_manager.actions and not dry_run:
                self.hooks_manager.execute(HookType.ON_ERROR)

                # Check if interactive mode
                is_interactive = self.config.get("interactive", True)
                action_count = len(self.rollback_manager.actions)

                if is_interactive:
                    # Prompt user for confirmation before rollback
                    import click

                    self.logger.warning(f"\n{'=' * 60}")
                    self.logger.warning(
                        f"Installation failed. {action_count} rollback actions available."
                    )
                    self.logger.warning(f"{'=' * 60}")

                    # Show rollback summary
                    summary = self.rollback_manager.get_summary()
                    self.logger.info(f"\nRollback preview:\n{summary}")

                    # Ask for user confirmation
                    should_rollback = click.confirm(
                        "\n⚠️  Do you want to rollback changes?", default=False
                    )

                    if should_rollback:
                        self.logger.info("User confirmed rollback. Proceeding...")
                        self.hooks_manager.execute(HookType.ON_ROLLBACK)
                        self.rollback_manager.rollback()
                    else:
                        self.logger.info("User declined rollback. Keeping partial changes.")
                        self.logger.warning("Review logs and manually fix issues if needed.")
                else:
                    # Non-interactive mode: check config for auto-rollback
                    auto_rollback = self.config.get("installation.auto_rollback_on_error", True)

                    if auto_rollback:
                        self.logger.info(
                            f"Auto-rollback enabled. Rolling back {action_count} actions..."
                        )
                        self.hooks_manager.execute(HookType.ON_ROLLBACK)
                        self.rollback_manager.rollback()
                    else:
                        self.logger.warning(
                            f"Auto-rollback disabled. Keeping partial changes "
                            f"({action_count} rollback actions available)."
                        )

            return False

    def _execute_module(
        self,
        module_name: str,
        dry_run: bool = False,
    ) -> bool:
        """
        Execute a single module (instantiates it first).
        """
        # Get module-specific config
        module_config = self._get_module_config(module_name)

        # Create module instance via container
        module = self.container.make(module_name, config=module_config)

        return self._execute_module_instance(module_name, module, dry_run=dry_run)

    def _execute_module_instance(
        self,
        module_name: str,
        module: ConfigurationModule,
        dry_run: bool = False,
    ) -> bool:
        """
        Execute a pre-instantiated module instance.
        """
        # Start phase
        self.reporter.start_phase(f"Installing {module.name}")

        try:
            # Pre-module hooks
            self.hooks_manager.execute(HookType.PRE_MODULE, module_name=module_name)

            # Validate
            self.reporter.update("Validating prerequisites...")
            if not module.validate():
                self.reporter.complete_phase(success=False)
                return False

            # Configure/Install (Safe to run in dry mode as module checks dry_run)
            self.reporter.update("Configuring..." if not dry_run else "Configuring (Dry Run)...")

            if not module.configure():
                self.reporter.complete_phase(success=False)
                return False

            # Verify
            self.reporter.update("Verifying installation...")
            if not module.verify():
                self.reporter.warning(f"Verification warnings for {module.name}")

            # Post-module hooks
            self.hooks_manager.execute(HookType.POST_MODULE, module_name=module_name)

            self.reporter.complete_phase(success=True)
            return True

        except Exception as e:
            import traceback

            self.logger.error(f"Module {module_name} failed: {e}")
            self.logger.debug(f"Traceback:\n{traceback.format_exc()}")
            self.reporter.complete_phase(success=False)
            return False

    def _get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration for a specific module."""
        # Check common paths for module configuration
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
                if isinstance(config, dict):
                    return config
                else:
                    return {"enabled": config}

        return {}

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

            module_config = self._get_module_config(module_name)

            module = self.container.make(module_name, config=module_config)

            try:
                success = module.verify()
                results[module_name] = success

                status = "✓" if success else "✗"
                self.reporter.update(f"{status} {module.name}")

            except Exception as e:
                results[module_name] = False
                self.reporter.update(f"✗ {module.name}: {e}")

        self.reporter.complete_phase(success=all(results.values()))

        # Show summary
        self.reporter.results = results
        self.reporter.show_summary()

        return all(results.values())

    def rollback(self) -> bool:
        """
        Rollback previous installation.

        Returns:
            True if rollback was successful
        """
        # Try to load state from previous run
        self.rollback_manager.load_state()

        if not self.rollback_manager.actions:
            self.logger.info("No rollback actions found")
            return True

        self.reporter.start_phase("Rollback")

        self.logger.info(self.rollback_manager.get_summary())

        success = self.rollback_manager.rollback()

        self.reporter.complete_phase(success=success)

        return success
