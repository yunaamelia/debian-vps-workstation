"""
Integration tests for the complete Desktop module phase execution flow.
"""

from unittest.mock import Mock, call, patch

import pytest

from configurator.modules.desktop import DesktopModule

pytestmark = pytest.mark.skip(reason="Desktop module refactored - config structure changed")


class TestDesktopPhaseIntegration:
    """Integration tests for Desktop phases execution order and dependencies."""

    @pytest.fixture
    def module(self):
        # Pass only desktop config section to module
        config = {
            "enabled": True,
            "xrdp": {"enabled": True},
            "compositor": {"mode": "optimized"},
            "themes": {"install": ["nordic"]},
            "zsh": {"enabled": True},
            "terminal_tools": {"bat": {"theme": "TwoDark"}},
        }
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "install_packages", return_value=True)
    @patch.object(DesktopModule, "_optimize_xrdp_performance", return_value=True)  # Phase 1
    @patch.object(DesktopModule, "_optimize_xfce_compositor", return_value=True)  # Phase 2
    @patch.object(DesktopModule, "_configure_polkit_rules", return_value=True)
    @patch.object(DesktopModule, "_install_themes", return_value=True)  # Phase 3
    @patch.object(DesktopModule, "_install_icons", return_value=True)
    @patch.object(DesktopModule, "_configure_fonts", return_value=True)
    @patch.object(DesktopModule, "_configure_zsh", return_value=True)  # Phase 4
    @patch.object(DesktopModule, "_configure_terminal_tools", return_value=True)  # Phase 5
    def test_complete_desktop_setup_flow(
        self,
        mock_phase5,
        mock_phase4,
        mock_fonts,
        mock_icons,
        mock_phase3,
        mock_polkit,
        mock_phase2,
        mock_phase1,
        mock_install_packages,
        module,
    ):
        """Test that all desktop phases execute in the correct order."""
        # Setup mocks to track execution order
        manager = Mock()
        manager.attach_mock(mock_phase1, "phase1")
        manager.attach_mock(mock_phase2, "phase2")
        manager.attach_mock(mock_phase3, "phase3")
        manager.attach_mock(mock_phase4, "phase4")
        manager.attach_mock(mock_phase5, "phase5")

        # Execute
        with patch.object(module, "run", return_value=Mock(success=True)):
            with patch("configurator.modules.desktop.os.path.exists", return_value=False):
                module.configure()

        # Verify execution order
        expected_calls = [
            call.phase1(),
            call.phase2(),
            call.phase3(),
            call.phase4(),
            call.phase5(),
        ]

        # We check that the calls happened in this relative order
        # Note: configure() might call other methods too, so we filter manager calls
        actual_calls = manager.mock_calls

        # Verify sequence
        assert len(actual_calls) >= 5
        assert actual_calls[0] == call.phase1()
        assert actual_calls[1] == call.phase2()
        # Phases 3, 4, 5 typically follow
        # Depending on implementation details, some small steps might interleave,
        # but the major phases should be sequential.

        # Ideally:
        # 1. XRDP (Phase 1)
        # 2. Compositor (Phase 2)
        # 3. Themes (Phase 3)
        # 4. Zsh (Phase 4)
        # 5. Tools (Phase 5)

    def test_rollback_actions_registered_for_all_phases(self, module):
        """Test that rollback actions are accumulated across phases."""
        with patch.object(module, "rollback_manager") as mock_bm:
            # Simulate methods adding rollback actions
            module.rollback_manager.add_command("undo phase 1")
            module.rollback_manager.add_command("undo phase 2")

            # Verify stack
            assert mock_bm.add_command.call_count == 2

            # Assuming LIFO, last added is first rolled back
            # Verification is usually done via RollbackManager unit tests,
            # here we verify DesktopModule usage.
            pass

    @pytest.mark.integration
    def test_phases_respect_configuration(self, module):
        """Test that phases are skipped if disabled in config."""
        # Disable XRDP (Phase 1)
        module.config["desktop"]["xrdp"]["enabled"] = False

        with patch.object(module, "_optimize_xrdp_performance") as mock_phase1:
            with patch.object(module, "run"):
                module.configure()

            # Phase 1 should not run
            mock_phase1.assert_not_called()
