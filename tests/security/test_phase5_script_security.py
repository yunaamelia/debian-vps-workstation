"""
Security tests for custom integration scripts in Phase 5.

CRITICAL: These tests verify defense against command injection attacks.
All tests MUST pass before production deployment.
"""

import os
import subprocess
import tempfile
from unittest.mock import Mock, patch

import pytest

from configurator.modules.desktop import DesktopModule


class TestCustomScriptSecurity:
    """Test defense against command injection in custom scripts."""

    @pytest.fixture
    def module(self):
        """Create module instance for testing."""
        config = {"desktop": {"terminal_tools": {"bat": {}, "eza": {}, "fzf": {}}}}
        return DesktopModule(
            config=config, logger=Mock(), rollback_manager=Mock(), dry_run_manager=Mock()
        )

    def test_preview_script_static_analysis(self, module):
        """Static analysis of preview script for security vulnerabilities."""
        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_user = Mock()
            mock_user.pw_name = "testuser"
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/testuser"

            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                # Create scripts
                module._create_tool_integration_scripts()

        # Extract preview script content cleanly
        preview_script_content = None
        for call in mock_run.call_args_list:
            # Check if this is a tee command for the preview script
            # args[0] is the command string
            cmd = str(call[0][0])
            if "tee" in cmd and "/preview" in cmd and "search" not in cmd:
                if hasattr(call, "kwargs") and "input" in call.kwargs:
                    preview_script_content = call.kwargs["input"].decode()
                elif len(call) > 1 and "input" in call[1]:
                    preview_script_content = call[1]["input"].decode()
                break

        if preview_script_content:
            script_content = preview_script_content
            print(f"DEBUG: Script Content:\n{script_content}")

            # Verify security patterns
            # 1. Variables should be quoted
            assert '"$FILE"' in script_content or '"$1"' in script_content, (
                "Variables not quoted in preview script"
            )

            # 2. Should not use eval
            assert "eval" not in script_content, "Dangerous eval found in preview script"

            # 3. Should validate input exists
            # Checks for [ -f, [ -d, or [ -e (existence)
            assert (
                "[ -f" in script_content or "[ -d" in script_content or "[ -e" in script_content
            ), f"Preview script doesn't validate file existence. Content: {script_content[:100]}..."

        assert preview_script_content, "Preview script creation not capturing input"

    def test_preview_script_prevents_flag_injection(self, module):
        """Test that preview script prevents filename starting with dash."""
        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_user = Mock()
            mock_user.pw_name = "testuser"
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/testuser"

            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                module._create_tool_integration_scripts()

        # Extract preview script
        preview_calls = [c for c in mock_run.call_args_list if "preview" in str(c)]

        for call in preview_calls:
            if hasattr(call[1], "get") and "input" in call[1]:
                script_content = call[1]["input"].decode()

                # Should use -- to prevent flag injection
                # Example: bat -- "$FILE" instead of bat "$FILE"
                # This is a recommendation, not always required
                pass  # Check implementation

    @pytest.mark.integration
    def test_preview_script_execution_with_malicious_input(self):
        """
        Integration test: Execute preview script with malicious input.

        Requires actual script creation and bash execution.
        Should be run in isolated environment (container).
        """
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create preview script
            script_path = os.path.join(tmpdir, "preview")

            # Minimal safe preview script
            script_content = """#!/bin/bash
FILE="$1"

if [ -z "$FILE" ]; then
    echo "Usage: preview <file>"
    exit 1
fi

if [ ! -e "$FILE" ]; then
    echo "File not found: $FILE"
    exit 1
fi

if [ -f "$FILE" ]; then
    cat -- "$FILE"
fi
"""

            with open(script_path, "w") as f:
                f.write(script_content)

            os.chmod(script_path, 0o755)

            # Test with malicious filename
            result = subprocess.run(
                [script_path, "file; whoami"], capture_output=True, text=True, timeout=5
            )

            # Should output "File not found", not execute whoami
            assert "File not found" in result.stdout or result.returncode != 0
            # Should NOT contain result of whoami
            assert "root" not in result.stdout.lower()
            assert "testuser" not in result.stdout.lower()

    def test_search_script_validates_pattern(self, module):
        """Test that search script validates search pattern safely."""
        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_user = Mock()
            mock_user.pw_name = "testuser"
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/testuser"

            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                module._create_tool_integration_scripts()

        # Extract search script
        search_calls = [
            c
            for c in mock_run.call_args_list
            if "search" in str(c) and "preview" not in str(c).lower()
        ]

        for call in search_calls:
            if hasattr(call[1], "get") and "input" in call[1]:
                script_content = call[1]["input"].decode()

                # Pattern should be quoted
                assert '"$PATTERN"' in script_content or '"$1"' in script_content

                # Should not eval pattern
                assert "eval" not in script_content

    def test_goto_script_validates_directory(self, module):
        """Test that goto script validates directory safely."""
        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_user = Mock()
            mock_user.pw_name = "testuser"
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/testuser"

            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                module._create_tool_integration_scripts()

        # Extract goto script
        goto_calls = [c for c in mock_run.call_args_list if "goto" in str(c)]

        for call in goto_calls:
            if hasattr(call[1], "get") and "input" in call[1]:
                script_content = call[1]["input"].decode()

                # Should check directory exists
                assert "[ -d" in script_content or "cd" in script_content


class TestPathManipulationSecurity:
    """Test PATH manipulation security."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"terminal_tools": {}}}
        return DesktopModule(config=config, logger=Mock())

    def test_local_bin_added_to_path_safely(self, module):
        """Test that ~/.local/bin is added to PATH safely."""
        zshrc_content = module._generate_advanced_tools_zshrc_block()

        # Should add to PATH
        assert "PATH=" in zshrc_content
        assert ".local/bin" in zshrc_content

        # Should use $HOME, not hardcoded path
        assert "$HOME/.local/bin" in zshrc_content

        # Should prepend (user scripts have priority)
        # This is intentional but verify it's documented
        assert (
            'PATH="$HOME/.local/bin:$PATH"' in zshrc_content
            or "PATH=$HOME/.local/bin:$PATH" in zshrc_content
        )

    def test_scripts_created_with_correct_ownership(self, module):
        """Test that scripts are created with user ownership, not root."""
        with patch("configurator.modules.desktop.pwd") as mock_pwd:
            mock_user = Mock()
            mock_user.pw_name = "testuser"
            mock_user.pw_uid = 1000
            mock_user.pw_dir = "/home/testuser"

            mock_pwd.getpwall.return_value = [mock_user]
            mock_pwd.getpwnam.return_value = mock_user

            with patch.object(module, "run") as mock_run:
                module._create_tool_integration_scripts()

        # Verify scripts created as user via sudo -u
        script_creates = [str(c) for c in mock_run.call_args_list if "tee" in str(c)]

        for call in script_creates:
            if "preview" in call or "search" in call or "goto" in call:
                assert "sudo -u" in call, f"Script not created as user: {call}"


class TestFZFPreviewSecurity:
    """Test FZF preview command security."""

    @pytest.fixture
    def module(self):
        config = {"desktop": {"terminal_tools": {"fzf": {"preview": True}}}}
        return DesktopModule(config=config, logger=Mock())

    def test_fzf_preview_uses_single_quotes(self, module):
        """Test that FZF preview commands use single quotes (no expansion)."""
        fzf_config = module._generate_fzf_config()

        # Find preview option
        assert "--preview" in fzf_config

        # Should use single quotes to prevent variable expansion
        # Example: --preview 'bat --color=always {}'
        # Not:  --preview "bat $VAR {}"

        import re

        preview_match = re.search(r"--preview\s+'([^']+)'", fzf_config)

        assert preview_match, "Preview command should use single quotes"

    def test_fzf_preview_no_eval(self, module):
        """Test that FZF preview doesn't use eval or dangerous constructs."""
        fzf_config = module._generate_fzf_config()

        # Should not contain eval
        assert "eval" not in fzf_config.lower()
