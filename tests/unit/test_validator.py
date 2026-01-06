"""
Unit tests for the SystemValidator class.
"""

from unittest.mock import MagicMock, patch

from configurator.core.validator import SystemValidator, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_str_passed_required(self):
        """Test string representation for passed required check."""
        result = ValidationResult(
            name="Test",
            passed=True,
            message="All good",
            required=True,
        )
        assert "✓" in str(result)
        assert "Test" in str(result)

    def test_str_failed_required(self):
        """Test string representation for failed required check."""
        result = ValidationResult(
            name="Test",
            passed=False,
            message="Failed",
            required=True,
        )
        assert "✗" in str(result)
        assert "(required)" in str(result)


class TestSystemValidator:
    """Tests for SystemValidator."""

    def test_validator_creation(self, mock_logger):
        """Test validator can be created."""
        validator = SystemValidator(logger=mock_logger)
        assert validator is not None

    @patch("configurator.core.validator.get_os_info")
    def test_debian_13_passes(self, mock_os_info, mock_logger):
        """Test that Debian 13 passes OS validation."""
        mock_os_info.return_value = MagicMock(
            is_debian=True,
            is_debian_13=True,
            pretty_name="Debian GNU/Linux 13 (trixie)",
        )

        validator = SystemValidator(logger=mock_logger)
        validator._check_os()

        assert len(validator.results) == 1
        assert validator.results[0].passed is True

    @patch("configurator.core.validator.get_os_info")
    def test_non_debian_fails(self, mock_os_info, mock_logger):
        """Test that non-Debian system fails OS validation."""
        mock_os_info.return_value = MagicMock(
            is_debian=False,
            is_debian_13=False,
            pretty_name="Ubuntu 22.04",
        )

        validator = SystemValidator(logger=mock_logger)
        validator._check_os()

        assert len(validator.results) == 1
        assert validator.results[0].passed is False

    @patch("configurator.core.validator.get_architecture")
    def test_x86_64_passes(self, mock_arch, mock_logger):
        """Test that x86_64 architecture passes."""
        mock_arch.return_value = "x86_64"

        validator = SystemValidator(logger=mock_logger)
        validator._check_architecture()

        assert len(validator.results) == 1
        assert validator.results[0].passed is True

    @patch("configurator.core.validator.is_root")
    def test_root_passes(self, mock_root, mock_logger):
        """Test that running as root passes."""
        mock_root.return_value = True

        validator = SystemValidator(logger=mock_logger)
        validator._check_root_access()

        assert len(validator.results) == 1
        assert validator.results[0].passed is True

    @patch("configurator.core.validator.is_root")
    def test_non_root_fails(self, mock_root, mock_logger):
        """Test that running as non-root fails."""
        mock_root.return_value = False

        validator = SystemValidator(logger=mock_logger)
        validator._check_root_access()

        assert len(validator.results) == 1
        assert validator.results[0].passed is False

    @patch("configurator.core.validator.get_ram_gb")
    def test_sufficient_ram_passes(self, mock_ram, mock_logger):
        """Test that sufficient RAM passes."""
        mock_ram.return_value = 8.0  # 8GB

        validator = SystemValidator(logger=mock_logger)
        validator._check_ram()

        assert len(validator.results) == 1
        assert validator.results[0].passed is True

    @patch("configurator.core.validator.get_ram_gb")
    def test_insufficient_ram_fails(self, mock_ram, mock_logger):
        """Test that insufficient RAM fails."""
        mock_ram.return_value = 1.0  # 1GB (below minimum)

        validator = SystemValidator(logger=mock_logger)
        validator._check_ram()

        assert len(validator.results) == 1
        assert validator.results[0].passed is False

    @patch("configurator.core.validator.check_internet")
    def test_internet_connected_passes(self, mock_internet, mock_logger):
        """Test that internet connectivity passes."""
        mock_internet.return_value = True

        validator = SystemValidator(logger=mock_logger)
        validator._check_internet()

        assert len(validator.results) == 1
        assert validator.results[0].passed is True

    @patch("configurator.core.validator.check_internet")
    def test_no_internet_fails(self, mock_internet, mock_logger):
        """Test that no internet fails."""
        mock_internet.return_value = False

        validator = SystemValidator(logger=mock_logger)
        validator._check_internet()

        assert len(validator.results) == 1
        assert validator.results[0].passed is False

    def test_get_summary(self, mock_logger):
        """Test getting validation summary."""
        validator = SystemValidator(logger=mock_logger)
        validator.results = [
            ValidationResult(name="A", passed=True, message="ok"),
            ValidationResult(name="B", passed=True, message="ok"),
            ValidationResult(name="C", passed=False, message="fail"),
        ]

        summary = validator.get_summary()
        assert "2/3" in summary
