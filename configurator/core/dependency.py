import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import networkx as nx


@dataclass
class ModuleDependency:
    """Represents a module with its dependencies"""

    name: str
    depends_on: List[str] = field(default_factory=list)
    priority: int = 100
    force_sequential: bool = False  # Heavy modules run alone


class DependencyGraph:
    """
    Build and analyze module dependency graph using Kahn's algorithm.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.graph = nx.DiGraph()
        self.logger = logger or logging.getLogger(__name__)
        self.module_info: Dict[str, ModuleDependency] = {}

    def add_module(
        self, name: str, depends_on: Optional[List[str]] = None, force_sequential: bool = False
    ) -> None:
        """
        Add module to dependency graph.

        Args:
            name: Module identifier
            depends_on: List of module names this depends on
            force_sequential: If True, module runs in its own batch
        """
        self.graph.add_node(name)

        # Store module info
        self.module_info[name] = ModuleDependency(
            name=name, depends_on=depends_on or [], force_sequential=force_sequential
        )

        # Add edges for dependencies
        if depends_on:
            for dependency in depends_on:
                if dependency not in self.graph:
                    self.graph.add_node(dependency)
                self.graph.add_edge(dependency, name)

    def get_execution_batches(self) -> List[List[str]]:
        """
        Get modules grouped into batches that can run in parallel.
        Returns:
            List of batches, where each batch contains modules
            that can be executed in parallel
        """
        batches = []
        # Create a working copy of in-degrees
        in_degree = dict(self.graph.in_degree())

        while in_degree:
            # Find all nodes with in-degree 0 (no unresolved dependencies)
            batch = [node for node, degree in in_degree.items() if degree == 0]

            if not batch:
                # Circular dependency detected
                remaining_nodes = list(in_degree.keys())
                raise ValueError(
                    f"Circular dependency detected among: {remaining_nodes}\n"
                    "Please check module dependencies for cycles."
                )

            # Separate force_sequential modules
            sequential_modules = [
                m for m in batch if self.module_info.get(m, ModuleDependency(m)).force_sequential
            ]
            parallel_modules = [
                m
                for m in batch
                if not self.module_info.get(m, ModuleDependency(m)).force_sequential
            ]

            # Add sequential modules in separate batches
            for module in sequential_modules:
                batches.append([module])
                self._remove_node_and_update_degrees(module, in_degree)

            # Add parallel modules together
            if parallel_modules:
                batches.append(parallel_modules)
                for module in parallel_modules:
                    self._remove_node_and_update_degrees(module, in_degree)

        return batches

    def _remove_node_and_update_degrees(self, node: str, in_degree: Dict[str, int]) -> None:
        """Remove node from graph and update in-degrees of successors"""
        if node in in_degree:
            del in_degree[node]

        for successor in self.graph.successors(node):
            if successor in in_degree:
                in_degree[successor] -= 1

    def validate(self) -> bool:
        """Validate dependency graph."""
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                raise ValueError(f"Circular dependencies detected: {cycles}")
        except nx.NetworkXNoCycle:
            pass

        # Check all dependencies exist
        for node in self.graph.nodes():
            module_info = self.module_info.get(node)
            if module_info:
                for dep in module_info.depends_on:
                    if dep not in self.module_info:
                        raise ValueError(f"Module '{node}' depends on '{dep}' which doesn't exist")
        return True
