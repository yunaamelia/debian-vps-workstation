"""
Unit tests for MFA Manager.
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from configurator.security.mfa_manager import (
    PYOTP_AVAILABLE,
    MFAConfig,
    MFAManager,
    MFAMethod,
    MFAStatus,
)


class TestMFAMethod(unittest.TestCase):
    """Test MFAMethod enum."""

    def test_totp_value(self):
        """Test TOTP method value."""
        self.assertEqual(MFAMethod.TOTP.value, "totp")

    def test_sms_value(self):
        """Test SMS method value."""
        self.assertEqual(MFAMethod.SMS.value, "sms")

    def test_backup_code_value(self):
        """Test backup code method value."""
        self.assertEqual(MFAMethod.BACKUP_CODE.value, "backup")

    def test_hardware_value(self):
        """Test hardware method value."""
        self.assertEqual(MFAMethod.HARDWARE.value, "hardware")


class TestMFAStatus(unittest.TestCase):
    """Test MFAStatus enum."""

    def test_enabled_value(self):
        """Test enabled status value."""
        self.assertEqual(MFAStatus.ENABLED.value, "enabled")

    def test_disabled_value(self):
        """Test disabled status value."""
        self.assertEqual(MFAStatus.DISABLED.value, "disabled")

    def test_pending_value(self):
        """Test pending status value."""
        self.assertEqual(MFAStatus.PENDING.value, "pending")

    def test_locked_value(self):
        """Test locked status value."""
        self.assertEqual(MFAStatus.LOCKED.value, "locked")


class TestMFAConfig(unittest.TestCase):
    """Test MFAConfig dataclass."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"],
            enabled=True,
            enrolled_at=datetime(2026, 1, 6, 12, 0, 0),
            last_used=datetime(2026, 1, 6, 14, 30, 0),
            failed_attempts=0,
            status=MFAStatus.ENABLED,
        )

    def test_config_creation(self):
        """Test MFAConfig creation."""
        self.assertEqual(self.config.user, "testuser")
        self.assertEqual(self.config.method, MFAMethod.TOTP)
        self.assertEqual(self.config.secret, "JBSWY3DPEHPK3PXP")
        self.assertTrue(self.config.enabled)

    def test_backup_codes_remaining(self):
        """Test backup codes remaining count."""
        self.assertEqual(self.config.backup_codes_remaining(), 2)

    def test_is_locked_false(self):
        """Test is_locked when not locked."""
        self.assertFalse(self.config.is_locked())

    def test_is_locked_true(self):
        """Test is_locked when locked."""
        self.config.status = MFAStatus.LOCKED
        self.assertTrue(self.config.is_locked())

    def test_to_dict(self):
        """Test serialization to dictionary."""
        data = self.config.to_dict()

        self.assertEqual(data["user"], "testuser")
        self.assertEqual(data["method"], "totp")
        self.assertEqual(data["secret"], "JBSWY3DPEHPK3PXP")
        self.assertEqual(data["backup_codes"], ["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"])
        self.assertTrue(data["enabled"])
        self.assertEqual(data["status"], "enabled")
        self.assertIsNotNone(data["enrolled_at"])
        self.assertIsNotNone(data["last_used"])

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "user": "newuser",
            "method": "totp",
            "secret": "ABCDEFGH",
            "backup_codes": ["1111-2222-3333"],
            "enabled": False,
            "enrolled_at": "2026-01-06T10:00:00",
            "last_used": None,
            "failed_attempts": 2,
            "status": "pending",
        }

        config = MFAConfig.from_dict(data)

        self.assertEqual(config.user, "newuser")
        self.assertEqual(config.method, MFAMethod.TOTP)
        self.assertEqual(config.secret, "ABCDEFGH")
        self.assertEqual(config.failed_attempts, 2)
        self.assertEqual(config.status, MFAStatus.PENDING)

    def test_roundtrip_serialization(self):
        """Test roundtrip serialization."""
        data = self.config.to_dict()
        restored = MFAConfig.from_dict(data)

        self.assertEqual(restored.user, self.config.user)
        self.assertEqual(restored.secret, self.config.secret)
        self.assertEqual(restored.enabled, self.config.enabled)


class TestMFAManager(unittest.TestCase):
    """Test MFAManager class."""

    def setUp(self):
        """Set up test fixtures with mocked methods."""
        self.manager_patch = patch.object(MFAManager, "_ensure_config_dir", return_value=None)
        self.load_patch = patch.object(MFAManager, "_load_configs", return_value=None)

        self.manager_patch.start()
        self.load_patch.start()

        self.manager = MFAManager()
        self.manager._configs = {}

    def tearDown(self):
        """Clean up patches."""
        self.manager_patch.stop()
        self.load_patch.stop()

    def test_list_users_empty(self):
        """Test list_users with no configs."""
        self.assertEqual(self.manager.list_users(), [])

    def test_list_users_with_configs(self):
        """Test list_users with some configs."""
        self.manager._configs = {
            "user1": MagicMock(),
            "user2": MagicMock(),
        }

        users = self.manager.list_users()
        self.assertIn("user1", users)
        self.assertIn("user2", users)

    def test_get_user_config_not_found(self):
        """Test get_user_config for non-existent user."""
        self.assertIsNone(self.manager.get_user_config("nonexistent"))

    def test_get_user_config_found(self):
        """Test get_user_config for existing user."""
        mock_config = MagicMock()
        self.manager._configs["testuser"] = mock_config

        result = self.manager.get_user_config("testuser")
        self.assertEqual(result, mock_config)

    def test_get_summary_empty(self):
        """Test get_summary with no users."""
        summary = self.manager.get_summary()

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["enabled"], 0)
        self.assertEqual(summary["pending"], 0)
        self.assertEqual(summary["locked"], 0)

    def test_get_summary_with_users(self):
        """Test get_summary with various user states."""
        self.manager._configs = {
            "enabled_user": MFAConfig(
                user="enabled_user",
                method=MFAMethod.TOTP,
                secret="ABC",
                enabled=True,
                status=MFAStatus.ENABLED,
            ),
            "pending_user": MFAConfig(
                user="pending_user",
                method=MFAMethod.TOTP,
                secret="DEF",
                enabled=False,
                status=MFAStatus.PENDING,
            ),
            "locked_user": MFAConfig(
                user="locked_user",
                method=MFAMethod.TOTP,
                secret="GHI",
                enabled=True,
                status=MFAStatus.LOCKED,
            ),
        }

        summary = self.manager.get_summary()

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["enabled"], 2)
        self.assertEqual(summary["pending"], 1)
        self.assertEqual(summary["locked"], 1)

    def test_generate_backup_codes_count(self):
        """Test backup code generation returns correct count."""
        codes = self.manager._generate_backup_codes(5)

        self.assertEqual(len(codes), 5)

    def test_generate_backup_codes_format(self):
        """Test backup code format."""
        codes = self.manager._generate_backup_codes(1)
        code = codes[0]

        # Format: XXXX-XXXX-XXXX
        parts = code.split("-")
        self.assertEqual(len(parts), 3)
        for part in parts:
            self.assertEqual(len(part), 4)
            self.assertTrue(part.isalnum())

    def test_generate_backup_codes_unique(self):
        """Test backup codes are unique."""
        codes = self.manager._generate_backup_codes(10)

        self.assertEqual(len(codes), len(set(codes)))

    def test_unlock_user_not_found(self):
        """Test unlock_user for non-existent user."""
        result = self.manager.unlock_user("nonexistent")
        self.assertFalse(result)

    def test_unlock_user_not_locked(self):
        """Test unlock_user when user is not locked."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="ABC",
            status=MFAStatus.ENABLED,
        )

        result = self.manager.unlock_user("testuser")
        self.assertFalse(result)

    @patch.object(MFAManager, "_save_configs")
    def test_unlock_user_success(self, mock_save):
        """Test successful user unlock."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="ABC",
            status=MFAStatus.LOCKED,
            failed_attempts=5,
        )

        result = self.manager.unlock_user("testuser")

        self.assertTrue(result)
        self.assertEqual(self.manager._configs["testuser"].status, MFAStatus.ENABLED)
        self.assertEqual(self.manager._configs["testuser"].failed_attempts, 0)
        mock_save.assert_called_once()


@unittest.skipUnless(PYOTP_AVAILABLE, "pyotp not installed")
class TestMFAManagerWithPyOTP(unittest.TestCase):
    """Test MFAManager methods that require pyotp."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager_patch = patch.object(MFAManager, "_ensure_config_dir", return_value=None)
        self.load_patch = patch.object(MFAManager, "_load_configs", return_value=None)
        self.save_patch = patch.object(MFAManager, "_save_configs", return_value=None)
        self.backup_file_patch = patch.object(
            MFAManager, "_save_backup_codes_file", return_value=None
        )

        self.manager_patch.start()
        self.load_patch.start()
        self.save_patch.start()
        self.backup_file_patch.start()

        self.manager = MFAManager()
        self.manager._configs = {}

    def tearDown(self):
        """Clean up patches."""
        self.manager_patch.stop()
        self.load_patch.stop()
        self.save_patch.stop()
        self.backup_file_patch.stop()

    def test_enroll_user_creates_config(self):
        """Test enroll_user creates MFAConfig."""
        config, qr = self.manager.enroll_user("testuser")

        self.assertEqual(config.user, "testuser")
        self.assertEqual(config.method, MFAMethod.TOTP)
        self.assertIsNotNone(config.secret)
        self.assertEqual(len(config.backup_codes), 10)
        self.assertFalse(config.enabled)
        self.assertEqual(config.status, MFAStatus.PENDING)

    def test_enroll_user_generates_qr(self):
        """Test enroll_user generates QR code."""
        config, qr = self.manager.enroll_user("testuser")

        self.assertIsNotNone(qr)
        self.assertIsInstance(qr, str)
        # QR code should contain some content
        self.assertGreater(len(qr), 100)

    def test_verify_code_not_configured(self):
        """Test verify_code for non-existent user."""
        result = self.manager.verify_code("nonexistent", "123456")
        self.assertFalse(result)

    def test_verify_code_locked(self):
        """Test verify_code for locked user."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            status=MFAStatus.LOCKED,
        )

        result = self.manager.verify_code("testuser", "123456")
        self.assertFalse(result)

    def test_verify_backup_code_success(self):
        """Test verify_code with valid backup code."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=["AAAA-BBBB-CCCC", "DDDD-EEEE-FFFF"],
            enabled=True,
            status=MFAStatus.ENABLED,
        )

        result = self.manager.verify_code("testuser", "AAAA-BBBB-CCCC")

        self.assertTrue(result)
        # Backup code should be removed
        self.assertNotIn("AAAA-BBBB-CCCC", self.manager._configs["testuser"].backup_codes)

    def test_verify_code_increments_failed_attempts(self):
        """Test verify_code increments failed attempts on bad code."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=[],
            enabled=True,
            status=MFAStatus.ENABLED,
            failed_attempts=0,
        )

        self.manager.verify_code("testuser", "invalid")

        self.assertEqual(self.manager._configs["testuser"].failed_attempts, 1)

    def test_verify_code_locks_after_max_attempts(self):
        """Test verify_code locks user after max failed attempts."""
        self.manager._configs["testuser"] = MFAConfig(
            user="testuser",
            method=MFAMethod.TOTP,
            secret="JBSWY3DPEHPK3PXP",
            backup_codes=[],
            enabled=True,
            status=MFAStatus.ENABLED,
            failed_attempts=4,  # One more will trigger lock
        )

        self.manager.verify_code("testuser", "invalid")

        self.assertEqual(self.manager._configs["testuser"].status, MFAStatus.LOCKED)


if __name__ == "__main__":
    unittest.main()
