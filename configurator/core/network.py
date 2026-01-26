"""
Network operations with built-in resilience.

Provides circuit breaker protection, retry logic, and timeout handling
for all network-dependent operations.
"""

import logging
import random
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional

from configurator.utils.circuit_breaker import CircuitBreaker, CircuitBreakerError


class NetworkOperationType(Enum):
    """Types of network operations."""

    APT_UPDATE = "apt_update"
    APT_INSTALL = "apt_install"
    CURL_DOWNLOAD = "curl_download"
    GIT_CLONE = "git_clone"
    HTTP_REQUEST = "http_request"
    DNS_LOOKUP = "dns_lookup"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True

    # Specific timeouts
    apt_timeout: int = 1200  # 20 minutes
    download_timeout: int = 600  # 10 minutes
    git_timeout: int = 300  # 5 minutes


class NetworkOperationWrapper:
    """
    Wrapper for network operations with resilience patterns.

    Features:
    - Circuit breaker protection
    - Exponential backoff retry
    - Timeout handling
    - Jitter for thundering herd prevention
    - Operation-specific circuit breakers

    Usage:
        wrapper = NetworkOperationWrapper(config, logger)

        # APT operations
        wrapper.apt_update_with_retry()
        wrapper.apt_install_with_retry(['docker-ce', 'docker-compose'])

        # Downloads
        wrapper.download_with_retry(
            url="https://example.com/file.tar.gz",
            dest="/tmp/file.tar.gz"
        )

        # Git operations
        wrapper.git_clone_resilient(
            url="https://github.com/user/repo.git",
            dest="/opt/repo"
        )
    """

    def __init__(
        self, config: dict, logger: logging.Logger, retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize network wrapper.

        Args:
            config: Configuration dictionary
            logger: Logger instance
            retry_config: Optional retry configuration
        """
        self.config = config
        self.logger = logger
        self.retry_config = retry_config or RetryConfig()

        # Circuit breaker configuration
        cb_config = config.get("performance", {}).get("circuit_breaker", {})
        self.cb_enabled = cb_config.get("enabled", True)
        failure_threshold = cb_config.get("failure_threshold", 3)
        timeout = cb_config.get("timeout", 60)

        # Create circuit breakers for different services
        self.circuit_breakers = {}
        if self.cb_enabled:
            services = [
                "apt_repository",
                "github",
                "docker_hub",
                "microsoft_packages",
                "external_downloads",
            ]

            for service in services:
                self.circuit_breakers[service] = CircuitBreaker(
                    name=service,
                    failure_threshold=failure_threshold,
                    timeout=timeout,
                    logger=logger,
                )

    def _get_circuit_breaker(
        self, operation_type: NetworkOperationType
    ) -> Optional[CircuitBreaker]:
        """Get appropriate circuit breaker for operation type."""
        if not self.cb_enabled:
            return None

        mapping = {
            NetworkOperationType.APT_UPDATE: "apt_repository",
            NetworkOperationType.APT_INSTALL: "apt_repository",
            NetworkOperationType.GIT_CLONE: "github",
            NetworkOperationType.CURL_DOWNLOAD: "external_downloads",
        }

        service = mapping.get(operation_type, "external_downloads")
        return self.circuit_breakers.get(service)

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = min(
            self.retry_config.initial_delay * (self.retry_config.exponential_base**attempt),
            self.retry_config.max_delay,
        )

        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter

        return delay

    def execute_with_retry(
        self, operation: Callable, operation_type: NetworkOperationType, *args, **kwargs
    ) -> Any:
        """
        Execute operation with retry logic and circuit breaker.

        Args:
            operation: Function to execute
            operation_type: Type of operation (for circuit breaker selection)
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If all retries exhausted
        """
        cb = self._get_circuit_breaker(operation_type)
        last_exception = None

        for attempt in range(self.retry_config.max_retries):
            try:
                # Execute through circuit breaker if available
                if cb:
                    result = cb.call(operation, *args, **kwargs)
                else:
                    result = operation(*args, **kwargs)

                # Success
                if attempt > 0:
                    self.logger.info(f"✅ Operation succeeded after {attempt + 1} attempts")
                return result

            except CircuitBreakerError as e:
                # Circuit is open, don't retry
                self.logger.error(f"🚨 Circuit breaker open: {e}")
                raise

            except Exception as e:
                last_exception = e

                if attempt < self.retry_config.max_retries - 1:
                    delay = self._calculate_backoff_delay(attempt)

                    self.logger.warning(f"⚠️  Attempt {attempt + 1} failed: {str(e)[:100]}")
                    self.logger.info(
                        f"🔄 Retrying in {delay:.1f}s... "
                        f"({self.retry_config.max_retries - attempt - 1} retries left)"
                    )

                    time.sleep(delay)
                else:
                    self.logger.error(f"❌ All {self.retry_config.max_retries} attempts failed")

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise Exception("Operation failed with no exception captured")

    def apt_update_with_retry(self) -> bool:
        """
        Execute apt-get update with retry and circuit breaker.

        Returns:
            True if successful
        """
        self.logger.info("Updating APT package lists (with retry protection)...")

        def apt_update():
            result = subprocess.run(
                ["apt-get", "update"],
                capture_output=True,
                text=True,
                timeout=self.retry_config.apt_timeout,
            )

            if result.returncode != 0:
                raise Exception(f"APT update failed: {result.stderr}")

            return True

        try:
            self.execute_with_retry(apt_update, NetworkOperationType.APT_UPDATE)
            self.logger.info("✅ APT update successful")
            return True

        except Exception as e:
            self.logger.error(f"❌ APT update failed after retries: {e}")
            return False

    def apt_install_with_retry(self, packages: List[str], update_cache: bool = True) -> bool:
        """
        Install APT packages with retry logic.

        Args:
            packages: List of package names
            update_cache: Whether to update cache first

        Returns:
            True if successful
        """
        if update_cache:
            if not self.apt_update_with_retry():
                return False

        self.logger.info(f"Installing packages: {', '.join(packages)}")
        self.logger.info("This may take several minutes for large packages (e.g., xfce4)...")

        def apt_install():
            # Use -q instead of -qq to show progress, and add --show-progress for visual feedback
            # This ensures output is generated during long installations
            cmd = ["apt-get", "install", "-y", "-q", "--show-progress"] + packages

            # Use Popen to stream output in real-time for better visibility
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )

            # Stream output line by line to show progress
            if process.stdout is None:
                raise Exception("Failed to capture stdout")

            last_log_time = time.time()
            for line in iter(process.stdout.readline, ""):
                if line:
                    # Log every 30 seconds to show progress without spamming
                    current_time = time.time()
                    if current_time - last_log_time >= 30:
                        # Extract progress info if available
                        if "%" in line or "Setting up" in line or "Unpacking" in line:
                            self.logger.info(f"Progress: {line.strip()}")
                            last_log_time = current_time
                        elif "Get:" in line or "Fetched" in line:
                            # Show download progress
                            self.logger.debug(f"Download: {line.strip()[:80]}")

            process.wait()

            if process.returncode != 0:
                raise Exception(f"Package installation failed with exit code {process.returncode}")

            return True

        try:
            self.execute_with_retry(apt_install, NetworkOperationType.APT_INSTALL)
            self.logger.info(f"✅ Installed: {', '.join(packages)}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Installation failed: {e}")
            return False

    def download_with_retry(self, url: str, dest: str, verify_ssl: bool = True) -> Optional[Path]:
        """
        Download file with retry logic.

        Args:
            url: Download URL
            dest: Destination path
            verify_ssl: Verify SSL certificates

        Returns:
            Path to downloaded file or None
        """
        dest_path = Path(dest)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Downloading: {url}")

        def download():
            cmd = ["curl", "-fsSL"]
            if not verify_ssl:
                cmd.append("--insecure")
            cmd.extend(
                [
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    str(self.retry_config.download_timeout),
                    url,
                    "-o",
                    str(dest_path),
                ]
            )

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"Download failed: {result.stderr}")

            return dest_path

        try:
            return self.execute_with_retry(download, NetworkOperationType.CURL_DOWNLOAD)

        except Exception as e:
            self.logger.error(f"❌ Download failed: {e}")
            return None

    def git_clone_resilient(
        self, url: str, dest: str, depth: int = 1, branch: Optional[str] = None
    ) -> bool:
        """
        Git clone with retry and timeout.

        Args:
            url: Git repository URL
            dest: Destination directory
            depth: Clone depth
            branch: Specific branch to clone

        Returns:
            True if successful
        """
        dest_path = Path(dest)

        self.logger.info(f"Cloning: {url}")

        def git_clone():
            cmd = ["git", "clone"]

            if depth:
                cmd.extend(["--depth", str(depth)])

            if branch:
                cmd.extend(["--branch", branch])

            cmd.extend([url, str(dest_path)])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.retry_config.git_timeout
            )

            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")

            return True

        try:
            self.execute_with_retry(git_clone, NetworkOperationType.GIT_CLONE)
            self.logger.info(f"✅ Cloned to: {dest_path}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Git clone failed: {e}")
            return False

    def check_internet_connectivity(self, test_urls: Optional[List[str]] = None) -> bool:
        """
        Check internet connectivity.

        Args:
            test_urls: URLs to test (defaults to common reliable endpoints)

        Returns:
            True if internet is accessible
        """
        if not test_urls:
            test_urls = ["https://deb.debian.org", "https://github.com", "https://google.com"]

        for url in test_urls:
            try:
                result = subprocess.run(
                    ["curl", "-fsSL", "--connect-timeout", "5", "--max-time", "10", url],
                    capture_output=True,
                    timeout=15,
                )

                if result.returncode == 0:
                    self.logger.debug(f"✅ Connectivity check passed: {url}")
                    return True

            except Exception:
                continue

        self.logger.warning("⚠️  Internet connectivity check failed")
        return False

    def get_circuit_breaker_status(self) -> dict:
        """
        Get status of all circuit breakers.

        Returns:
            Dictionary of circuit breaker states
        """
        status = {}

        for name, cb in self.circuit_breakers.items():
            status[name] = {
                "state": cb.state.value,
                "failure_count": cb.failure_count,
                "success_count": cb.success_count,
                "total_calls": cb.total_calls,
                "total_failures": cb.total_failures,
            }

        return status
