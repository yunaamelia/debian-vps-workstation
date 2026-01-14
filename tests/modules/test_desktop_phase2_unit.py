"""
Unit tests for Phase 2 compositor and Polkit functionality.
"""

from unittest.mock import Mock, mock_open, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestCompositorConfiguration:
    """Unit tests for XFCE compositor optimization."""

    @pytest.fixture
    def module(self):
        config = {
            "compositor": {"mode": "disabled"},
            "polkit": {"allow_colord": True},
        }
        dry_run_manager = Mock()
        dry_run_manager.is_enabled = False
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=dry_run_manager,
        )

    def test_generate_xfwm4_config_disabled_mode(self, module):
        """Test XML generation for disabled mode."""
        xml = module._generate_xfwm4_config("disabled")

        assert '<property name="use_compositing" type="bool" value="false"/>' in xml
        assert '<property name="show_frame_shadow" type="bool" value="false"/>' in xml
        assert '<property name="show_popup_shadow" type="bool" value="false"/>' in xml
        assert 'value="100"' in xml  # Opacity

    def test_generate_xfwm4_config_optimized_mode(self, module):
        """Test XML generation for optimized mode."""
        xml = module._generate_xfwm4_config("optimized")

        assert '<property name="use_compositing" type="bool" value="true"/>' in xml
        assert '<property name="vblank_mode" type="string" value="off"/>' in xml
        assert '<property name="zoom_desktop" type="bool" value="false"/>' in xml
        assert '<property name="show_frame_shadow" type="bool" value="false"/>' in xml

    def test_generate_xfwm4_config_enabled_mode(self, module):
        """Test XML generation for enabled mode."""
        xml = module._generate_xfwm4_config("enabled")

        assert '<property name="use_compositing" type="bool" value="true"/>' in xml
        assert '<property name="vblank_mode" type="string" value="auto"/>' in xml
        assert '<property name="zoom_desktop" type="bool" value="true"/>' in xml
        assert '<property name="show_frame_shadow" type="bool" value="true"/>' in xml

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_optimize_xfce_compositor_processes_all_users(
        self, mock_run, mock_pwd, mock_write, module
    ):
        """Test that compositor config is created for all regular users."""
        # Mock multiple users
        users = []
        for i in range(3):
            mock_user = Mock()
            mock_user.pw_name = f"user{i}"
            mock_user.pw_uid = 1000 + i
            mock_user.pw_dir = f"/home/user{i}"
            users.append(mock_user)

        mock_pwd.getpwall.return_value = users
        mock_pwd.getpwnam.side_effect = lambda name: next(u for u in users if u.pw_name == name)

        with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
            with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
                module._optimize_xfce_compositor()

        # Verify config created for each user
        # Verify config created for each user
        # Should call write_file
        assert mock_write.call_count >= 3

        # Verify all usernames appear in commands
        all_writes = " ".join(str(c) for c in mock_write.call_args_list)
        for i in range(3):
            assert f"user{i}" in all_writes

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_compositor_handles_no_users_gracefully(self, mock_run, mock_pwd, module):
        """Test behavior when no regular users exist."""
        # Only system users (UID < 1000)
        mock_system = Mock()
        mock_system.pw_name = "daemon"
        mock_system.pw_uid = 1

        mock_pwd.getpwall.return_value = [mock_system]

        # Should return without error
        module._optimize_xfce_compositor()

        # No file operations should occur
        assert mock_run.call_count == 0

    def test_validate_compositor_mode_accepts_valid_modes(self, module):
        """Test that valid compositor modes are accepted."""
        assert module._validate_compositor_mode("disabled") == "disabled"
        assert module._validate_compositor_mode("optimized") == "optimized"
        assert module._validate_compositor_mode("enabled") == "enabled"

    def test_validate_compositor_mode_rejects_invalid_modes(self, module):
        """Test that invalid compositor modes default to 'disabled'."""
        assert module._validate_compositor_mode("invalid") == "disabled"
        assert module._validate_compositor_mode("turbo") == "disabled"
        assert module._validate_compositor_mode("") == "disabled"

    @patch("configurator.modules.desktop.pwd")
    @patch.object(DesktopModule, "run")
    def test_compositor_skips_user_with_invalid_home(self, mock_run, mock_pwd, module):
        """Test that users with non-existent home directories are skipped."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/nonexistent/home"

        mock_pwd.getpwall.return_value = [mock_user]
        mock_pwd.getpwnam.return_value = mock_user

        with patch("configurator.modules.desktop.os.path.isabs", return_value=True):
            with patch("configurator.modules.desktop.os.path.isdir", return_value=False):
                # Should log warning and skip
                module._optimize_xfce_compositor()

        # Verify warning logged
        assert module.logger.warning.called
        warning_msg = str(module.logger.warning.call_args)
        assert (
            "doesn't exist" in warning_msg.lower()
            or "not found" in warning_msg.lower()
            or "skipping" in warning_msg.lower()
        )


class TestPolkitConfiguration:
    """Unit tests for Polkit rules configuration."""

    @pytest.fixture
    def module(self):
        config = {"polkit": {"allow_colord": True, "allow_packagekit": True}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    @patch.object(DesktopModule, "run")
    def test_configure_polkit_creates_both_rules(self, mock_run, mock_isdir, mock_write, module):
        """Test that both Polkit rules are created."""
        module._configure_polkit_rules()

        # Verify both files written
        assert mock_write.call_count == 2

        written_paths = [call[0][0] for call in mock_write.call_args_list]
        assert any("colord" in path for path in written_paths)
        assert any("packagekit" in path for path in written_paths)

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    @patch.object(DesktopModule, "run")
    def test_polkit_rules_have_correct_format(self, mock_run, mock_isdir, mock_write, module):
        """Test that Polkit rules use correct .pkla format."""
        module._configure_polkit_rules()

        for call_item in mock_write.call_args_list:
            content = call_item[0][1]

            # Verify INI-style format
            assert "[" in content and "]" in content
            assert "Identity=" in content
            assert "Action=" in content
            assert "ResultAny=" in content
            assert "ResultInactive=" in content
            assert "ResultActive=" in content

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.makedirs")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=False)
    @patch.object(DesktopModule, "run")
    def test_polkit_creates_directory_if_missing(
        self, mock_run, mock_isdir, mock_makedirs, mock_write, module
    ):
        """Test that Polkit directory is created if it doesn't exist."""
        module._configure_polkit_rules()

        # Verify makedirs was called
        assert mock_makedirs.called
        assert "polkit-1" in mock_makedirs.call_args[0][0]

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    @patch.object(DesktopModule, "run")
    def test_polkit_respects_config_flags(self, mock_run, mock_isdir, mock_write, module):
        """Test that Polkit rules respect configuration flags."""
        # Disable packagekit rule
        module.config["polkit"]["allow_packagekit"] = False

        module._configure_polkit_rules()

        # Should only write colord rule
        written_paths = [call_item[0][0] for call_item in mock_write.call_args_list]
        assert any("colord" in path for path in written_paths)
        assert not any("packagekit" in path for path in written_paths)

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    @patch.object(DesktopModule, "run")
    def test_polkit_restarts_service(self, mock_run, mock_isdir, mock_write, module):
        """Test that Polkit service is restarted after configuration."""
        module._configure_polkit_rules()

        # Verify systemctl restart was called
        restart_calls = [
            str(c) for c in mock_run.call_args_list if "systemctl" in str(c) and "restart" in str(c)
        ]
        assert len(restart_calls) >= 1
        assert "polkit" in restart_calls[0]


class TestVerificationMethods:
    """Unit tests for verification logic."""

    @pytest.fixture
    def module(self):
        config = {"compositor": {"mode": "disabled"}}
        return DesktopModule(config=config, logger=Mock())

    @patch("configurator.modules.desktop.pwd")
    @patch("configurator.modules.desktop.os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='<property name="use_compositing" type="bool" value="false"/>',
    )
    def test_verify_compositor_config_checks_all_users(
        self, mock_file, mock_exists, mock_pwd, module
    ):
        """Test that verification checks compositor config for all users."""
        # Mock users
        users = []
        for i in range(2):
            mock_user = Mock()
            mock_user.pw_name = f"user{i}"
            mock_user.pw_uid = 1000 + i
            mock_user.pw_dir = f"/home/user{i}"
            users.append(mock_user)

        mock_pwd.getpwall.return_value = users
        mock_pwd.getpwnam.side_effect = lambda name: next(u for u in users if u.pw_name == name)

        # Execute verification
        result = module._verify_compositor_config("disabled")

        # Verify all user configs were checked
        assert mock_file.call_count >= 2  # One per user

    @patch("configurator.modules.desktop.os.path.exists")
    def test_verify_polkit_rules_checks_file_existence(self, mock_exists, module):
        """Test that Polkit verification checks if rule files exist."""
        mock_exists.side_effect = lambda path: "colord" in path

        with patch.object(module, "run", return_value=Mock(success=True)):
            result = module._verify_polkit_rules()

        # Verify checks for both files
        checked_paths = [call_item[0][0] for call_item in mock_exists.call_args_list]
        assert any("colord" in path for path in checked_paths)
        assert any("packagekit" in path for path in checked_paths)


class TestDryRunMode:
    """Test dry-run mode compliance."""

    @pytest.fixture
    def module(self):
        config = {"compositor": {"mode": "disabled"}}
        module = DesktopModule(config=config, logger=Mock(), dry_run_manager=Mock())
        module.dry_run = True
        return module

    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    @patch("configurator.modules.desktop.pwd")
    def test_compositor_dry_run_no_file_writes(self, mock_pwd, mock_isdir, module):
        """Test that dry-run mode doesn't write files."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        mock_pwd.getpwall.return_value = [mock_user]

        with patch.object(module, "run") as mock_run:
            module._optimize_xfce_compositor()

        # No actual commands should be executed
        assert mock_run.call_count == 0

        # Dry-run manager should record action
        assert module.dry_run_manager.record_file_write.called

    @patch("configurator.utils.file.write_file")
    @patch("configurator.modules.desktop.os.path.isdir", return_value=True)
    def test_polkit_dry_run_no_file_writes(self, mock_isdir, mock_write, module):
        """Test that Polkit dry-run doesn't write files."""
        with patch.object(module, "run") as mock_run:
            result = module._configure_polkit_rules()

        # No actual writes should occur
        assert mock_write.call_count == 0
        assert mock_run.call_count == 0
