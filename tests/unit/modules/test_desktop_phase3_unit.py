"""
Unit tests for Phase 3 theme, icon, font, and panel functionality.
"""

import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestThemeInstallation:
    """Unit tests for theme installation methods."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"themes": {"install": ["nordic", "arc"], "active": "Nordic-darker"}}}
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    @patch.object(DesktopModule, "run")
    @patch.object(DesktopModule, "install_packages")
    def test_install_themes_installs_dependencies(self, mock_install_pkg, mock_run, module):
        """Test that theme dependencies are installed first."""
        mock_run.return_value = Mock(success=True)
        module._install_themes()

        # Verify dependencies installed
        mock_install_pkg.assert_called()

        # Check for required packages
        all_packages = []
        for call_obj in mock_install_pkg.call_args_list:
            all_packages.extend(call_obj[0][0])

        required_deps = ["gtk2-engines-murrine", "gtk2-engines-pixbuf", "sassc", "git"]
        for dep in required_deps:
            assert dep in all_packages, f"Missing dependency: {dep}"

    @patch.object(DesktopModule, "run")
    def test_install_nordic_theme_clones_repository(self, mock_run, module):
        """Test that Nordic theme installation clones Git repository."""
        mock_run.return_value = Mock(success=True)

        module._install_nordic_theme()

        # Verify git clone executed
        git_clone_calls = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]
        assert len(git_clone_calls) > 0, "Git clone not executed"

        # Verify correct repository
        assert any("EliverLara/Nordic.git" in call for call in git_clone_calls)

    @patch.object(DesktopModule, "run")
    def test_install_nordic_theme_moves_to_install_dir(self, mock_run, module):
        """Test that Nordic theme is moved to /usr/share/themes."""
        mock_run.return_value = Mock(success=True)

        module._install_nordic_theme()

        # Verify mv command executed
        mv_calls = [str(c) for c in mock_run.call_args_list if " mv " in str(c)]
        assert len(mv_calls) > 0, "Theme not moved to install directory"

        # Verify destination is correct
        assert any("/usr/share/themes/Nordic" in call for call in mv_calls)

    @patch.object(DesktopModule, "run")
    def test_install_nordic_theme_cleans_up_temp(self, mock_run, module):
        """Test that temporary directory is cleaned up after installation."""
        mock_run.return_value = Mock(success=True)

        module._install_nordic_theme()

        # Verify cleanup (rm -rf /tmp/nordic-theme)
        rm_calls = [str(c) for c in mock_run.call_args_list if "rm -rf" in str(c)]
        assert any(
            "/tmp/nordic" in call.lower() for call in rm_calls
        ), "Temporary directory not cleaned up"

    @patch.object(DesktopModule, "install_packages")
    def test_install_arc_theme_uses_apt(self, mock_install_pkg, module):
        """Test that Arc theme installs from APT repository."""
        module._install_arc_theme()

        # Verify apt package installed
        mock_install_pkg.assert_called_once()
        packages = mock_install_pkg.call_args[0][0]
        assert "arc-theme" in packages

    @patch.object(DesktopModule, "run")
    def test_install_whitesur_theme_runs_installer_script(self, mock_run, module):
        """Test that WhiteSur theme runs installer script."""
        mock_run.return_value = Mock(success=True, stdout="", stderr="")

        module._install_whitesur_theme()

        # Verify install.sh executed
        script_calls = [str(c) for c in mock_run.call_args_list if "install.sh" in str(c)]
        assert len(script_calls) > 0, "Installer script not executed"

    @patch.object(DesktopModule, "run")
    def test_install_whitesur_theme_fallback_on_script_failure(self, mock_run, module):
        """Test WhiteSur installation has fallback if script fails."""

        # Simulate script failure
        def run_side_effect(cmd, **kwargs):
            if "install.sh" in cmd:
                return Mock(success=False, stdout="", stderr="Script failed")
            return Mock(success=True, stdout="", stderr="")

        mock_run.side_effect = run_side_effect

        # Should not crash
        try:
            module._install_whitesur_theme()
            # Verify fallback attempted (manual copy) or warning logged
            assert mock_run.call_count > 1 or module.logger.warning.called
        except Exception as e:
            pytest.fail(f"Should have fallback for script failure: {e}")

    def test_install_themes_continues_on_individual_failure(self, module):
        """Test that one theme failure doesn't abort all installations."""
        with patch.object(module, "_install_nordic_theme") as mock_nordic:
            with patch.object(module, "_install_arc_theme") as mock_arc:
                # Nordic fails
                mock_nordic.side_effect = Exception("Nordic installation failed")

                # Arc should still be attempted
                module._install_themes()

                # Verify both were attempted
                assert mock_nordic.called
                assert mock_arc.called, "Arc installation should be attempted even if Nordic fails"

    def test_install_themes_registers_rollback_actions(self, module):
        """Test that rollback actions are registered for installed themes."""
        with patch.object(module, "run", return_value=Mock(success=True)):
            module._install_nordic_theme()

        # Verify rollback action registered
        assert module.rollback_manager.add_command.called

        # Check rollback command contains theme removal
        rollback_calls = [str(c) for c in module.rollback_manager.add_command.call_args_list]
        assert any("Nordic" in call for call in rollback_calls)


class TestIconPackInstallation:
    """Unit tests for icon pack installation."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"icons": {"install": ["papirus", "tela"], "active": "Papirus-Dark"}}}
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    @patch.object(DesktopModule, "install_packages")
    def test_install_papirus_icons_uses_apt(self, mock_install_pkg, module):
        """Test that Papirus icons install from APT."""
        module._install_papirus_icons()

        mock_install_pkg.assert_called_once()
        packages = mock_install_pkg.call_args[0][0]
        assert "papirus-icon-theme" in packages

    @patch.object(DesktopModule, "run")
    def test_install_tela_icons_clones_and_runs_installer(self, mock_run, module):
        """Test that Tela icons clone repo and run installer."""
        mock_run.return_value = Mock(success=True)

        module._install_tela_icons()

        # Verify git clone
        git_calls = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]
        assert len(git_calls) > 0
        assert any("Tela-icon-theme" in call for call in git_calls)

        # Verify installer executed
        script_calls = [str(c) for c in mock_run.call_args_list if "install.sh" in str(c)]
        assert len(script_calls) > 0

    @patch.object(DesktopModule, "install_packages")
    def test_install_numix_icons_uses_apt(self, mock_install_pkg, module):
        """Test that Numix icons install from APT."""
        module._install_numix_icons()

        mock_install_pkg.assert_called_once()
        packages = mock_install_pkg.call_args[0][0]
        assert "numix-icon-theme-circle" in packages


class TestFontConfiguration:
    """Unit tests for font configuration."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"fonts": {"default": "Roboto 10"}}}
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_configure_fonts_installs_packages(
        self, mock_write, mock_run, mock_install_pkg, module
    ):
        """Test that font packages are installed."""
        module._configure_fonts()

        # Verify font packages installed
        all_packages = []
        for call_obj in mock_install_pkg.call_args_list:
            all_packages.extend(call_obj[0][0])

        required_fonts = ["fonts-firacode", "fonts-noto", "fonts-roboto"]
        for font in required_fonts:
            assert font in all_packages, f"Missing font package: {font}"

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_configure_fonts_creates_fontconfig(
        self, mock_write, mock_run, mock_install_pkg, module
    ):
        """Test that fontconfig XML is created."""
        module._configure_fonts()

        # Verify write_file called for fontconfig
        fontconfig_calls = [
            c for c in mock_write.call_args_list if "/etc/fonts/local.conf" in str(c)
        ]
        assert len(fontconfig_calls) > 0, "Fontconfig not created"

        # Verify content
        fontconfig_content = fontconfig_calls[0][0][1]
        assert "<fontconfig>" in fontconfig_content
        assert '<?xml version="1.0"?>' in fontconfig_content

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_fontconfig_disables_subpixel_rendering(
        self, mock_write, mock_run, mock_install_pkg, module
    ):
        """CRITICAL: Test that fontconfig sets RGBA=none for RDP."""
        module._configure_fonts()

        # Get fontconfig content
        fontconfig_calls = [
            c for c in mock_write.call_args_list if "/etc/fonts/local.conf" in str(c)
        ]
        fontconfig_content = fontconfig_calls[0][0][1]

        # CRITICAL: Must contain RGBA=none
        assert "<const>none</const>" in fontconfig_content, "Fontconfig must set RGBA=none for RDP"
        assert 'name="rgba"' in fontconfig_content

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_fontconfig_enables_hinting(self, mock_write, mock_run, mock_install_pkg, module):
        """Test that fontconfig enables hinting."""
        module._configure_fonts()

        fontconfig_calls = [
            c for c in mock_write.call_args_list if "/etc/fonts/local.conf" in str(c)
        ]
        fontconfig_content = fontconfig_calls[0][0][1]

        # Should enable hinting with hintslight
        assert 'name="hinting"' in fontconfig_content
        assert "<bool>true</bool>" in fontconfig_content
        assert "<const>hintslight</const>" in fontconfig_content

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_configure_fonts_rebuilds_cache(self, mock_write, mock_run, mock_install_pkg, module):
        """Test that font cache is rebuilt after configuration."""
        module._configure_fonts()

        # Verify fc-cache executed
        fc_cache_calls = [str(c) for c in mock_run.call_args_list if "fc-cache" in str(c)]
        assert len(fc_cache_calls) > 0, "Font cache not rebuilt"

    @patch.object(DesktopModule, "install_packages")
    @patch.object(DesktopModule, "run")
    @patch("configurator.modules.desktop.write_file")
    def test_fontconfig_xml_is_valid(self, mock_write, mock_run, mock_install_pkg, module):
        """Test that generated fontconfig XML is syntactically valid."""
        module._configure_fonts()

        fontconfig_calls = [
            c for c in mock_write.call_args_list if "/etc/fonts/local.conf" in str(c)
        ]
        fontconfig_content = fontconfig_calls[0][0][1]

        # Parse XML
        try:
            root = ET.fromstring(fontconfig_content)
            assert root.tag == "fontconfig"
        except ET.ParseError as e:
            pytest.fail(f"Invalid fontconfig XML: {e}")


class TestPanelConfiguration:
    """Unit tests for panel and dock configuration."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"panel": {"layout": "macos", "enable_plank": True}}}
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    @patch.object(DesktopModule, "install_packages")
    def test_configure_panel_installs_plank(self, mock_install_pkg, module):
        """Test that Plank dock is installed."""
        with patch.object(module, "_setup_plank_autostart"):
            module._configure_panel_layout()

        # Verify Plank installed
        all_packages = []
        for call_obj in mock_install_pkg.call_args_list:
            all_packages.extend(call_obj[0][0])

        assert "plank" in all_packages

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_setup_plank_autostart_creates_desktop_file(self, mock_run, mock_pwd, module):
        """Test that Plank autostart file is created for users."""
        # Mock user
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]
        mock_pwd.getpwnam.return_value = mock_user

        module._setup_plank_autostart()

        # Verify desktop file created
        tee_calls = [str(c) for c in mock_run.call_args_list if "tee" in str(c)]
        assert any("plank.desktop" in call for call in tee_calls)
        assert any(".config/autostart" in call for call in tee_calls)


class TestThemeApplication:
    """Unit tests for theme and icon application."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "themes": {"active": "Nordic-darker"},
                "icons": {"active": "Papirus-Dark"},
            }
        }
        return DesktopModule(config=config, logger=Mock(), dry_run_manager=Mock())

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_apply_theme_and_icons_applies_to_all_users(self, mock_run, mock_pwd, module):
        """Test that theme and icons are applied for all users."""
        # Mock multiple users
        users = []
        for i in range(3):
            user = Mock()
            user.pw_name = f"user{i}"
            user.pw_uid = 1000 + i
            user.pw_dir = f"/home/user{i}"
            users.append(user)

        mock_pwd.getpwall.return_value = users
        mock_pwd.getpwnam.side_effect = lambda name: next(u for u in users if u.pw_name == name)

        module._apply_theme_and_icons()

        # Verify xfconf-query called for each user
        xfconf_calls = [str(c) for c in mock_run.call_args_list if "xfconf-query" in str(c)]

        # Should have at least 3 calls per user (GTK theme, icon theme, WM theme)
        assert len(xfconf_calls) >= 9  # 3 users × 3 settings

        # Verify all users mentioned
        all_commands = " ".join(xfconf_calls)
        for i in range(3):
            assert f"user{i}" in all_commands

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_apply_theme_sets_gtk_theme(self, mock_run, mock_pwd, module):
        """Test that GTK theme is applied via xfconf-query."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]
        mock_pwd.getpwnam.return_value = mock_user

        module._apply_theme_and_icons()

        # Verify GTK theme command
        xfconf_calls = [str(c) for c in mock_run.call_args_list if "xfconf-query" in str(c)]

        gtk_theme_calls = [c for c in xfconf_calls if "ThemeName" in c]
        assert len(gtk_theme_calls) > 0
        assert any("Nordic-darker" in c for c in gtk_theme_calls)

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_apply_theme_sets_icon_theme(self, mock_run, mock_pwd, module):
        """Test that icon theme is applied via xfconf-query."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]
        mock_pwd.getpwnam.return_value = mock_user

        module._apply_theme_and_icons()

        # Verify icon theme command
        xfconf_calls = [str(c) for c in mock_run.call_args_list if "xfconf-query" in str(c)]

        icon_theme_calls = [c for c in xfconf_calls if "IconThemeName" in c]
        assert len(icon_theme_calls) > 0
        assert any("Papirus-Dark" in c for c in icon_theme_calls)
