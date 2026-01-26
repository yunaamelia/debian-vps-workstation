from typing import List

from configurator.core.dependency import DependencyGraph
from configurator.dependencies.registry import DependencyRegistry


class DependencyGraphVisualizer:
    """
    Visualize module dependencies as ASCII tree.
    """

    def __init__(self, modules: List[str]) -> None:
        self.modules = modules

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect dependency cycles in the registry.
        """
        # Build full graph from registry
        graph = (
            DependencyRegistry._registry
        )  # This is internal, but for visualization ok or use DependencyGraph

        # We can reuse DependencyGraph's detection if it exists, but it throws error on add_module loop.
        # So we can try to build a graph and catch it, or implement simple DFS here.

        # Simple DFS for cycle detection used by the test expectation
        logger = None
        dep_graph = DependencyGraph(logger=logger)

        for module_name in self.modules:
            dependency = DependencyRegistry.get(module_name)
            if dependency:
                try:
                    dep_graph.add_module(module_name, depends_on=dependency.depends_on)
                except ValueError as e:
                    if "Dependency cycle detected" in str(e):
                        # Parsing cycle from error message is ugly but simple for now
                        # Or we expose the cycle detection from DependencyGraph
                        return [["cycle detected"]]

        # If we want to return the exact cycle, we might need to query the graph internals or catch the specific error
        # Let's inspect DependencyGraph.add_module implementation in core/dependency
        # Actually, let's just implement a standalone cycle detector here since we have the registry.

        cycles = []
        visited = set()
        path: List[str] = []

        def visit(node: str) -> None:
            if node in path:
                cycle = path[path.index(node) :] + [node]
                cycles.append(cycle)
                return
            if node in visited:
                return

            visited.add(node)
            path.append(node)

            dep = DependencyRegistry.get(node)
            if dep:
                for neighbor in dep.depends_on:
                    visit(neighbor)

            path.pop()

        for module in self.modules:
            visit(module)

        return cycles

    def render_tree(self) -> str:
        """
        Render dependency tree as ASCII art via Execution Batches.
        """
        # Build execution batches using core logic
        # We assume the user has configured logging elsewhere or we pass None
        graph = DependencyGraph(logger=None)

        for module_name in self.modules:
            dependency = DependencyRegistry.get(module_name)
            if dependency:
                graph.add_module(
                    module_name,
                    depends_on=dependency.depends_on,
                    force_sequential=dependency.force_sequential,
                )
            else:
                graph.add_module(module_name)

        try:
            batches = graph.get_execution_batches()
        except Exception as e:
            return f"Error building graph: {e}"

        # Render
        lines = []
        lines.append(
            "Installation Order ({} batch{}):".format(
                len(batches), "es" if len(batches) != 1 else ""
            )
        )
        lines.append("")

        for i, batch in enumerate(batches, 1):
            execution_type = (
                "Sequential" if len(batch) == 1 and self._is_sequential(batch[0]) else "Parallel"
            )
            lines.append(f"Batch {i} ({execution_type}):")

            for j, module_name in enumerate(batch):
                is_last = j == len(batch) - 1
                prefix = "  └─" if is_last else "  ├─"

                dependency = DependencyRegistry.get(module_name)
                priority = dependency.priority if dependency else 50

                lines.append(f"{prefix} {module_name} [priority: {priority}]")

                # Show dependencies
                if dependency and dependency.depends_on:
                    dep_prefix = "     " if is_last else "  │  "
                    deps_str = ", ".join(dependency.depends_on)
                    lines.append(f"{dep_prefix}└─ depends on: {deps_str}")

            lines.append("")

        # Add execution time estimate
        estimated_time = self._estimate_time(batches)
        lines.append(f"Estimated installation time: {estimated_time}")

        return "\n".join(lines)

    def render_flat(self) -> str:
        """Render as flat indented list."""
        lines = []

        for module_name in self.modules:
            dependency = DependencyRegistry.get(module_name)

            # Module name
            lines.append(f"• {module_name}")

            # Dependencies
            if dependency and dependency.depends_on:
                for dep in dependency.depends_on:
                    lines.append(f"  ↳ requires: {dep}")

            # Conflicts
            if dependency and dependency.conflicts_with:
                for conflict in dependency.conflicts_with:
                    lines.append(f"  ⚠ conflicts with: {conflict}")

        return "\n".join(lines)

    def _is_sequential(self, module_name: str) -> bool:
        """Check if module requires sequential execution."""
        dependency = DependencyRegistry.get(module_name)
        return dependency.force_sequential if dependency else False

    def _estimate_time(self, batches: List[List[str]]) -> str:
        """Estimate installation time based on batches."""
        # Rough estimate: 3 min per batch overhead + 2 min per module
        # If parallel, batch time is overhead + max(module_time) roughly, but simplified here
        minutes = len(batches) * 3 + sum(len(batch) for batch in batches) * 2

        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m"
