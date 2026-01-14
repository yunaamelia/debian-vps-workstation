"""
Integration tests for Phase 5 tool chain.
"""

from unittest.mock import Mock, patch

from configurator.modules.desktop import DesktopModule


class TestPhase5Integration:
    """Integration tests for Phase 5 complete flow."""

    def test_configure_calls_all_phase5_methods(self):
        """Test that configure() calls all Phase 5 methods."""
        config = {"desktop": {"terminal_tools": {"bat": {}, "exa": {}, "fzf": {}, "zoxide": {}}}}
        module = DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

        # Track method calls
        called_methods = []

        def track(name):
            def wrapper(*args, **kwargs):
                called_methods.append(name)

            return wrapper

        from contextlib import ExitStack

        with ExitStack() as stack:
            # Patch Phase 5 methods to track calls
            stack.enter_context(
                patch.object(module, "_configure_bat_advanced", track("_configure_bat_advanced"))
            )
            stack.enter_context(
                patch.object(module, "_configure_eza_advanced", track("_configure_eza_advanced"))
            )
            stack.enter_context(
                patch.object(
                    module, "_configure_zoxide_advanced", track("_configure_zoxide_advanced")
                )
            )
            stack.enter_context(
                patch.object(module, "_configure_fzf_advanced", track("_configure_fzf_advanced"))
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_create_tool_integration_scripts",
                    track("_create_tool_integration_scripts"),
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_update_zshrc_for_advanced_tools",
                    track("_update_zshrc_for_advanced_tools"),
                )
            )
            stack.enter_context(
                patch.object(
                    module,
                    "_install_optional_productivity_tools",
                    track("_install_optional_productivity_tools"),
                )
            )

            # Mock all previous phases to avoid actual execution
            stack.enter_context(patch.object(module, "_install_xrdp"))
            stack.enter_context(patch.object(module, "_install_xfce4"))
            stack.enter_context(patch.object(module, "_configure_xrdp"))
            stack.enter_context(patch.object(module, "_optimize_xrdp_performance"))
            stack.enter_context(patch.object(module, "_configure_user_session"))
            stack.enter_context(patch.object(module, "_optimize_xfce_compositor"))
            stack.enter_context(patch.object(module, "_configure_polkit_rules"))
            stack.enter_context(patch.object(module, "_install_themes"))
            stack.enter_context(patch.object(module, "_install_icon_packs"))
            stack.enter_context(patch.object(module, "_configure_fonts"))
            stack.enter_context(patch.object(module, "_configure_panel_layout"))
            stack.enter_context(patch.object(module, "_apply_theme_and_icons"))
            stack.enter_context(patch.object(module, "_install_and_configure_zsh"))
            stack.enter_context(patch.object(module, "_configure_session"))
            stack.enter_context(patch.object(module, "_start_services"))
            stack.enter_context(patch.object(module, "_configure_xwrapper"))

            # Run configure
            module.configure()

        # Verify Phase 5 methods called
        assert "_configure_bat_advanced" in called_methods
        assert "_configure_eza_advanced" in called_methods
        assert "_configure_zoxide_advanced" in called_methods
        assert "_configure_fzf_advanced" in called_methods
        assert "_create_tool_integration_scripts" in called_methods
        assert "_update_zshrc_for_advanced_tools" in called_methods

    def test_zshrc_updated_with_all_tool_configs(self):
        """Test that .zshrc is updated with all tool configurations."""
        config = {"desktop": {"terminal_tools": {}}}
        module = DesktopModule(config=config, logger=Mock())

        # Configure all tools
        module._configure_bat_advanced()
        module._configure_eza_advanced()
        module._configure_zoxide_advanced()
        module._configure_fzf_advanced()

        # Generate zshrc block
        zshrc_block = module._generate_advanced_tools_zshrc_block()

        # Verify all tool configs present
        assert "eza" in zshrc_block.lower()
        assert "zoxide" in zshrc_block.lower()
        assert "fzf" in zshrc_block.lower()
        assert "PATH=" in zshrc_block  # PATH for scripts
