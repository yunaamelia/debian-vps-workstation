import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

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

    Features:
    - Topological sort with level grouping
    - Circular dependency detection
    - Parallel batch generation
    - Graph visualization (optional, requires matplotlib)
    """

    def __init__(self, logger: logging.Logger = None):
        self.graph = nx.DiGraph()
        self.logger = logger or logging.getLogger(__name__)
        self.module_info: Dict[str, ModuleDependency] = {}

    def add_module(
        self, name: str, depends_on: List[str] = None, force_sequential: bool = False
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
                    # Depending on logic, we might not have added the dependency yet.
                    # This is just a warning or implicit addition.
                    # For safety, we can add the node.
                    self.graph.add_node(dependency)
                self.graph.add_edge(dependency, name)

    def get_parallel_batches(self) -> List[List[str]]:
        """
        Get modules grouped into batches that can run in parallel.

        Uses Kahn's algorithm for topological sort with level grouping.

        Returns:
            List of batches, where each batch contains modules
            that can be executed in parallel

        Raises:
            ValueError: If circular dependency detected
        """
        batches = []
        # Create a working copy of in-degrees
        in_degree = dict(self.graph.in_degree())

        # Filter in_degree to only include nodes present in graph
        # (Though in theory the dict above does exactly that)

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

    def visualize(self, output_file: str = "dependency_graph.png") -> None:
        """
        Generate dependency graph visualization (requires matplotlib).

        Args:
            output_file: Path to save graph image
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            self.logger.warning(
                "matplotlib not installed, skipping visualization. "
                "Install with: pip install matplotlib"
            )
            return

        try:
            pos = nx.spring_layout(self.graph)

            # Color nodes by batch
            batches = self.get_parallel_batches()
            color_map = {}
            for i, batch in enumerate(batches):
                for node in batch:
                    color_map[node] = f"C{i % 10}"

            node_colors = [color_map.get(node, "lightblue") for node in self.graph.nodes()]

            plt.figure(figsize=(12, 8))
            nx.draw(
                self.graph,
                pos,
                with_labels=True,
                node_color=node_colors,
                node_size=3000,
                font_size=9,
                font_weight="bold",
                arrows=True,
                edge_color="gray",
                arrowsize=20,
            )

            plt.title("Module Dependency Graph\n(Same color = same batch)", fontsize=14)
            plt.tight_layout()
            plt.savefig(output_file, dpi=150, bbox_inches="tight")
            plt.close()

            self.logger.info(f"Dependency graph saved to {output_file}")
        except Exception as e:
            self.logger.warning(f"Failed to generate visualization: {e}")

    def validate(self) -> bool:
        """
        Validate dependency graph.

        Returns:
            True if valid
        """
        # Check for cycles
        try:
            cycles = list(nx.simple_cycles(self.graph))
            if cycles:
                raise ValueError(f"Circular dependencies detected: {cycles}")
        except nx.NetworkXNoCycle:
            pass  # No cycles found, good

        # Check all dependencies exist
        for node in self.graph.nodes():
            module_info = self.module_info.get(node)
            if module_info:
                for dep in module_info.depends_on:
                    if dep not in self.module_info:
                        raise ValueError(f"Module '{node}' depends on '{dep}' which doesn't exist")

        # Check for disconnected components (warning only)
        if hasattr(nx, "is_weakly_connected") and not nx.is_weakly_connected(self.graph):
            # Just logs a warning, doesn't fail validation
            pass

        return True


class ParallelModuleExecutor:
    """
    Thread-safe executor for parallel module execution.
    """

    def __init__(
        self,
        max_workers: int = 3,
        logger: Optional[logging.Logger] = None,
        reporter: Optional[Any] = None,
    ):
        """
        Initialize parallel executor.

        Args:
            max_workers: Maximum number of parallel modules (default: 3)
            logger: Logger instance
            reporter: Progress reporter for UI updates
        """
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)
        self.reporter = reporter

        # Thread-safe result storage
        self.results: Dict[str, bool] = {}
        self.results_lock = threading.Lock()

        # Shared cancellation flag
        self.should_stop = threading.Event()

        # Execution metadata
        self.start_times: Dict[str, float] = {}
        self.end_times: Dict[str, float] = {}

    def get_execution_stats(self) -> Dict[str, Dict[str, float]]:
        """Get execution statistics."""
        stats = {}
        with self.results_lock:
            for name, start in self.start_times.items():
                end = self.end_times.get(name)
                if end:
                    stats[name] = {"start": start, "end": end, "duration": end - start}
        return stats

    def execute_batches(
        self,
        batches: List[List[str]],
        module_registry: Dict[str, Any],
        execution_handler: Optional[Callable[[str, Any], bool]] = None,
    ) -> Dict[str, bool]:
        """
        Execute module batches in parallel.

        Args:
            batches: List of module batches (from dependency graph)
            module_registry: Dict mapping module name to instance
            execution_handler: Optional custom handler to execute module logic

        Returns:
            Dict of module name -> success status
        """
        total_batches = len(batches)

        # Default handler if none provided
        if execution_handler is None:
            execution_handler = self._execute_module_internal

        for batch_index, batch in enumerate(batches, 1):
            self.logger.info(
                f"\n{'='*60}\n"
                f"Batch {batch_index}/{total_batches}: {len(batch)} module(s)\n"
                f"{'='*60}"
            )

            if len(batch) == 1:
                # Single module, execute directly logic
                module_name = batch[0]
                module = module_registry[module_name]

                self.logger.info(f"Executing: {module.name}")
                success = execution_handler(module_name, module)

                with self.results_lock:
                    self.results[module_name] = success

                if not success:
                    self.logger.error(f"Module '{module_name}' failed, stopping installation")
                    return self.results

            else:
                # Multiple modules, execute in parallel
                self.logger.info("Running in parallel:")
                for module_name in batch:
                    module = module_registry[module_name]
                    self.logger.info(f"  • {module.name}")

                success = self._execute_parallel_batch(batch, module_registry, execution_handler)

                if not success:
                    self.logger.error("Batch execution failed, stopping installation")
                    return self.results

        return self.results

    def _execute_parallel_batch(
        self,
        batch: List[str],
        module_registry: Dict[str, Any],
        execution_handler: Callable[[str, Any], bool],
    ) -> bool:
        """
        Execute a batch of modules in parallel (thread-safe).
        """
        # Limit workers to batch size
        workers = min(self.max_workers, len(batch))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all modules
            future_to_module = {
                executor.submit(execution_handler, name, module_registry[name]): name
                for name in batch
            }

            # Wait for completion
            batch_success = True

            for future in as_completed(future_to_module):
                module_name = future_to_module[future]

                try:
                    success = future.result()

                    with self.results_lock:
                        self.results[module_name] = success

                    if not success:
                        batch_success = False
                        self.should_stop.set()

                        # Cancel remaining futures
                        for f in future_to_module:
                            if not f.done():
                                f.cancel()

                        break

                except Exception as e:
                    self.logger.error(
                        f"Module '{module_name}' raised exception: {e}", exc_info=True
                    )
                    batch_success = False

                    with self.results_lock:
                        self.results[module_name] = False

                    self.should_stop.set()

                    # Cancel remaining
                    for f in future_to_module:
                        if not f.done():
                            f.cancel()

                    break

        return batch_success

    def _execute_module_internal(self, module_name: str, module: Any) -> bool:
        """
        Execute a single module (thread-safe wrapper).
        """
        # Check if we should stop
        if self.should_stop.is_set():
            self.logger.warning(
                f"[{threading.current_thread().name}] "
                f"Skipping {module_name} due to previous failure"
            )
            return False

        thread_name = threading.current_thread().name
        start_time = time.time()

        try:
            self.logger.info(f"[{thread_name}] Starting {module_name}")

            with self.results_lock:
                self.start_times[module_name] = start_time

            # Validate
            if hasattr(module, "validate") and not module.validate():
                self.logger.error(f"[{thread_name}] {module_name} validation failed")
                return False

            # Configure
            if hasattr(module, "configure") and not module.configure():
                self.logger.error(f"[{thread_name}] {module_name} configuration failed")
                return False

            # Verify
            if hasattr(module, "verify") and not module.verify():
                self.logger.error(f"[{thread_name}] {module_name} verification failed")
                return False

            end_time = time.time()
            duration = end_time - start_time

            with self.results_lock:
                self.end_times[module_name] = end_time

            self.logger.info(
                f"[{thread_name}] ✅ {module_name} complete " f"(took {duration:.1f}s)"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"[{thread_name}] {module_name} failed with exception: {e}", exc_info=True
            )
            return False
