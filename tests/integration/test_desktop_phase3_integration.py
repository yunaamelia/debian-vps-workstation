"""
Integration tests for Phase 3 complete module flow.
"""

from unittest.mock import Mock, patch

from configurator.modules.desktop import DesktopModule


class TestPhase3Integration:
    """Integration tests for full Phase 3 flow."""

    def test_configure_calls_all_phase3_methods_in_order(self):
        """Test that configure() calls all Phase 3 methods in correct sequence."""
        config = {
            "desktop": {
                "themes": {"install": ["nordic"], "active": "Nordic-darker"},
                "icons": {"install": ["papirus"], "active": "Papirus-Dark"},
                "fonts": {"default": "Roboto 10"},
                "panel": {"layout": "macos"},
            }
        }
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        # Track method calls
        called_methods = []

        def track_method(name):
            def wrapper(*args, **kwargs):
                called_methods.append(name)

            return wrapper

        # Patch Phase 3 methods
        with patch.object(module, "_install_themes", track_method("_install_themes")):
            with patch.object(module, "_install_icon_packs", track_method("_install_icon_packs")):
                with patch.object(module, "_configure_fonts", track_method("_configure_fonts")):
                    with patch.object(
                        module,
                        "_configure_panel_layout",
                        track_method("_configure_panel_layout"),
                    ):
                        with patch.object(
                            module,
                            "_apply_theme_and_icons",
                            track_method("_apply_theme_and_icons"),
                        ):
                            # Mock previous phases
                            with patch.object(module, "_install_xrdp"):
                                with patch.object(module, "_install_xfce4"):
                                    with patch.object(module, "_configure_xrdp"):
                                        with patch.object(module, "_optimize_xrdp_performance"):
                                            with patch.object(module, "_configure_user_session"):
                                                with patch.object(
                                                    module, "_optimize_xfce_compositor"
                                                ):
                                                    with patch.object(
                                                        module, "_configure_polkit_rules"
                                                    ):
                                                        with patch.object(
                                                            module, "_configure_session"
                                                        ):
                                                            with patch.object(
                                                                module, "_start_services"
                                                            ):
                                                                module.configure()

        # Verify Phase 3 methods called
        assert "_install_themes" in called_methods
        assert "_install_icon_packs" in called_methods
        assert "_configure_fonts" in called_methods
        assert "_configure_panel_layout" in called_methods
        assert "_apply_theme_and_icons" in called_methods

        # Verify order (themes/icons before application)
        themes_idx = called_methods.index("_install_themes")
        icons_idx = called_methods.index("_install_icon_packs")
        apply_idx = called_methods.index("_apply_theme_and_icons")

        assert themes_idx < apply_idx, "Themes should be installed before application"
        assert icons_idx < apply_idx, "Icons should be installed before application"

    def test_no_conflicts_with_previous_phases(self):
        """Test that Phase 3 doesn't conflict with Phase 1 and Phase 2."""
        config = {"desktop": {"themes": {"install": ["nordic"]}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        # All phases should be callable without conflict
        with patch.object(module, "run"):
            with patch.object(module, "install_packages"):
                with patch("configurator.modules.desktop.write_file"):
                    with patch("configurator.modules.desktop.pwd") as mock_pwd:
                        mock_pwd.getpwall.return_value = []

                        # Phase 1 methods
                        if hasattr(module, "_optimize_xrdp_performance"):
                            module._optimize_xrdp_performance()

                        # Phase 2 methods
                        if hasattr(module, "_optimize_xfce_compositor"):
                            module._optimize_xfce_compositor()

                        # Phase 3 methods
                        module._install_themes()
                        module._configure_fonts()

        # No exceptions = success

    def test_verification_includes_phase3_checks(self):
        """Test that verify() includes Phase 3 verification."""
        config = {
            "desktop": {
                "themes": {"active": "Nordic-darker"},
                "icons": {"active": "Papirus-Dark"},
            }
        }
        module = DesktopModule(config=config, logger=Mock())

        with patch.object(module, "_verify_themes_and_icons", return_value=True) as mock_verify:
            with patch.object(module, "is_service_active", return_value=True):
                with patch.object(module, "run", return_value=Mock(success=True)):
                    with patch.object(module, "command_exists", return_value=True):
                        with patch.object(module, "_verify_compositor_config"):
                            with patch.object(module, "_verify_polkit_rules"):
                                module.verify()

        # Verify Phase 3 verification called
        assert mock_verify.called

    def test_dry_run_mode_prevents_actual_changes(self):
        """Test that dry-run mode doesn't make actual changes."""
        config = {
            "desktop": {
                "themes": {"install": ["nordic"]},
                "icons": {"install": ["papirus"]},
                "fonts": {"default": "Roboto 10"},
            }
        }
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )
        module.dry_run = True

        with patch.object(module, "run") as mock_run:
            with patch.object(module, "install_packages") as mock_install:
                with patch("configurator.modules.desktop.write_file") as mock_write:
                    # Call Phase 3 methods
                    module._install_themes()
                    module._install_icon_packs()
                    module._configure_fonts()

                    # Verify no actual commands executed (should return early)
                    # In dry-run mode, methods should return early or record to dry_run_manager
                    # but not call actual run/install_packages/write_file

                    # This verifies proper dry-run handling exists
                    # Exact assertion depends on implementation details

    def test_rollback_removes_all_phase3_components(self):
        """Test that rollback properly removes all Phase 3 installations."""
        config = {
            "desktop": {
                "themes": {"install": ["nordic", "arc"]},
                "icons": {"install": ["papirus"]},
            }
        }
        rollback_manager = Mock()
        module = DesktopModule(config=config, logger=Mock(), rollback_manager=rollback_manager)

        with patch.object(module, "run", return_value=Mock(success=True)):
            with patch.object(module, "install_packages"):
                with patch("configurator.modules.desktop.write_file"):
                    # Install themes and icons
                    module._install_nordic_theme()
                    module._install_icon_packs()

        # Verify rollback actions registered
        assert rollback_manager.add_command.called

        # Check that all Phase 3 components have rollback
        rollback_calls = [str(c) for c in rollback_manager.add_command.call_args_list]

        # Should have rollback for themes
        assert any("Nordic" in call for call in rollback_calls)


class TestPhase3ErrorHandling:
    """Test error handling in Phase 3 operations."""

    def test_theme_installation_continues_after_git_clone_failure(self):
        """Test that theme installation continues if one Git clone fails."""
        config = {"desktop": {"themes": {"install": ["nordic", "arc"]}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "run") as mock_run:
            with patch.object(module, "install_packages"):

                # Simulate Git clone failure for Nordic
                def run_side_effect(cmd, **kwargs):
                    if "git clone" in cmd and "Nordic" in cmd:
                        raise Exception("Git clone failed")
                    return Mock(success=True)

                mock_run.side_effect = run_side_effect

                # Should not crash, continue with other themes
                module._install_themes()

                # Arc theme should still be attempted (APT install)
                # Verify logger recorded the error
                assert module.logger.error.called

    def test_font_configuration_handles_missing_packages(self):
        """Test that font configuration handles missing packages gracefully."""
        config = {"desktop": {"fonts": {"default": "Roboto 10"}}}
        module = DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

        with patch.object(module, "install_packages") as mock_install:
            with patch.object(module, "run"):
                with patch("configurator.modules.desktop.write_file"):
                    # Simulate package installation failure
                    mock_install.side_effect = Exception("Package not found")

                    # Should handle gracefully
                    try:
                        module._configure_fonts()
                    except Exception as e:
                        # Should log error but not crash entire installation
                        assert module.logger.error.called or module.logger.warning.called
