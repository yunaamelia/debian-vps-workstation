"""
Health check system for external dependencies.

Monitors connectivity to critical services and provides
status dashboard.
"""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional


class HealthStatus(Enum):
    """Health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Single health check result."""

    service: str
    status: HealthStatus
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None


class HealthCheckService:
    """
    Monitor health of external dependencies.

    Usage:
        health = HealthCheckService(logger)

        # Check all services
        results = health.check_all()

        # Check specific service
        status = health.check_service("apt_repository", "http://deb.debian.org")

        # Get summary
        summary = health.get_summary()
    """

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.last_results: Dict[str, HealthCheck] = {}

        # Define services to monitor
        self.services = {
            "apt_repository": "http://deb.debian.org",
            "github": "https://github.com",
            "docker_hub": "https://hub.docker.com",
            "pypi": "https://pypi.org",
            "npm_registry": "https://registry.npmjs.org",
        }

    def check_service(self, service: str, url: str) -> HealthCheck:
        """
        Check health of a single service.

        Args:
            service: Service name
            url: Service URL to test

        Returns:
            HealthCheck result
        """
        import time

        start_time = time.time()

        try:
            result = subprocess.run(
                ["curl", "-fsSL", "--connect-timeout", "5", "--max-time", "10", url],
                capture_output=True,
                timeout=15,
            )

            response_time = (time.time() - start_time) * 1000  # ms

            if result.returncode == 0:
                if response_time < 1000:
                    status = HealthStatus.HEALTHY
                elif response_time < 3000:
                    status = HealthStatus.DEGRADED
                else:
                    status = HealthStatus.UNHEALTHY

                return HealthCheck(
                    service=service,
                    status=status,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                )
            else:
                return HealthCheck(
                    service=service,
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    last_check=datetime.now(),
                    error_message=result.stderr.decode() if result.stderr else "Connection failed",
                )

        except Exception as e:
            return HealthCheck(
                service=service,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=0,
                last_check=datetime.now(),
                error_message=str(e),
            )

    def check_all(self) -> Dict[str, HealthCheck]:
        """
        Check health of all services.

        Returns:
            Dictionary of service name to HealthCheck
        """
        results = {}

        for service, url in self.services.items():
            result = self.check_service(service, url)
            results[service] = result
            self.last_results[service] = result

        return results

    def get_summary(self) -> Dict[str, object]:
        """Get health check summary."""
        if not self.last_results:
            self.check_all()

        healthy = sum(1 for r in self.last_results.values() if r.status == HealthStatus.HEALTHY)
        degraded = sum(1 for r in self.last_results.values() if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in self.last_results.values() if r.status == HealthStatus.UNHEALTHY)

        return {
            "total_services": len(self.last_results),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "overall_status": self._calculate_overall_status(healthy, degraded, unhealthy),
        }

    def _calculate_overall_status(
        self, healthy: int, degraded: int, unhealthy: int
    ) -> HealthStatus:
        """Calculate overall system health status."""
        total = healthy + degraded + unhealthy

        if unhealthy > 0:
            return HealthStatus.UNHEALTHY
        elif degraded > total / 2:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
