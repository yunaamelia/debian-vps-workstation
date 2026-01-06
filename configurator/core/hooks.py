"""
Hooks system for pre/post installation events.

Allows users to run custom scripts or functions at various
points during the installation process.
"""

import importlib.util
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class HookType(Enum):
    """Types of hooks that can be registered."""

    PRE_INSTALL = "pre_install"
    POST_INSTALL = "post_install"
    PRE_MODULE = "pre_module"
    POST_MODULE = "post_module"
    ON_ERROR = "on_error"
    ON_ROLLBACK = "on_rollback"


@dataclass
class Hook:
    """A registered hook."""

    name: str
    hook_type: HookType
    handler: Callable[..., None]
    priority: int = 50  # Lower = runs first (0-100)
    module_name: Optional[str] = None  # For module-specific hooks

    def __lt__(self, other: "Hook") -> bool:
        return self.priority < other.priority


@dataclass
class HookContext:
    """Context passed to hooks."""

    hook_type: HookType
    module_name: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    dry_run: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


class HooksManager:
    """
    Manages registration and execution of hooks.

    Hooks can be:
    - Python functions registered via API
    - Shell scripts in hooks directories
    """

    # Default hook directories
    HOOK_DIRS = [
        Path("/etc/debian-vps-configurator/hooks.d"),
        Path.home() / ".config/debian-vps-configurator/hooks.d",
    ]

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize hooks manager.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._hooks: Dict[HookType, List[Hook]] = {ht: [] for ht in HookType}
        self._load_script_hooks()

    def register(
        self,
        hook_type: HookType,
        handler: Callable[..., None],
        name: Optional[str] = None,
        priority: int = 50,
        module_name: Optional[str] = None,
    ) -> None:
        """
        Register a hook function.

        Args:
            hook_type: Type of hook (when to run)
            handler: Function to call
            name: Human-readable name for the hook
            priority: Execution order (lower = first)
            module_name: For module-specific hooks
        """
        hook = Hook(
            name=name or handler.__name__,
            hook_type=hook_type,
            handler=handler,
            priority=priority,
            module_name=module_name,
        )
        self._hooks[hook_type].append(hook)
        self._hooks[hook_type].sort()
        self.logger.debug(f"Registered hook: {hook.name} ({hook_type.value})")

    def unregister(self, name: str, hook_type: Optional[HookType] = None) -> bool:
        """
        Unregister a hook by name.

        Args:
            name: Name of hook to remove
            hook_type: Optional type to narrow search

        Returns:
            True if hook was found and removed
        """
        types_to_check = [hook_type] if hook_type else list(HookType)
        removed = False

        for ht in types_to_check:
            self._hooks[ht] = [h for h in self._hooks[ht] if h.name != name]
            if len(self._hooks[ht]) != len([h for h in self._hooks[ht]]):
                removed = True

        return removed

    def execute(
        self,
        hook_type: HookType,
        context: Optional[HookContext] = None,
        module_name: Optional[str] = None,
    ) -> bool:
        """
        Execute all hooks of a given type.

        Args:
            hook_type: Type of hooks to execute
            context: Context to pass to hooks
            module_name: For module-specific hooks

        Returns:
            True if all hooks executed successfully
        """
        if context is None:
            context = HookContext(hook_type=hook_type, module_name=module_name)

        hooks = self._hooks[hook_type]

        # Filter module-specific hooks if applicable
        if module_name and hook_type in (HookType.PRE_MODULE, HookType.POST_MODULE):
            hooks = [h for h in hooks if h.module_name is None or h.module_name == module_name]

        if not hooks:
            return True

        self.logger.debug(f"Executing {len(hooks)} {hook_type.value} hooks")

        success = True
        for hook in hooks:
            try:
                self.logger.debug(f"Running hook: {hook.name}")
                hook.handler(context)
            except Exception as e:
                self.logger.error(f"Hook {hook.name} failed: {e}")
                success = False
                # Continue with other hooks unless it's critical

        return success

    def _load_script_hooks(self) -> None:
        """Load hooks from script directories."""
        for hook_dir in self.HOOK_DIRS:
            if not hook_dir.exists():
                continue

            for script in sorted(hook_dir.glob("*.sh")):
                self._register_script_hook(script)

            for script in sorted(hook_dir.glob("*.py")):
                self._register_python_hook(script)

    def _register_script_hook(self, script_path: Path) -> None:
        """Register a shell script as a hook."""
        # Parse hook type from filename: NN-hooktype-name.sh
        # e.g., 10-pre_install-custom.sh
        name = script_path.stem
        parts = name.split("-", 2)

        if len(parts) >= 2:
            try:
                priority = int(parts[0])
                hook_type_str = parts[1]
            except ValueError:
                priority = 50
                hook_type_str = parts[0]
        else:
            priority = 50
            hook_type_str = name

        # Map to hook type
        hook_type = None
        module_name = None

        if hook_type_str == "pre_install":
            hook_type = HookType.PRE_INSTALL
        elif hook_type_str == "post_install":
            hook_type = HookType.POST_INSTALL
        elif hook_type_str.startswith("pre_module_"):
            hook_type = HookType.PRE_MODULE
            module_name = hook_type_str.replace("pre_module_", "")
        elif hook_type_str.startswith("post_module_"):
            hook_type = HookType.POST_MODULE
            module_name = hook_type_str.replace("post_module_", "")
        elif hook_type_str == "on_error":
            hook_type = HookType.ON_ERROR
        elif hook_type_str == "on_rollback":
            hook_type = HookType.ON_ROLLBACK

        if hook_type is None:
            self.logger.debug(f"Unknown hook type in {script_path}, skipping")
            return

        def make_handler(path: Path) -> Callable[[HookContext], None]:
            def handler(ctx: HookContext) -> None:
                env = {
                    "HOOK_TYPE": ctx.hook_type.value,
                    "MODULE_NAME": ctx.module_name or "",
                    "DRY_RUN": "1" if ctx.dry_run else "0",
                }
                subprocess.run(
                    ["bash", str(path)],
                    env={**dict(__import__("os").environ), **env},
                    check=True,
                )

            return handler

        self.register(
            hook_type=hook_type,
            handler=make_handler(script_path),
            name=f"script:{script_path.name}",
            priority=priority,
            module_name=module_name,
        )

    def _register_python_hook(self, script_path: Path) -> None:
        """
        Register a Python script as a hook.

        The script should define a `run(context: HookContext)` function.
        Can optionally define `HOOK_TYPE`, `PRIORITY`, and `MODULE_NAME`.
        """
        try:
            # Load module
            module_name = f"configurator_hooks_{script_path.stem}"
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None or spec.loader is None:
                self.logger.warning(f"Could not load hook spec from {script_path}")
                return

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Check for run function
            if not hasattr(module, "run") or not callable(module.run):
                self.logger.warning(f"Python hook {script_path} missing 'run(context)' function")
                return

            # Determine hook properties from module attributes or filename
            name = script_path.stem
            parts = name.split("-", 2)

            # Default from filename
            priority_default = 50
            hook_type_default = None
            module_name_default = None

            if len(parts) >= 2:
                try:
                    priority_default = int(parts[0])
                    hook_type_str = parts[1]
                except ValueError:
                    hook_type_str = parts[0]
            else:
                hook_type_str = name

            if hook_type_str == "pre_install":
                hook_type_default = HookType.PRE_INSTALL
            elif hook_type_str == "post_install":
                hook_type_default = HookType.POST_INSTALL
            elif hook_type_str.startswith("pre_module_"):
                hook_type_default = HookType.PRE_MODULE
                module_name_default = hook_type_str.replace("pre_module_", "")
            elif hook_type_str.startswith("post_module_"):
                hook_type_default = HookType.POST_MODULE
                module_name_default = hook_type_str.replace("post_module_", "")
            elif hook_type_str == "on_error":
                hook_type_default = HookType.ON_ERROR
            elif hook_type_str == "on_rollback":
                hook_type_default = HookType.ON_ROLLBACK

            # Allow module override
            hook_type = getattr(module, "HOOK_TYPE", hook_type_default)
            if isinstance(hook_type, str):
                try:
                    hook_type = HookType(hook_type)
                except ValueError:
                    self.logger.warning(f"Invalid HOOK_TYPE string in {script_path}")
                    hook_type = None

            priority = getattr(module, "PRIORITY", priority_default)
            target_module = getattr(module, "MODULE_NAME", module_name_default)

            if hook_type is None:
                self.logger.debug(f"Could not determine hook type for {script_path}")
                return

            # Register
            self.register(
                hook_type=hook_type,
                handler=module.run,
                name=f"python:{script_path.name}",
                priority=priority,
                module_name=target_module,
            )

        except Exception as e:
            self.logger.error(f"Failed to load Python hook {script_path}: {e}")

    def get_hooks(self, hook_type: Optional[HookType] = None) -> List[Hook]:
        """
        Get registered hooks.

        Args:
            hook_type: Optional filter by type

        Returns:
            List of registered hooks
        """
        if hook_type:
            return list(self._hooks[hook_type])
        return [h for hooks in self._hooks.values() for h in hooks]


# Convenience decorators
def pre_install(priority: int = 50) -> Callable:
    """Decorator to register a pre-install hook."""

    def decorator(func: Callable) -> Callable:
        func._hook_type = HookType.PRE_INSTALL
        func._hook_priority = priority
        return func

    return decorator


def post_install(priority: int = 50) -> Callable:
    """Decorator to register a post-install hook."""

    def decorator(func: Callable) -> Callable:
        func._hook_type = HookType.POST_INSTALL
        func._hook_priority = priority
        return func

    return decorator


def pre_module(module_name: str, priority: int = 50) -> Callable:
    """Decorator to register a pre-module hook."""

    def decorator(func: Callable) -> Callable:
        func._hook_type = HookType.PRE_MODULE
        func._hook_priority = priority
        func._hook_module = module_name
        return func

    return decorator


def post_module(module_name: str, priority: int = 50) -> Callable:
    """Decorator to register a post-module hook."""

    def decorator(func: Callable) -> Callable:
        func._hook_type = HookType.POST_MODULE
        func._hook_priority = priority
        func._hook_module = module_name
        return func

    return decorator
