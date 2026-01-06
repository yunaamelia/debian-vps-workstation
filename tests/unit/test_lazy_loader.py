import sys
import threading
import time
from unittest.mock import MagicMock, patch

from configurator.core.lazy_loader import LazyLoader, LazyModule, lazy_import


class TestLazyLoader:
    def test_lazy_import_deferred(self):
        """Verify imports are deferred until accessed"""
        # We need a module that is NOT already imported.
        # 'uuid' is often not imported yet, or we can use a made up one if we mock importlib

        module_name = "uuid"
        if module_name in sys.modules:
            del sys.modules[module_name]

        loader = LazyLoader(module_name)

        assert not loader.is_loaded()
        assert module_name not in sys.modules

        # Access attribute
        _ = loader.uuid4

        assert loader.is_loaded()
        assert module_name in sys.modules

    def test_lazy_object_import(self):
        """Test importing a specific object lazily"""
        loader = LazyLoader("json", "dumps")
        assert not loader.is_loaded()

        # Call it
        result = loader({"key": "value"})
        assert result == '{"key": "value"}'
        assert loader.is_loaded()

    def test_caching(self):
        """Test that import is cached"""
        loader = LazyLoader("os", "path")

        obj1 = loader._load()
        time1 = loader.get_import_time()

        obj2 = loader._load()
        time2 = loader.get_import_time()

        assert obj1 is obj2
        assert time1 == time2

    def test_preload(self):
        """Test explicit preload"""
        loader = LazyLoader("sys")
        assert not loader.is_loaded()
        loader.preload()
        assert loader.is_loaded()

    def test_thread_safety(self):
        """Test thread safety of lazy loading"""
        # We use a mock to simulate slow import
        mock_module = MagicMock()
        mock_module.some_attr = 1

        import_count = 0

        def slow_import(name):
            nonlocal import_count
            time.sleep(0.1)
            import_count += 1
            return mock_module

        with patch("importlib.import_module", side_effect=slow_import):
            loader = LazyLoader("fake_slow_module")

            def worker():
                _ = loader.some_attr

            threads = [threading.Thread(target=worker) for _ in range(10)]

            start = time.time()
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            end = time.time()

            # Should have only imported once
            assert import_count == 1
            assert loader.is_loaded()

    def test_import_time_metrics(self):
        """Test that import time is recorded"""
        loader = LazyLoader("time")
        assert loader.get_import_time() == 0.0

        loader._load()
        assert loader.get_import_time() > 0.0


class TestLazyModule:
    def test_lazy_module_registration(self):
        """Test LazyModule registration helper"""
        registry = {}
        LazyModule.register_lazy(registry, "test_mod", "os", "path")

        assert "test_mod" in registry
        assert isinstance(registry["test_mod"], LazyModule)

        # access it
        path_mod = registry["test_mod"]
        assert path_mod.join("a", "b") == "a/b"


def test_lazy_import_helper():
    """Test the functional helper"""
    loader = lazy_import("os.path")
    assert not loader.is_loaded()
    assert loader.join("a", "b") == "a/b"
