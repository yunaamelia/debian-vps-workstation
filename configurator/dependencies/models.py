"""
Dependency models for module relationships.

Defines data structures for representing module dependencies and conflicts.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ModuleDependency:
    """
    Module dependency configuration.

    Defines dependencies, optional dependencies, and conflicts for a module.
    """

    module_name: str
    depends_on: List[str] = field(default_factory=list)
    optional_deps: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    priority: int = 50
    force_sequential: bool = False

    def __post_init__(self) -> None:
        """Validate dependency configuration."""
        # Ensure no module depends on itself
        if self.module_name in self.depends_on:
            raise ValueError(f"Module {self.module_name} cannot depend on itself")

        # Ensure no overlap between dependencies and conflicts
        conflicts_set = set(self.conflicts_with)
        deps_set = set(self.depends_on) | set(self.optional_deps)

        overlap = conflicts_set & deps_set
        if overlap:
            raise ValueError(
                f"Module {self.module_name} has conflicting configuration: "
                f"{overlap} appears in both dependencies and conflicts"
            )


@dataclass
class ConflictRule:
    """
    Module conflict rule.

    Defines a conflict between two modules that cannot be installed together.
    """

    module_a: str
    module_b: str
    reason: str

    def __post_init__(self) -> None:
        """Validate conflict rule."""
        if self.module_a == self.module_b:
            raise ValueError("A module cannot conflict with itself")

    def involves(self, module_name: str) -> bool:
        """
        Check if this conflict rule involves a specific module.

        Args:
            module_name: Name of module to check

        Returns:
            True if module is part of this conflict
        """
        return module_name in (self.module_a, self.module_b)

    def conflicts_with(self, module_name: str) -> str:
        """
        Get the module that conflicts with the given module.

        Args:
            module_name: Name of module to check

        Returns:
            Name of conflicting module, or empty string if not involved

        Raises:
            ValueError: If module_name is not part of this conflict
        """
        if module_name == self.module_a:
            return self.module_b
        elif module_name == self.module_b:
            return self.module_a
        else:
            raise ValueError(f"Module {module_name} is not part of this conflict rule")
