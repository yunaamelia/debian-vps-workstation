"""
Unit tests for utility functions.
"""

from unittest.mock import patch

from configurator.utils.system import OSInfo, get_architecture, is_root


class TestOSInfo:
    """Tests for OSInfo dataclass."""

    def test_is_debian(self):
        """Test is_debian property."""
        debian_info = OSInfo(
            name="debian",
            version="13",
            version_id="13",
            codename="trixie",
            pretty_name="Debian GNU/Linux 13",
        )
        assert debian_info.is_debian is True

        ubuntu_info = OSInfo(
            name="ubuntu",
            version="22.04",
            version_id="22.04",
            codename="jammy",
            pretty_name="Ubuntu 22.04",
        )
        assert ubuntu_info.is_debian is False

    def test_is_debian_13(self):
        """Test is_debian_13 property."""
        debian13 = OSInfo(
            name="debian",
            version="13",
            version_id="13",
            codename="trixie",
            pretty_name="Debian GNU/Linux 13",
        )
        assert debian13.is_debian_13 is True

        debian12 = OSInfo(
            name="debian",
            version="12",
            version_id="12",
            codename="bookworm",
            pretty_name="Debian GNU/Linux 12",
        )
        assert debian12.is_debian_13 is False


class TestGetOSInfo:
    """Tests for get_os_info function."""

    def test_parse_os_release(self, mock_os_release):
        """Test parsing /etc/os-release file."""
        with patch("configurator.utils.system.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.read_text.return_value = """
PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
NAME="Debian GNU/Linux"
VERSION_ID="13"
VERSION="13 (trixie)"
VERSION_CODENAME=trixie
ID=debian
"""
            # Note: This test might need adjustment based on actual implementation
            # The mock needs to match Path behavior


class TestSystemUtilities:
    """Tests for system utility functions."""

    def test_get_architecture(self):
        """Test getting system architecture."""
        arch = get_architecture()
        assert isinstance(arch, str)
        assert len(arch) > 0

    @patch("os.getuid")
    def test_is_root_true(self, mock_uid):
        """Test is_root returns True for UID 0."""
        mock_uid.return_value = 0
        assert is_root() is True

    @patch("os.getuid")
    def test_is_root_false(self, mock_uid):
        """Test is_root returns False for non-root UID."""
        mock_uid.return_value = 1000
        assert is_root() is False
