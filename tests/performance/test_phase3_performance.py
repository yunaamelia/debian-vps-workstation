"""Performance tests for Phase 3."""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestPhase3Performance:
    """Performance tests for theme installation."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    def test_theme_installation_performance(self, module):
        """Test theme installation performance."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            with patch("os.path.exists", return_value=True):
                import time

                start = time.time()
                module._install_themes()
                duration = time.time() - start
                # Should be fast when themes already installed
                assert duration < 5.0
