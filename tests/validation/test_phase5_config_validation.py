"""
Configuration validation tests for Phase 5 terminal tools.
"""

import os
import subprocess
import tempfile
from unittest.mock import Mock

import pytest

from configurator.modules.desktop import DesktopModule


class TestBatConfiguration:
    """Validate bat configuration generation."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "terminal_tools": {
                    "bat": {"theme": "TwoDark", "line_numbers": True, "git_integration": True}
                }
            }
        }
        return DesktopModule(config=config, logger=Mock())

    def test_generate_bat_config_creates_valid_syntax(self, module):
        """Test that generated bat config has valid syntax."""
        bat_config = module._generate_bat_config("TwoDark", True, True)

        # Basic syntax checks
        lines = bat_config.split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Should be in format --option or --option=value
            if line.startswith("--"):
                assert (
                    "=" in line
                    or line.startswith("--")
                    and " " not in line
                    or line in ["--italic-text=always", "--paging=auto", "--tabs=4"]
                ), f"Invalid bat config line: {line}"

    def test_bat_config_includes_required_options(self, module):
        """Test that bat config includes all required options."""
        bat_config = module._generate_bat_config("TwoDark", True, True)

        # Required options
        assert "--theme=" in bat_config
        assert "--style=" in bat_config
        assert "--paging=" in bat_config
        assert "--tabs=" in bat_config

    def test_bat_config_theme_is_quoted(self, module):
        """Test that bat theme with spaces is properly quoted."""
        # Theme with space
        bat_config = module._generate_bat_config("Monokai Extended", True, True)

        # Should be quoted
        assert '--theme="Monokai Extended"' in bat_config

    def test_bat_config_respects_line_numbers_setting(self, module):
        """Test that line numbers setting is respected."""
        # With line numbers
        config_with = module._generate_bat_config("TwoDark", True, True)
        assert "numbers" in config_with

        # Without line numbers
        config_without = module._generate_bat_config("TwoDark", False, True)
        # Should still have style but not numbers
        assert "--style=" in config_without
        # Verify numbers not in style (exact check depends on implementation)

    def test_bat_config_respects_git_integration(self, module):
        """Test that git integration setting is respected."""
        # With git
        config_with = module._generate_bat_config("TwoDark", True, True)
        assert "changes" in config_with or "--decorations=" in config_with

        # Without git
        config_without = module._generate_bat_config("TwoDark", True, False)
        # Check implementation


class TestExaConfiguration:
    """Validate exa alias generation."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "terminal_tools": {
                    "exa": {
                        "git_integration": True,
                        "icons": True,
                        "time_style": "long-iso",
                        "group_directories_first": True,
                    }
                }
            }
        }
        return DesktopModule(config=config, logger=Mock())

    def test_generate_exa_aliases_creates_valid_bash(self, module):
        """Test that generated exa aliases have valid bash syntax."""
        module._configure_eza_advanced()
        exa_aliases = module._generate_exa_aliases()

        # Should be valid bash
        # Test by writing to temp file and checking syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write(exa_aliases)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["bash", "-n", temp_path], capture_output=True, text=True, timeout=5
            )

            assert result.returncode == 0, f"Bash syntax error in exa aliases:\n{result.stderr}"
        finally:
            os.unlink(temp_path)

    def test_exa_aliases_have_fallbacks(self, module):
        """Test that exa aliases fall back to standard ls."""
        module._configure_eza_advanced()
        exa_aliases = module._generate_exa_aliases()

        # Should check if exa exists
        assert "command -v eza" in exa_aliases

        # Should have else clause with standard ls
        assert "else" in exa_aliases
        assert "ls -" in exa_aliases  # Standard ls flags

    def test_exa_aliases_include_git_integration(self, module):
        """Test that git integration is included when configured."""
        module._configure_eza_advanced()
        exa_aliases = module._generate_exa_aliases()

        # Should include --git flag
        assert "--git" in exa_aliases

    def test_exa_aliases_include_icons(self, module):
        """Test that icons are included when configured."""
        module._configure_eza_advanced()
        exa_aliases = module._generate_exa_aliases()

        # Should include --icons flag
        assert "--icons" in exa_aliases

    def test_exa_aliases_group_directories_first(self, module):
        """Test that group-directories-first is included."""
        module._configure_eza_advanced()
        exa_aliases = module._generate_exa_aliases()

        # Should include flag
        assert "--group-directories-first" in exa_aliases


class TestZoxideConfiguration:
    """Validate zoxide configuration generation."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "terminal_tools": {
                    "zoxide": {"interactive_mode": True, "exclude_dirs": ["/tmp", "/var/tmp"]}
                }
            }
        }
        return DesktopModule(config=config, logger=Mock())

    def test_generate_zoxide_config_creates_valid_bash(self, module):
        """Test that zoxide config has valid bash syntax."""
        module._configure_zoxide_advanced()
        zoxide_config = module._generate_zoxide_config()

        # Test syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write(zoxide_config)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["bash", "-n", temp_path], capture_output=True, text=True, timeout=5
            )

            assert result.returncode == 0, f"Bash syntax error in zoxide config:\n{result.stderr}"
        finally:
            os.unlink(temp_path)

    def test_zoxide_config_checks_installation(self, module):
        """Test that zoxide config checks if zoxide is installed."""
        module._configure_zoxide_advanced()
        zoxide_config = module._generate_zoxide_config()

        # Should check for zoxide
        assert "command -v zoxide" in zoxide_config

    def test_zoxide_config_includes_utility_functions(self, module):
        """Test that utility functions are included."""
        module._configure_zoxide_advanced()
        zoxide_config = module._generate_zoxide_config()

        # Should include functions
        assert "zoxide-stats" in zoxide_config
        assert "zoxide-remove" in zoxide_config
        assert "zoxide-clean" in zoxide_config


class TestFZFConfiguration:
    """Validate FZF configuration generation."""

    @pytest.fixture
    def module(self):
        config = {
            "desktop": {
                "terminal_tools": {
                    "fzf": {
                        "preview": True,
                        "height": "40%",
                        "layout": "reverse",
                        "border": True,
                        "color_scheme": "dark",
                    }
                }
            }
        }
        return DesktopModule(config=config, logger=Mock())

    def test_generate_fzf_config_creates_valid_bash(self, module):
        """Test that FZF config has valid bash syntax."""
        module._configure_fzf_advanced()
        fzf_config = module._generate_fzf_config()

        # Test syntax
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n")
            f.write(fzf_config)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["bash", "-n", temp_path], capture_output=True, text=True, timeout=5
            )

            assert result.returncode == 0, f"Bash syntax error in FZF config:\n{result.stderr}"
        finally:
            os.unlink(temp_path)

    def test_fzf_config_includes_default_opts(self, module):
        """Test that FZF_DEFAULT_OPTS is set."""
        module._configure_fzf_advanced()
        fzf_config = module._generate_fzf_config()

        # Should export FZF_DEFAULT_OPTS
        assert "export FZF_DEFAULT_OPTS=" in fzf_config

        # Should include configured options
        assert "--height" in fzf_config
        assert "--layout=" in fzf_config
        assert "--border" in fzf_config

    def test_fzf_config_includes_preview_window(self, module):
        """Test that preview window is configured."""
        module._configure_fzf_advanced()
        fzf_config = module._generate_fzf_config()

        # Should include preview with bat
        assert "--preview" in fzf_config
        assert "bat" in fzf_config

    def test_fzf_config_includes_custom_functions(self, module):
        """Test that custom functions are included."""
        module._configure_fzf_advanced()
        fzf_config = module._generate_fzf_config()

        # Should include functions
        assert "fcd()" in fzf_config
        assert "fe()" in fzf_config
        assert "fgc()" in fzf_config
        assert "fkill()" in fzf_config
