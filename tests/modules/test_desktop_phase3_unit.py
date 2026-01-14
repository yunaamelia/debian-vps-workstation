"""
Unit tests for Phase 3: Themes, Icons, and Fonts.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestThemeInstallation:
    """Test theme installation methods."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"themes": {"install": ["nordic", "arc"], "active": "Nordic-darker"}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch.object(DesktopModule, "run")
    def test_install_nordic_theme_clones_repository(self, mock_run, module):
        """Test that Nordic theme is cloned."""
        mock_run.return_value.success = True

        module._install_nordic_theme()

        # Check for clone command
        clone_found = False
        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if "git clone" in cmd and "Nordic" in cmd:
                clone_found = True
                break

        assert clone_found, "Git clone command not found for Nordic theme"

    @patch("os.path.exists")
    @patch.object(DesktopModule, "run")
    def test_install_nordic_theme_copies_variants(self, mock_run, mock_exists, module):
        """Test that theme variants are copied."""
        mock_run.return_value.success = True
        mock_exists.return_value = True  # ensure src directories exist

        module._install_nordic_theme()

        # Check for cp -r commands
        cp_found = False
        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if "cp -r" in cmd and "/usr/share/themes" in cmd:
                cp_found = True
                break

        assert cp_found, "Copy command not found for Nordic theme variants"

    @patch.object(DesktopModule, "install_packages")
    def test_install_arc_theme_uses_apt(self, mock_install, module):
        """Test Arc theme installation via APT."""
        mock_install.return_value = True

        module._install_arc_theme()

        assert mock_install.called
        args, _ = mock_install.call_args
        assert "arc-theme" in args[0]


class TestFontConfiguration:
    """Test font configuration."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "fonts": {
                    "rendering": {
                        "enabled": True,
                        "dpi": 96,
                        "hinting": "slight",
                        "antialias": True,
                    }
                }
            }
        }
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("os.makedirs")
    @patch("shutil.chown")
    @patch.object(DesktopModule, "write_file")
    def test_configure_fonts_creates_xml(
        self, mock_write, mock_chown, mock_makedirs, mock_getpwall, module
    ):
        """Test that fonts.conf XML is created."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwall.return_value = [mock_user]

        module.dry_run = False
        module._configure_fonts()

        # Verify write_file called
        assert mock_write.called
        args, _ = mock_write.call_args
        content = args[1]

        assert "<fontconfig>" in content
        assert "<bool>true</bool>" in content  # antialias check
        assert "<double>96</double>" in content  # DPI check


class TestThemeApplication:
    """Test applying themes to users."""

    @pytest.fixture
    def module(self):
        return DesktopModule(config={}, logger=Mock(), rollback_manager=Mock())

    @patch("pwd.getpwall")
    @patch("os.makedirs")
    @patch("shutil.chown")
    @patch.object(DesktopModule, "write_file")
    def test_apply_theme_to_users_writes_xsettings(
        self, mock_write, mock_chown, mock_makedirs, mock_getpwall, module
    ):
        """Test that xsettings.xml is written for users."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"
        mock_getpwall.return_value = [mock_user]

        module.dry_run = False
        module._apply_theme_to_users("Nordic-darker")

        assert mock_write.called
        args, _ = mock_write.call_args
        path = args[0]
        content = args[1]

        assert "xsettings.xml" in path
        assert 'value="Nordic-darker"' in content
        assert 'property name="ThemeName"' in content

    @patch.object(DesktopModule, "_apply_theme_to_users")
    def test_apply_icons_delegates_to_theme_applier(self, mock_apply, module):
        """Test _apply_icons_to_users calls _apply_theme_to_users."""
        module._apply_icons_to_users("Papirus")
        assert mock_apply.called
