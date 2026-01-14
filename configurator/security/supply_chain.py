"""
Supply Chain Security Module.

Mitigates supply chain attack vectors by:
- Verifying checksums for downloads
- Validating GPG signatures
- Maintaining allowlist of trusted sources
- Logging all external resource fetches

Addresses security audit findings around Oh My Zsh and theme installations.
"""

import hashlib
import logging
import re
import subprocess
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TrustedSource:
    """Represents a trusted external source."""

    url_pattern: str  # Regex pattern for matching URLs
    requires_checksum: bool = True
    requires_signature: bool = False
    allowed_protocols: List[str] = field(default_factory=lambda: ["https"])

    def matches(self, url: str) -> bool:
        """Check if URL matches this trusted source."""
        return bool(re.match(self.url_pattern, url))


@dataclass
class DownloadRecord:
    """Record of external download for audit trail."""

    url: str
    timestamp: datetime
    checksum_sha256: str
    verified: bool
    source_type: str  # github, apt, web, etc.
    destination: Optional[str] = None


class SupplyChainValidator:
    """
    Supply chain security validator.

    Validates external downloads against checksums, signatures,
    and allowlists to prevent supply chain attacks.
    """

    def __init__(self, config: dict, logger: logging.Logger):
        """
        Initialize supply chain validator.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.enabled = config.get("security_advanced.supply_chain.enabled", True)
        self.verify_checksums = config.get("security_advanced.supply_chain.verify_checksums", True)
        self.verify_signatures = config.get(
            "security_advanced.supply_chain.verify_signatures", True
        )
        self.checksum_db_path = Path(
            config.get(
                "security_advanced.supply_chain.checksum_database",
                "/etc/vps-configurator/checksums.db",
            )
        )
        self.download_history: List[DownloadRecord] = []

        # Build trusted sources
        self.trusted_sources = self._build_trusted_sources()

    def _build_trusted_sources(self) -> List[TrustedSource]:
        """Build list of trusted sources from config."""
        sources = []

        allowed = self.config.get("security_advanced.supply_chain.allowed_sources", {})

        # GitHub sources
        for repo in allowed.get("github", []):
            pattern = f"https://{re.escape(repo)}.*"
            sources.append(
                TrustedSource(
                    url_pattern=pattern,
                    requires_checksum=True,
                    requires_signature=False,
                    allowed_protocols=["https"],
                )
            )

        # APT sources
        for apt_host in allowed.get("apt", []):
            pattern = f"https?://{re.escape(apt_host)}.*"
            sources.append(
                TrustedSource(
                    url_pattern=pattern,
                    requires_checksum=True,
                    requires_signature=True,
                    allowed_protocols=["http", "https"],
                )
            )

        return sources

    def validate_url(self, url: str) -> bool:
        """
        Validate URL against trusted sources.

        Args:
            url: URL to validate

        Returns:
            bool: True if URL is trusted
        """
        if not self.enabled:
            return True

        parsed = urllib.parse.urlparse(url)

        # Check protocol
        if parsed.scheme not in ["http", "https"]:
            self.logger.warning(f"Supply chain: Untrusted protocol: {parsed.scheme}")
            return False

        # Check against trusted sources
        for source in self.trusted_sources:
            if source.matches(url):
                if parsed.scheme not in source.allowed_protocols:
                    self.logger.warning(
                        f"Supply chain: Protocol {parsed.scheme} not allowed for {url}"
                    )
                    return False
                return True

        self.logger.warning(f"Supply chain: URL not in allowlist: {url}")
        return False

    def compute_checksum(self, filepath: Path) -> str:
        """
        Compute SHA256 checksum of file.

        Args:
            filepath: Path to file

        Returns:
            str: Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def verify_checksum(self, filepath: Path, expected_checksum: str) -> bool:
        """
        Verify file checksum.

        Args:
            filepath: Path to file
            expected_checksum: Expected SHA256 hex digest

        Returns:
            bool: True if checksum matches
        """
        if not self.enabled or not self.verify_checksums:
            return True

        actual = self.compute_checksum(filepath)
        matches = actual.lower() == expected_checksum.lower()

        if not matches:
            self.logger.error(
                f"Supply chain: Checksum mismatch for {filepath}\n"
                f"  Expected: {expected_checksum}\n"
                f"  Actual:   {actual}"
            )

        return matches

    def verify_gpg_signature(self, filepath: Path, signature_path: Path) -> bool:
        """
        Verify GPG signature of file.

        Args:
            filepath: Path to file
            signature_path: Path to detached signature (.asc or .sig)

        Returns:
            bool: True if signature is valid
        """
        if not self.enabled or not self.verify_signatures:
            return True

        try:
            result = subprocess.run(
                ["gpg", "--verify", str(signature_path), str(filepath)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                self.logger.info(f"Supply chain: Valid GPG signature for {filepath}")
                return True
            else:
                self.logger.error(
                    f"Supply chain: Invalid GPG signature for {filepath}\n{result.stderr}"
                )
                return False

        except FileNotFoundError:
            self.logger.warning("Supply chain: gpg not installed, cannot verify signatures")
            return False
        except Exception as e:
            self.logger.error(f"Supply chain: Signature verification failed: {e}")
            return False

    def store_checksum(self, url: str, checksum: str):
        """
        Store checksum in database.

        Args:
            url: Source URL
            checksum: SHA256 checksum
        """
        if not self.checksum_db_path.exists():
            self.checksum_db_path.parent.mkdir(parents=True, exist_ok=True)
            self.checksum_db_path.touch()

        # Simple append-based database (URL|CHECKSUM|TIMESTAMP)
        with open(self.checksum_db_path, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{url}|{checksum}|{timestamp}\n")

    def lookup_checksum(self, url: str) -> Optional[str]:
        """
        Lookup stored checksum for URL.

        Args:
            url: Source URL

        Returns:
            Optional[str]: Checksum if found, None otherwise
        """
        if not self.checksum_db_path.exists():
            return None

        with open(self.checksum_db_path, "r") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) >= 2 and parts[0] == url:
                    return parts[1]

        return None

    def validate_download(
        self,
        url: str,
        filepath: Path,
        expected_checksum: Optional[str] = None,
        signature_path: Optional[Path] = None,
    ) -> bool:
        """
        Validate downloaded file.

        Args:
            url: Source URL
            filepath: Downloaded file path
            expected_checksum: Expected SHA256 (optional, will lookup in DB)
            signature_path: Path to GPG signature (optional)

        Returns:
            bool: True if validation passed
        """
        if not self.enabled:
            return True

        # Validate URL
        if not self.validate_url(url):
            return False

        # Compute checksum
        actual_checksum = self.compute_checksum(filepath)

        # Verify checksum
        if expected_checksum:
            if not self.verify_checksum(filepath, expected_checksum):
                return False
        else:
            # Try lookup
            stored_checksum = self.lookup_checksum(url)
            if stored_checksum:
                if not self.verify_checksum(filepath, stored_checksum):
                    return False
            else:
                # First download, store checksum
                self.logger.info(f"Supply chain: First download from {url}, storing checksum")
                self.store_checksum(url, actual_checksum)

        # Verify signature if provided
        if signature_path and signature_path.exists():
            if not self.verify_gpg_signature(filepath, signature_path):
                return False

        # Record download
        record = DownloadRecord(
            url=url,
            timestamp=datetime.now(),
            checksum_sha256=actual_checksum,
            verified=True,
            source_type=self._detect_source_type(url),
            destination=str(filepath),
        )
        self.download_history.append(record)

        self.logger.info(f"Supply chain: Validated download from {url}")
        return True

    def _detect_source_type(self, url: str) -> str:
        """Detect source type from URL."""
        if "github.com" in url:
            return "github"
        elif "debian.org" in url:
            return "apt"
        else:
            return "web"

    def get_audit_report(self) -> Dict:
        """
        Get audit report of all downloads.

        Returns:
            Dict: Audit report with download history
        """
        return {
            "total_downloads": len(self.download_history),
            "verified_downloads": len([r for r in self.download_history if r.verified]),
            "downloads": [
                {
                    "url": r.url,
                    "timestamp": r.timestamp.isoformat(),
                    "checksum": r.checksum_sha256,
                    "verified": r.verified,
                    "source_type": r.source_type,
                }
                for r in self.download_history
            ],
        }


class SecureDownloader:
    """
    Secure downloader with supply chain validation.

    Wraps download operations with automatic validation.
    """

    def __init__(self, validator: SupplyChainValidator, logger: logging.Logger):
        """
        Initialize secure downloader.

        Args:
            validator: Supply chain validator
            logger: Logger instance
        """
        self.validator = validator
        self.logger = logger

    def download_file(
        self,
        url: str,
        destination: Path,
        expected_checksum: Optional[str] = None,
        verify_signature: bool = False,
    ) -> bool:
        """
        Download file with validation.

        Args:
            url: Source URL
            destination: Destination path
            expected_checksum: Expected SHA256 checksum
            verify_signature: Whether to verify GPG signature

        Returns:
            bool: True if download and validation successful
        """
        # Pre-validate URL
        if not self.validator.validate_url(url):
            self.logger.error(f"Secure download: URL validation failed: {url}")
            return False

        # Download using curl/wget
        try:
            subprocess.run(
                ["curl", "-L", "-o", str(destination), url],
                check=True,
                capture_output=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Secure download: Download failed: {e}")
            return False
        except FileNotFoundError:
            # Fallback to wget
            try:
                subprocess.run(
                    ["wget", "-O", str(destination), url],
                    check=True,
                    capture_output=True,
                    timeout=300,
                )
            except Exception as e:
                self.logger.error(f"Secure download: Download failed (wget): {e}")
                return False

        # Download signature if requested
        signature_path = None
        if verify_signature:
            signature_url = f"{url}.asc"
            signature_path = destination.with_suffix(destination.suffix + ".asc")
            try:
                subprocess.run(
                    ["curl", "-L", "-o", str(signature_path), signature_url],
                    check=True,
                    capture_output=True,
                    timeout=60,
                )
            except Exception:
                self.logger.warning(f"Secure download: Signature not available: {signature_url}")
                signature_path = None

        # Validate
        if self.validator.validate_download(url, destination, expected_checksum, signature_path):
            self.logger.info(f"Secure download: Successfully downloaded and validated {url}")
            return True
        else:
            # Validation failed, remove downloaded file
            self.logger.error(f"Secure download: Validation failed, removing {destination}")
            destination.unlink(missing_ok=True)
            return False

    def download_script(
        self, url: str, destination: Path, expected_checksum: Optional[str] = None
    ) -> bool:
        """
        Download and validate shell script.

        Args:
            url: Script URL
            destination: Destination path
            expected_checksum: Expected SHA256 checksum

        Returns:
            bool: True if successful
        """
        success = self.download_file(url, destination, expected_checksum)

        if success:
            # Make executable
            destination.chmod(0o755)
            self.logger.info(f"Secure download: Script ready at {destination}")

        return success
