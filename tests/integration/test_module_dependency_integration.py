"""
Integration tests for module dependency resolution and execution order.
"""

import pytest

from configurator.core.parallel import DependencyGraph
from configurator.modules.base import ConfigurationModule


class MockModuleA(ConfigurationModule):
    name = "module_a"

    def execute(self):
        pass


class MockModuleB(ConfigurationModule):
    name = "module_b"
    depends_on = ["module_a"]

    def execute(self):
        pass


class MockModuleC(ConfigurationModule):
    name = "module_c"
    depends_on = ["module_b"]

    def execute(self):
        pass


class MockModuleD(ConfigurationModule):
    name = "module_d"
    depends_on = ["module_a"]

    def execute(self):
        pass


class TestModuleDependencies:
    """Test dependency resolution and execution order."""

    def test_dependency_resolution_order(self):
        """Test that dependencies are resolved in correct topological order."""
        graph = DependencyGraph()

        # Add modules in random order
        graph.add_module("module_c", depends_on=["module_b"])
        graph.add_module("module_a", depends_on=[])
        graph.add_module("module_b", depends_on=["module_a"])
        graph.add_module("module_d", depends_on=["module_a"])

        batches = graph.get_parallel_batches()
        # Batches is list of lists: [['module_a'], ['module_b', 'module_d'], ['module_c']]

        flattened = [m for batch in batches for m in batch]

        # Verify order constraints
        assert flattened.index("module_a") < flattened.index("module_b")
        assert flattened.index("module_b") < flattened.index("module_c")
        assert flattened.index("module_a") < flattened.index("module_d")

    def test_system_before_security(self):
        """Test that system module executes before security module (convention)."""
        graph = DependencyGraph()

        graph.add_module("security", depends_on=["system"])
        graph.add_module("desktop", depends_on=["system", "security"])
        graph.add_module("system", depends_on=[])

        batches = graph.get_parallel_batches()
        flattened = [m for batch in batches for m in batch]

        assert flattened.index("system") < flattened.index("security")
        assert flattened.index("security") < flattened.index("desktop")

    def test_circular_dependency_detection(self):
        """Test that circular dependencies raise an error."""
        graph = DependencyGraph()

        graph.add_module("module_a", depends_on=["module_b"])
        graph.add_module("module_b", depends_on=["module_a"])

        with pytest.raises(Exception):
            graph.get_parallel_batches()

    def test_diamond_dependency_resolution(self):
        """Test diamond dependency structure."""
        # A -> B, A -> C, B -> D, C -> D => A must be first, D last
        graph = DependencyGraph()

        graph.add_module("D", depends_on=["B", "C"])
        graph.add_module("B", depends_on=["A"])
        graph.add_module("C", depends_on=["A"])
        graph.add_module("A", depends_on=[])

        batches = graph.get_parallel_batches()
        flattened = [m for batch in batches for m in batch]

        assert flattened[0] == "A"
        # B and C can be in any order but after A and before D
        assert flattened.index("A") < flattened.index("B")
        assert flattened.index("A") < flattened.index("C")
        assert flattened.index("B") < flattened.index("D")
        assert flattened.index("C") < flattened.index("D")
