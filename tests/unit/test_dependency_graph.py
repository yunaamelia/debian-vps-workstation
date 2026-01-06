import unittest.mock

import pytest

from configurator.core.parallel import DependencyGraph


class TestDependencyGraph:
    def test_topo_sort_simple(self):
        graph = DependencyGraph()
        graph.add_module("A")
        graph.add_module("B", depends_on=["A"])
        graph.add_module("C", depends_on=["B"])

        batches = graph.get_parallel_batches()
        # Expect [['A'], ['B'], ['C']]
        assert batches == [["A"], ["B"], ["C"]]

    def test_parallel_independent(self):
        graph = DependencyGraph()
        graph.add_module("A")
        graph.add_module("B")
        graph.add_module("C")

        batches = graph.get_parallel_batches()
        # Expect [['A', 'B', 'C']] (order within layer doesn't matter, but all together)
        assert len(batches) == 1
        assert set(batches[0]) == {"A", "B", "C"}

    def test_mixed_dependencies(self):
        graph = DependencyGraph()
        graph.add_module("sys")
        graph.add_module("py", depends_on=["sys"])
        graph.add_module("node", depends_on=["sys"])
        graph.add_module("app", depends_on=["py", "node"])

        batches = graph.get_parallel_batches()
        # Batch 1: sys
        # Batch 2: py, node
        # Batch 3: app
        assert batches[0] == ["sys"]
        assert set(batches[1]) == {"py", "node"}
        assert batches[2] == ["app"]

    def test_force_sequential(self):
        """Test that force_sequential modules run in their own batch"""
        graph = DependencyGraph()
        graph.add_module("A")
        graph.add_module("B", force_sequential=True)
        graph.add_module("C")

        batches = graph.get_parallel_batches()

        # Flatten and check content
        all_mods = [m for b in batches for m in b]
        assert set(all_mods) == {"A", "B", "C"}

        # Check B is alone in its batch
        b_batch_idx = -1
        for i, batch in enumerate(batches):
            if "B" in batch:
                b_batch_idx = i
                assert len(batch) == 1, "Sequential module B must be alone"

        assert b_batch_idx >= 0

    def test_cycle_detection(self):
        graph = DependencyGraph()
        graph.add_module("A", depends_on=["B"])
        graph.add_module("B", depends_on=["A"])

        with pytest.raises(ValueError, match="Circular dependency"):
            graph.get_parallel_batches()

    def test_missing_dependency_validation(self):
        graph = DependencyGraph()
        graph.add_module("A", depends_on=["NonExistent"])

        with pytest.raises(ValueError, match="depends on 'NonExistent' which doesn't exist"):
            graph.validate()

    def test_visualize_mock(self):
        graph = DependencyGraph()
        graph.add_module("A")

        # Test 1: Matplotlib not installed (safe fail)
        with unittest.mock.patch.dict("sys.modules", {"matplotlib.pyplot": None}):
            graph.visualize("test.png")
            # Should not raise

        # Test 2: Matplotlib success
        mock_mpl = unittest.mock.MagicMock()
        mock_mpl.__path__ = []  # Simulate package
        mock_plt = unittest.mock.MagicMock()

        # Patch sys.modules to simulate matplotlib installed
        with unittest.mock.patch.dict(
            "sys.modules", {"matplotlib": mock_mpl, "matplotlib.pyplot": mock_plt}
        ):
            # Ensure import matplotlib.pyplot works
            mock_mpl.pyplot = mock_plt

            with unittest.mock.patch("networkx.spring_layout"):
                with unittest.mock.patch("networkx.draw"):
                    graph.visualize("test.png")
                    mock_plt.savefig.assert_called_once()
