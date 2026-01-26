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
import json
import logging
import re
import subprocess
import tempfile
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


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


class SecurityError(Exception):
    """
    Raised when supply chain security validation fails.

    Provides structured error information for debugging and user guidance.
    """

    def __init__(self, what: str, why: str, how: str):
        """
        Initialize security error.

        Args:
            what: What failed (concise description)
            why: Why it failed (technical details)
            how: How to fix it (actionable steps)
        """
        self.what = what
        self.why = why
        self.how = how

        message = f"""
╔══════════════════════════════════════════════════════════╗
║                 🚨 SECURITY ALERT 🚨                      ║
╚══════════════════════════════════════════════════════════╝

WHAT HAPPENED:
  {what}

WHY IT HAPPENED:
  {why}

WHAT TO DO:
  {how}

🔒 This is a security-critical error. Do not bypass this check.
📧 Report security issues: https://github.com/ahmadrizal7/debian-vps-workstation/security
"""
        super().__init__(message)


class SupplyChainValidator:
    """
    Supply chain security validator.

    Validates external downloads against checksums, signatures,
    and allowlists to prevent supply chain attacks.
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize supply chain validator.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Helper function to get nested config values
        def get_nested(d: Dict[str, Any], key: str, default: Any = None) -> Any:
            """Get nested dict value by dot notation key."""
            keys = key.split(".")
            current: Any = d
            for k in keys:
                if isinstance(current, dict):
                    current = current.get(k, {})
                else:
                    return default
            return current if current != {} else default

        self.enabled = get_nested(config, "security_advanced.supply_chain.enabled", True)
        self.verify_checksums = get_nested(
            config, "security_advanced.supply_chain.verify_checksums", True
        )
        self.verify_signatures = get_nested(
            config, "security_advanced.supply_chain.verify_signatures", True
        )
        self.strict_mode = get_nested(config, "security_advanced.supply_chain.strict_mode", False)

        self.checksum_db_path = Path(
            get_nested(
                config,
                "security_advanced.supply_chain.checksum_database",
                "/etc/vps-configurator/checksums.db",
            )
        )

        # Load YAML checksum database
        self.checksums = self._load_checksums()

        # Audit log path
        self.audit_log_path = Path(
            get_nested(
                config,
                "security_advanced.supply_chain.audit_log",
                "/var/log/vps-configurator/supply-chain-audit.log",
            )
        )
        # Only create parent dir if it doesn't exist and we have permission
        try:
            self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fall back to temp directory for testing
            import tempfile

            self.audit_log_path = Path(tempfile.gettempdir()) / "supply-chain-audit.log"
            self.logger.debug(f"Using temp audit log: {self.audit_log_path}")

        self.download_history: List[DownloadRecord] = []

        # Build trusted sources
        self.trusted_sources = self._build_trusted_sources()

    def _load_checksums(self) -> Dict[str, Any]:
        """Load checksum database from YAML file."""
        # Look for checksums.yaml next to this module
        checksum_file = Path(__file__).parent / "checksums.yaml"

        if not checksum_file.exists():
            self.logger.warning(f"Checksum database not found: {checksum_file}")
            return {}

        try:
            with open(checksum_file, "r") as f:
                data = yaml.safe_load(f) or {}
                self.logger.debug(f"Loaded {len(data)} checksum entries from {checksum_file}")
                return data
        except Exception as e:
            self.logger.error(f"Failed to load checksums: {e}")
            return {}

    def _build_trusted_sources(self) -> List[TrustedSource]:
        """Build list of trusted sources from config."""
        sources = []

        # Helper function to get nested config values
        def get_nested(d: Dict[str, Any], key: str, default: Any = None) -> Any:
            """Get nested dict value by dot notation key."""
            keys = key.split(".")
            current: Any = d
            for k in keys:
                if isinstance(current, dict):
                    current = current.get(k, {})
                else:
                    return default
            return current if current != {} else default

        allowed = get_nested(self.config, "security_advanced.supply_chain.allowed_sources", {})

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

        # Web sources (general web downloads)
        for web_host in allowed.get("web", []):
            pattern = f"https?://.*{re.escape(web_host)}.*"
            sources.append(
                TrustedSource(
                    url_pattern=pattern,
                    requires_checksum=True,
                    requires_signature=False,
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

        Raises:
            SecurityError: If checksum mismatch detected (strict mode)
        """
        if not self.enabled or not self.verify_checksums:
            self.logger.warning("Supply chain validation disabled - SKIPPING CHECKSUM")
            return True

        try:
            actual = self.compute_checksum(filepath)
            matches = actual.lower() == expected_checksum.lower()

            if not matches:
                error_msg_what = f"Checksum mismatch for {filepath.name}"
                error_msg_why = f"Expected: {expected_checksum}\nActual: {actual}"
                error_msg_how = (
                    "1. This could indicate a compromised download\n"
                    "2. DO NOT proceed with installation\n"
                    "3. Report to: https://github.com/ahmadrizal7/debian-vps-workstation/security\n"
                    "4. Check if checksum database is outdated"
                )

                if self.strict_mode:
                    raise SecurityError(error_msg_what, error_msg_why, error_msg_how)
                else:
                    self.logger.error(f"Supply chain: {error_msg_what}\n{error_msg_why}")
                    return False

            self.logger.info(f"✅ Checksum verified: {filepath.name}")
            self._audit_log("checksum_verified", str(filepath), actual)
            return True

        except FileNotFoundError:
            raise SecurityError(
                what=f"File not found: {filepath}",
                why="Download may have failed",
                how="Check network connection and retry",
            )

    def verify_apt_key_fingerprint(
        self, key_source: str, expected_fingerprint: str, is_local_file: bool = False
    ) -> bool:
        """
        Verify APT repository GPG key fingerprint.

        Args:
            key_source: URL to GPG key or local file path
            expected_fingerprint: Expected key fingerprint (40 hex chars)
            is_local_file: True if key_source is a local file path

        Returns:
            bool: True if fingerprint matches

        Raises:
            SecurityError: If fingerprint mismatch detected
        """
        if not self.enabled:
            return True

        try:
            if is_local_file:
                # Use existing local file
                tmp_path = Path(key_source)
                cleanup_needed = False
            else:
                # Download key to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".gpg") as tmp:
                    tmp_path = Path(tmp.name)
                cleanup_needed = True

                subprocess.run(
                    ["curl", "-fsSL", key_source, "-o", str(tmp_path)],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )

            # Get fingerprint using gpg with machine-readable output
            result = subprocess.run(
                ["gpg", "--with-colons", "--show-keys", str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Clean up temp file if we created it
            if cleanup_needed:
                tmp_path.unlink()

            # Extract fingerprints from output (looking for 'fpr' record type)
            # Format: fpr:::::::::FINGERPRINT:
            fingerprints = []
            for line in result.stdout.splitlines():
                if line.startswith("fpr:"):
                    parts = line.split(":")
                    if len(parts) > 9:
                        fingerprints.append(parts[9])

            if not fingerprints:
                # Fallback to standard output check if no fpr records found (unlikely with --with-colons)
                fingerprints = re.findall(r"[A-F0-9]{40}", result.stdout.replace(" ", "").upper())

            # Normalize fingerprints (remove spaces)
            expected_normalized = expected_fingerprint.replace(" ", "").upper()
            found_normalized = [fp.replace(" ", "").upper() for fp in fingerprints]

            if expected_normalized not in found_normalized:
                raise SecurityError(
                    what="APT key fingerprint mismatch",
                    why=f"Expected: {expected_fingerprint}\nFound: {fingerprints}",
                    how="DO NOT add this repository - key may be compromised",
                )

            self.logger.info(f"✅ APT key fingerprint verified: {expected_fingerprint[:16]}...")
            self._audit_log("apt_key_verified", key_source, expected_fingerprint)
            return True

        except FileNotFoundError:
            self.logger.warning("GPG not installed, cannot verify fingerprint")
            return not self.strict_mode  # Fail in strict mode
        except subprocess.CalledProcessError as e:
            raise SecurityError(
                what="APT key verification failed",
                why=str(e),
                how="Check network connectivity and GPG installation",
            )

    def _audit_log(self, event_type: str, resource: str, verification: str) -> None:
        """
        Log supply chain audit event.

        Args:
            event_type: Type of event (checksum_verified, apt_key_verified, etc.)
            resource: Resource path or URL
            verification: Verification value (checksum, fingerprint, etc.)
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "resource": resource,
            "verification": verification,
        }

        try:
            with open(self.audit_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to write audit log: {e}")

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

    def store_checksum(self, url: str, checksum: str) -> None:
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

    def get_audit_report(self) -> Dict[str, Any]:
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

    def git_clone_verified(
        self, url: str, dest: str, commit: Optional[str] = None, depth: int = 1
    ) -> Path:
        """
        Git clone with commit verification.

        Args:
            url: Git repository URL
            dest: Destination directory
            commit: Specific commit hash to checkout (for security pinning)
            depth: Clone depth (1 for shallow clone)

        Returns:
            Path: Path to cloned repository

        Raises:
            SecurityError: If commit verification fails
        """
        dest_path = Path(dest)

        self.logger.info(f"Cloning: {url}")

        # Build git clone command
        cmd = ["git", "clone"]
        if depth:
            cmd.extend(["--depth", str(depth)])
        cmd.extend([url, str(dest_path)])

        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git clone failed: {e.stderr.decode()}")

        # Checkout and verify specific commit if provided
        if commit:
            self.logger.info(f"Checking out commit: {commit[:8]}...")

            # Fetch if shallow clone
            if depth:
                try:
                    subprocess.run(
                        ["git", "-C", str(dest_path), "fetch", "--depth=1", "origin", commit],
                        check=True,
                        capture_output=True,
                        timeout=60,
                    )
                except subprocess.CalledProcessError:
                    # Commit might already be in shallow clone
                    pass

            # Checkout the commit
            subprocess.run(
                ["git", "-C", str(dest_path), "checkout", commit],
                check=True,
                capture_output=True,
                timeout=30,
            )

            # Verify we're on the right commit
            result = subprocess.run(
                ["git", "-C", str(dest_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            actual_commit = result.stdout.strip()
            if actual_commit != commit:
                raise SecurityError(
                    what="Git commit mismatch",
                    why=f"Expected: {commit}\nActual: {actual_commit}",
                    how="Repository may have been tampered with - DO NOT use",
                )

            self.logger.info(f"✅ Git commit verified: {commit[:8]}")

        return dest_path

    def download_and_extract(
        self, url: str, dest_dir: str, checksum: Optional[str] = None, archive_type: str = "auto"
    ) -> Path:
        """
        Download and extract archive with verification.

        Args:
            url: Archive URL
            dest_dir: Extraction directory
            checksum: Expected SHA256 checksum
            archive_type: Archive type (tar.gz, zip, auto)

        Returns:
            Path: Path to extracted directory
        """
        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".archive") as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Download with verification
            if not self.download_file(url, tmp_path, checksum):
                raise SecurityError(
                    what=f"Download verification failed for {url}",
                    why="Checksum mismatch or download error",
                    how="Check network and verify checksum in database",
                )

            # Auto-detect archive type
            if archive_type == "auto":
                if url.endswith(".tar.gz") or url.endswith(".tgz"):
                    archive_type = "tar.gz"
                elif url.endswith(".zip"):
                    archive_type = "zip"
                else:
                    raise ValueError(f"Cannot detect archive type for: {url}")

            # Extract
            dest_path = Path(dest_dir)
            dest_path.mkdir(parents=True, exist_ok=True)

            if archive_type == "tar.gz":
                subprocess.run(
                    ["tar", "-xzf", str(tmp_path), "-C", str(dest_path)], check=True, timeout=120
                )
            elif archive_type == "zip":
                subprocess.run(
                    ["unzip", "-q", str(tmp_path), "-d", str(dest_path)], check=True, timeout=120
                )

            self.logger.info(f"✅ Extracted to: {dest_path}")
            return dest_path

        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()
