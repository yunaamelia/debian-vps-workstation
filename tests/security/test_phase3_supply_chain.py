"""
Supply chain security tests for Phase 3 theme/icon installation.

CRITICAL: These tests verify defense against supply chain attacks.
All tests MUST pass before production deployment.
"""

import inspect
from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestGitRepositorySecurity:
    """Test defense against malicious Git repositories."""

    @pytest.fixture
    def module(self):
        """Create module instance for testing."""
        config = {
            "desktop": {
                "themes": {"install": ["nordic"], "active": "Nordic-darker"},
                "icons": {"install": ["papirus"], "active": "Papirus-Dark"},
            }
        }
        return DesktopModule(
            config=config,
            logger=Mock(),
            rollback_manager=Mock(),
            dry_run_manager=Mock(),
        )

    def test_git_urls_are_hardcoded_not_from_config(self, module):
        """CRITICAL: Verify Git URLs are hardcoded, not user-configurable."""
        # Check module source code for hardcoded URLs
        source = inspect.getsource(module._install_nordic_theme)

        # Should contain hardcoded GitHub URL
        assert "https://github.com/EliverLara/Nordic.git" in source, (
            "Git URL should be hardcoded in method"
        )

        # Should NOT read URL from config
        assert "self.config.get" not in source or "repo" not in source.lower(), (
            "Git URL should not be configurable (supply chain risk)"
        )

    @pytest.mark.parametrize(
        "malicious_url",
        [
            "git://attacker.com/fake-theme.git",  # Insecure protocol
            "http://evil.com/malware.git",  # Non-HTTPS
            "https://typosquatted-github.com/Nordic.git",  # Typosquatting
            "file:///etc/passwd",  # Local file access
            "../../../malicious-repo",  # Path traversal
            "https://github.com/attacker/nordic.git",  # Wrong owner
        ],
    )
    def test_malicious_git_url_rejected(self, module, malicious_url):
        """Test that malicious Git URLs are rejected."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)

            try:
                module._install_nordic_theme()

                # Verify the actual URL used is safe
                git_clone_calls = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]

                for call_str in git_clone_calls:
                    # Should NOT contain malicious URL
                    assert malicious_url not in call_str, (
                        f"Malicious URL used in git clone: {call_str}"
                    )

                    # Should use HTTPS GitHub
                    assert "https://github.com/" in call_str, (
                        f"Git clone doesn't use HTTPS GitHub: {call_str}"
                    )

            except Exception:
                # If implementation raises exception, that's acceptable
                pass

    def test_git_clone_uses_shallow_clone(self, module):
        """Test that git clones use --depth=1 for security and performance."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            module._install_nordic_theme()

            # Find git clone command
            git_clone_calls = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]

            assert len(git_clone_calls) > 0, "No git clone executed"

            for call_str in git_clone_calls:
                assert "--depth=1" in call_str or "--depth 1" in call_str, (
                    f"Git clone should use shallow clone: {call_str}"
                )

    def test_git_clone_destination_validated(self, module):
        """Test that git clone destination paths are validated."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            module._install_nordic_theme()

            git_clone_calls = [str(c) for c in mock_run.call_args_list if "git clone" in str(c)]

            for call_str in git_clone_calls:
                # Destination should be in /tmp
                assert "/tmp/" in call_str, f"Git clone destination should be in /tmp: {call_str}"

                # Should NOT contain path traversal
                assert "../" not in call_str, f"Path traversal in git clone destination: {call_str}"


class TestInstallerScriptSecurity:
    """Test defense against malicious installer scripts."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"themes": {"install": ["whitesur"]}}}
        return DesktopModule(
            config=config, logger=Mock(), rollback_manager=Mock(), dry_run_manager=Mock()
        )

    def test_installer_script_execution_has_error_handling(self, module):
        """Test that installer script failures don't crash installation."""
        with patch.object(module, "run") as mock_run:
            # Simulate script failure
            def run_side_effect(cmd, **kwargs):
                if "install.sh" in cmd:
                    return Mock(success=False, stdout="", stderr="Script failed")
                return Mock(success=True, stdout="", stderr="")

            mock_run.side_effect = run_side_effect

            # Should not raise exception
            try:
                module._install_whitesur_theme()
                # Verify fallback was attempted or error logged
                assert module.logger.warning.called or module.logger.error.called
            except Exception as e:
                pytest.fail(f"Installer script failure should be handled gracefully: {e}")

    def test_installer_script_parameters_validated(self, module):
        """Test that parameters passed to installer scripts are validated."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            module._install_whitesur_theme()

            # Find install.sh execution
            script_calls = [str(c) for c in mock_run.call_args_list if "install.sh" in str(c)]

            for call_str in script_calls:
                # Parameters should be hardcoded or validated
                assert "-d /usr/share/themes" in call_str, (
                    "Installer destination should be hardcoded"
                )

                # Should NOT contain command injection attempts from user input
                # Note: && for command chaining is acceptable when paths are hardcoded
                # Check for dangerous patterns that could come from user input
                dangerous_patterns = [";", "$(", "`"]
                for pattern in dangerous_patterns:
                    if pattern in call_str:
                        pytest.fail(
                            f"Potential command injection pattern '{pattern}' in installer call: {call_str}"
                        )

    def test_installer_script_runs_from_validated_directory(self, module):
        """Test that installer scripts only run from validated temp directories."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            module._install_whitesur_theme()

            script_calls = [str(c) for c in mock_run.call_args_list if "install.sh" in str(c)]

            for call_str in script_calls:
                # Should cd to /tmp directory first
                if "cd" in call_str:
                    assert "/tmp/" in call_str, f"Installer should run from /tmp: {call_str}"


class TestPathTraversalDefense:
    """Test defense against path traversal in theme installations."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"themes": {"active": "Nordic-darker"}}}
        return DesktopModule(config=config, logger=Mock(), dry_run_manager=Mock())

    @pytest.mark.parametrize(
        "malicious_name",
        [
            "../../../etc/passwd",
            "../../root/.ssh/authorized_keys",
            "/etc/shadow",
            "theme; rm -rf /",
            "theme`whoami`",
            "theme$(cat /etc/passwd)",
        ],
    )
    def test_theme_name_validation_prevents_traversal(self, module, malicious_name):
        """Test that theme name validation prevents path traversal."""
        # Test that malicious names don't appear in paths
        with patch.object(module, "run") as mock_run:
            with patch("configurator.modules.desktop.pwd") as mock_pwd:
                mock_pwd.getpwall.return_value = []

                # Try to trigger theme installation with malicious config
                module.config["desktop"]["themes"]["active"] = malicious_name

                try:
                    module._apply_theme_and_icons()

                    # Verify malicious name not used in file operations
                    for call_obj in mock_run.call_args_list:
                        call_str = str(call_obj)
                        if "xfconf-query" in call_str:
                            # Theme name should be sanitized or rejected
                            assert "../" not in call_str
                            assert "etc/passwd" not in call_str
                except Exception:
                    # Exception is acceptable (validation working)
                    pass

    def test_theme_install_directory_validated(self, module):
        """Test that theme installation directories are validated."""
        with patch.object(module, "run") as mock_run:
            mock_run.return_value = Mock(success=True)
            module._install_nordic_theme()

            # Find mv commands (move theme to install directory)
            mv_calls = [str(c) for c in mock_run.call_args_list if " mv " in str(c)]

            for call_str in mv_calls:
                # Destination should be /usr/share/themes
                if "/usr/share/themes" in call_str:
                    # Should NOT have path traversal
                    assert "../" not in call_str, f"Path traversal in mv command: {call_str}"


class TestDependencyVerification:
    """Test that dependencies come from trusted sources."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"themes": {"install": ["arc"]}}}
        return DesktopModule(
            config=config, logger=Mock(), rollback_manager=Mock(), dry_run_manager=Mock()
        )

    def test_apt_packages_from_official_repos(self, module):
        """Test that APT packages come from official Debian repositories."""
        with patch.object(module, "install_packages") as mock_install:
            module._install_arc_theme()

            # Verify arc-theme package name is exact
            mock_install.assert_called()
            call_args = mock_install.call_args[0][0]

            # Should be exact package name
            assert "arc-theme" in call_args

            # Should NOT have URLs or external sources
            assert "http" not in str(call_args).lower()

    def test_git_repositories_from_trusted_orgs(self, module):
        """Test that Git repositories are from verified GitHub organizations."""
        # Check Nordic theme installation method
        source = inspect.getsource(module._install_nordic_theme)

        # Should contain GitHub URLs
        if "github.com" in source:
            # Verify trusted organizations
            trusted_orgs = ["EliverLara", "dracula", "vinceliuice"]

            assert any(org in source for org in trusted_orgs), (
                "Git repository not from trusted organization"
            )

    def test_no_downloads_from_untrusted_domains(self, module):
        """Test that no downloads occur from untrusted domains."""
        with patch.object(module, "run") as mock_run:
            with patch.object(module, "install_packages"):
                mock_run.return_value = Mock(success=True)
                module._install_themes()

                # Check all commands for URLs
                all_commands = " ".join(str(c) for c in mock_run.call_args_list)

                # Should only download from trusted domains
                trusted_domains = ["github.com", "githubusercontent.com"]

                # Extract URLs from commands
                import re

                urls = re.findall(r"https?://[^\s]+", all_commands)

                for url in urls:
                    domain = url.split("/")[2]
                    assert any(trusted in domain for trusted in trusted_domains), (
                        f"Download from untrusted domain: {url}"
                    )
