from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union

from configurator.dependencies.models import ConflictRule, ModuleDependency


@dataclass
class ModuleDependencyInfo:
    name: str
    depends_on: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    priority: int = 50
    force_sequential: bool = False


class DependencyRegistry:
    _registry: Dict[str, Union[ModuleDependencyInfo, ModuleDependency]] = {}

    @classmethod
    def register(cls, info: Union[ModuleDependencyInfo, ModuleDependency]):
        # Support both ModuleDependencyInfo (name) and ModuleDependency (module_name)
        if hasattr(info, "name"):
            cls._registry[info.name] = info
        elif hasattr(info, "module_name"):
            cls._registry[info.module_name] = info
        else:
            raise ValueError("Invalid dependency info object")

    @classmethod
    def get(cls, name: str) -> Optional[Union[ModuleDependencyInfo, ModuleDependency]]:
        return cls._registry.get(name)

    @classmethod
    def get_all(cls) -> List[Union[ModuleDependencyInfo, ModuleDependency]]:
        return list(cls._registry.values())

    @classmethod
    def clear(cls):
        cls._registry = {}

    @classmethod
    def _get_name(cls, info) -> str:
        """Get name from either type of info object."""
        name = getattr(info, "name", None) or getattr(info, "module_name", None)
        return str(name) if name else ""

    @classmethod
    def _get_depends_on(cls, info) -> List[str]:
        """Get depends_on from either type of info object."""
        return getattr(info, "depends_on", [])

    @classmethod
    def _get_conflicts_with(cls, info) -> List[str]:
        """Get conflicts_with from either type of info object."""
        return getattr(info, "conflicts_with", [])

    @classmethod
    def _get_priority(cls, info) -> int:
        """Get priority from either type of info object."""
        return getattr(info, "priority", 50)

    @classmethod
    def detect_conflicts(cls, module_names: List[str]) -> List[ConflictRule]:
        """Detect conflicts between selected modules."""
        conflicts = []
        for name in module_names:
            info = cls._registry.get(name)
            if info:
                for conflict in cls._get_conflicts_with(info):
                    if conflict in module_names:
                        conflicts.append(
                            ConflictRule(
                                module_a=name,
                                module_b=conflict,
                                reason=f"{name} conflicts with {conflict}",
                            )
                        )
        return conflicts

    @classmethod
    def resolve_order(cls, module_names: List[str]) -> List[str]:
        """Resolve execution order based on dependencies and priority."""
        from configurator.core.dependency import DependencyGraph

        graph = DependencyGraph()
        for name in module_names:
            info = cls._registry.get(name)
            if info:
                deps = [d for d in cls._get_depends_on(info) if d in module_names]
                graph.add_module(name, depends_on=deps)
            else:
                graph.add_module(name)

        batches = graph.get_execution_batches()
        # Flatten batches, sort within each batch by priority
        result = []
        for batch in batches:
            sorted_batch = sorted(
                batch,
                key=lambda n: cls._get_priority(cls._registry.get(n))
                if cls._registry.get(n)
                else 50,
            )
            result.extend(sorted_batch)
        return result

    @classmethod
    def validate_dependencies(cls, module_names: List[str]) -> List[str]:
        """Validate that all dependencies are satisfied. Returns list of error messages."""
        errors = []
        for name in module_names:
            info = cls._registry.get(name)
            if info:
                for dep in cls._get_depends_on(info):
                    if dep not in module_names and dep not in cls._registry:
                        errors.append(f"Module '{name}' requires '{dep}' which is not selected")
        return errors


# Pre-populate with known dependencies
# Priorities: System (10) -> Security (20) -> Core Apps (30) -> User Apps (50) -> UI (60)

_DEFAULTS = [
    ModuleDependencyInfo("system", priority=10),
    ModuleDependencyInfo("security", depends_on=["system"], priority=20),
    ModuleDependencyInfo("rbac", depends_on=["security"], priority=25),
    ModuleDependencyInfo("desktop", depends_on=["system", "security"], priority=30),
    # Dev Languages
    ModuleDependencyInfo("python", depends_on=["system"], priority=50),
    ModuleDependencyInfo("nodejs", depends_on=["system"], priority=50),
    ModuleDependencyInfo("golang", depends_on=["system"], priority=50),
    ModuleDependencyInfo("rust", depends_on=["system"], priority=50),
    ModuleDependencyInfo("java", depends_on=["system"], priority=50),
    ModuleDependencyInfo("php", depends_on=["system"], priority=50),
    # Core Tools
    ModuleDependencyInfo("git", depends_on=["system"], priority=40),
    ModuleDependencyInfo("docker", depends_on=["system", "security"], priority=40),
    ModuleDependencyInfo("databases", depends_on=["system"], priority=50),
    ModuleDependencyInfo("devops", depends_on=["system", "python"], priority=50),
    # UI / Desktop Apps
    ModuleDependencyInfo("vscode", depends_on=["desktop"], priority=60),
    ModuleDependencyInfo("cursor", depends_on=["desktop"], priority=60),
    ModuleDependencyInfo("neovim", depends_on=["system"], priority=50),
    # Networking
    ModuleDependencyInfo("wireguard", depends_on=["security"], priority=30),
    ModuleDependencyInfo("caddy", depends_on=["security"], priority=30),
    # Monitoring
    ModuleDependencyInfo("netdata", depends_on=["system"], priority=90),  # Run last
]

for dep in _DEFAULTS:
    DependencyRegistry.register(dep)
