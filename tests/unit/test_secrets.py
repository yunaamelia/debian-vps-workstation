import os
from unittest.mock import patch

import pytest

from configurator.core.secrets import SecretsError, SecretsManager


@pytest.fixture
def secrets_manager(tmp_path):
    storage = tmp_path / "secrets.json"

    # Mock master password env var and file permissions
    with patch.dict(os.environ, {"DVPS_MASTER_PASSWORD": "test_master_password"}):
        with patch("os.chmod"):  # Mock chmod since tmp might not support 0600 on all CI
            manager = SecretsManager(storage_path=storage)
            yield manager


def test_store_and_retrieve(secrets_manager):
    secrets_manager.store("api_key", "secret_value_123")
    retrieved = secrets_manager.retrieve("api_key")
    assert retrieved == "secret_value_123"


def test_retrieve_nonexistent(secrets_manager):
    assert secrets_manager.retrieve("missing") is None


def test_delete(secrets_manager):
    secrets_manager.store("key", "val")
    assert secrets_manager.delete("key") is True
    assert secrets_manager.retrieve("key") is None
    assert secrets_manager.delete("key") is False


def test_list_keys(secrets_manager):
    secrets_manager.store("k1", "v1")
    secrets_manager.store("k2", "v2")
    keys = secrets_manager.list_keys()
    assert len(keys) == 2
    assert "k1" in keys
    assert "k2" in keys


def test_persistence(tmp_path):
    storage = tmp_path / "secrets.json"

    with patch.dict(os.environ, {"DVPS_MASTER_PASSWORD": "test_master_password"}):
        with patch("os.chmod"):
            # Store with one instance
            m1 = SecretsManager(storage_path=storage)
            m1.store("persistent_key", "persistent_value")

            # Retrieve with another instance
            m2 = SecretsManager(storage_path=storage)
            assert m2.retrieve("persistent_key") == "persistent_value"


def test_invalid_decrypt_key(tmp_path):
    storage = tmp_path / "secrets.json"

    # Store with one password
    with patch.dict(os.environ, {"DVPS_MASTER_PASSWORD": "pass1"}):
        with patch("os.chmod"):
            m1 = SecretsManager(storage_path=storage)
            m1.store("key", "val")

    # Try to Retrieve with different password
    with patch.dict(os.environ, {"DVPS_MASTER_PASSWORD": "pass2"}):
        with patch("os.chmod"):
            m2 = SecretsManager(storage_path=storage)
            # Should fail to decrypt and raise SecretsError
            with pytest.raises(SecretsError, match="Failed to decrypt"):
                m2.retrieve("key")


def test_permissions_enforcement(tmp_path):
    storage = tmp_path / "secrets.json"

    with patch("os.chmod") as mock_chmod:
        with patch.dict(os.environ, {"DVPS_MASTER_PASSWORD": "test"}):
            m = SecretsManager(storage_path=storage)
            m.store("k", "v")

            # Check if chmod 0600 was called on the file
            mock_chmod.assert_called_with(storage, 0o600)
