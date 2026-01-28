import base64
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from configurator.exceptions import ConfiguratorError

logger = logging.getLogger(__name__)


class SecretsError(ConfiguratorError):
    """Exception raised for secrets management errors."""


class SecretsManager:
    """
    Manages secure storage of sensitive data using encryption.

    Implementation:
    - Uses Fernet (symmetric encryption) from the cryptography library
    - Derives encryption keys from a Master Password using PBKDF2HMAC
    - Stores encrypted secrets in a JSON file with restricted permissions (0600)
    - Automatically handles key derivation and storage initialization
    """

    DEFAULT_STORAGE_PATH = Path("/var/lib/debian-vps-configurator/secrets.json")
    DEFAULT_MASTER_KEY_PATH = Path("/etc/debian-vps-configurator/.master_key")

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the secrets manager.

        Args:
            storage_path: Path to the JSON file storing encrypted secrets.
        """
        self.storage_path = storage_path or self.DEFAULT_STORAGE_PATH
        self._fernet: Optional[Fernet] = None
        self._secrets: Dict[str, str] = {}

        # Ensure directory exists
        if not self.storage_path.parent.exists():
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                os.chmod(self.storage_path.parent, 0o700)
            except PermissionError:
                # If running as non-root during dev/test, use local dir
                self.storage_path = Path.cwd() / "secrets.json"
                logger.warning(f"Using local secrets storage: {self.storage_path}")

        self._initialize_encryption()
        self._load_storage()

    def _initialize_encryption(self) -> None:
        """Initialize the encryption key using master password."""
        master_password = os.environ.get("DVPS_MASTER_PASSWORD")

        if not master_password:
            # Try to load from file
            if self.DEFAULT_MASTER_KEY_PATH.exists():
                try:
                    with open(self.DEFAULT_MASTER_KEY_PATH, "r") as f:
                        master_password = f.read().strip()
                except PermissionError:
                    pass

            # If still no password and we are interactive, ask or generate (if root)
            if not master_password:
                if os.getuid() == 0:
                    # Auto-generate for root usage (automation friendly)
                    master_password = base64.urlsafe_b64encode(os.urandom(32)).decode()
                    try:
                        # Ensure directory exists
                        self.DEFAULT_MASTER_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
                        os.chmod(self.DEFAULT_MASTER_KEY_PATH.parent, 0o700)

                        with open(self.DEFAULT_MASTER_KEY_PATH, "w") as f:
                            f.write(master_password)
                        os.chmod(self.DEFAULT_MASTER_KEY_PATH, 0o600)
                        logger.info(
                            f"Generated new master password at {self.DEFAULT_MASTER_KEY_PATH}"
                        )
                    except OSError as e:
                        logger.warning(f"Could not save master password: {e}")
                else:
                    # Use a default development key if not root and not specified
                    # In production, this should error out or prompt
                    logger.warning("Using default development master key (INSECURE)")
                    master_password = "development_insecure_master_key"

        # Derive key
        try:
            # Load or generate salt - use storage path parent for testability
            # In production, storage_path parent is DEFAULT_STORAGE_PATH.parent
            salt_dir = self.storage_path.parent
            salt_path = salt_dir / ".salt"
            salt = None

            if salt_path.exists():
                try:
                    with open(salt_path, "rb") as f:
                        salt = f.read()
                except OSError:
                    pass

            if not salt or len(salt) != 16:
                salt = os.urandom(16)
                try:
                    # Save salt with restricted permissions
                    with open(salt_path, "wb") as f:
                        f.write(salt)
                    os.chmod(salt_path, 0o600)
                    logger.info(f"Generated new cryptographic salt at {salt_path}")
                except OSError as e:
                    logger.warning(
                        f"Could not save salt: {e}. Keys will not be persistent across re-installs of salt file."
                    )

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
            self._fernet = Fernet(key)
        except Exception as e:
            raise SecretsError(f"Failed to initialize encryption: {e}")

    def _load_storage(self) -> None:
        """Load encrypted secrets from storage."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self._secrets = data.get("secrets", {})
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load secrets storage: {e}")
            # Don't crash, just start empty
            self._secrets = {}

    def _save_storage(self) -> None:
        """Save encrypted secrets to storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump({"secrets": self._secrets}, f, indent=2)
            os.chmod(self.storage_path, 0o600)
        except OSError as e:
            raise SecretsError(f"Failed to save secrets: {e}")

    def store(self, key: str, value: str) -> None:
        """
        Encrypt and store a secret.

        Args:
            key: Secret identifier
            value: Secret value
        """
        if not self._fernet:
            raise SecretsError("Encryption not initialized")

        encrypted = self._fernet.encrypt(value.encode()).decode()
        self._secrets[key] = encrypted
        self._save_storage()
        logger.debug(f"Stored secret: {key}")

    def retrieve(self, key: str) -> Optional[str]:
        """
        Retrieve and decrypt a secret.

        Args:
            key: Secret identifier

        Returns:
            Decrypted secret or None if not found
        """
        if not self._fernet:
            raise SecretsError("Encryption not initialized")

        encrypted = self._secrets.get(key)
        if not encrypted:
            return None

        try:
            return self._fernet.decrypt(encrypted.encode()).decode()
        except Exception as e:
            # More user-friendly error
            msg = f"Failed to decrypt secret '{key}'. Master password mismatch or corruption."
            logger.error(f"{msg} ({e})")
            raise SecretsError(msg) from e

    def list_keys(self) -> List[str]:
        """List all stored secret keys."""
        return list(self._secrets.keys())

    def delete(self, key: str) -> bool:
        """
        Delete a secret.

        Returns:
            True if deleted, False if not found
        """
        if key in self._secrets:
            del self._secrets[key]
            self._save_storage()
            logger.debug(f"Deleted secret: {key}")
            return True
        return False
