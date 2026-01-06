"""
Docker module for container development.

Handles:
- Docker Engine installation
- Docker Compose plugin
- Docker daemon configuration
- User permissions
"""

import json
import os

from configurator.modules.base import ConfigurationModule
from configurator.utils.file import write_file


class DockerModule(ConfigurationModule):
    """
    Docker installation module.

    Installs Docker Engine and Docker Compose from
    the official Docker repository.
    """

    name = "Docker"
    description = "Docker Engine and Docker Compose"
    depends_on = ["system", "security"]
    priority = 50
    mandatory = False

    def validate(self) -> bool:
        """Validate Docker prerequisites."""
        # Check if Docker is already installed
        if self.command_exists("docker"):
            result = self.run("docker --version", check=False)
            self.logger.info(f"  Found existing Docker: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure Docker."""
        self.logger.info("Installing Docker...")

        # 1. Add Docker repository
        self._add_docker_repository()

        # 2. Install Docker packages
        self._install_docker()

        # 3. Configure Docker daemon
        self._configure_daemon()

        # 4. Configure user permissions
        self._configure_permissions()

        # 5. Start services
        self._start_services()

        # 6. Verify installation
        self._verify_docker()

        self.logger.info("✓ Docker installed and configured")
        return True

    def verify(self) -> bool:
        """Verify Docker installation."""
        checks_passed = True

        # Check Docker service
        if not self.is_service_active("docker"):
            self.logger.error("Docker service is not running!")
            checks_passed = False
        else:
            self.logger.info("✓ Docker service is running")

        # Check docker command
        result = self.run("docker --version", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("docker command not found!")
            checks_passed = False

        # Check docker compose
        result = self.run("docker compose version", check=False)
        if result.success:
            self.logger.info(f"✓ Docker Compose: {result.stdout.strip()}")
        else:
            # Try old docker-compose
            result = self.run("docker-compose --version", check=False)
            if result.success:
                self.logger.info(f"✓ {result.stdout.strip()}")

        return checks_passed

    def _add_docker_repository(self):
        """Add Docker's official GPG key and repository."""
        self.logger.info("Adding Docker repository...")

        # Remove conflicting docker.sources if it exists (prevents duplicate target warnings)
        if os.path.exists("/etc/apt/sources.list.d/docker.sources"):
            os.remove("/etc/apt/sources.list.d/docker.sources")

        # Create keyrings directory
        self.run("install -m 0755 -d /etc/apt/keyrings", check=True)

        # Download Docker's GPG key
        self.run(
            "curl -fsSL https://download.docker.com/linux/debian/gpg "
            "-o /etc/apt/keyrings/docker.asc",
            check=True,
        )

        # Make key readable
        self.run("chmod a+r /etc/apt/keyrings/docker.asc", check=True)

        # Get architecture
        result = self.run("dpkg --print-architecture", check=True)
        arch = result.stdout.strip()

        # Get version codename
        result = self.run(
            "grep VERSION_CODENAME /etc/os-release | cut -d= -f2",
            check=True,
        )
        codename = result.stdout.strip() or "trixie"

        # Add repository
        repo_line = (
            f"deb [arch={arch} signed-by=/etc/apt/keyrings/docker.asc] "
            f"https://download.docker.com/linux/debian {codename} stable"
        )

        write_file("/etc/apt/sources.list.d/docker.list", repo_line + "\n")

        # Update package lists
        self.run("apt-get update", check=True)

        self.logger.info("✓ Docker repository added")

    def _install_docker(self):
        """Install Docker packages."""
        self.logger.info("Installing Docker packages...")

        packages = [
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ]

        self.install_packages(packages, update_cache=False)

    def _configure_daemon(self):
        """Configure Docker daemon."""
        self.logger.info("Configuring Docker daemon...")

        daemon_config = {
            "log-driver": "json-file",
            "log-opts": {
                "max-size": "10m",
                "max-file": "3",
            },
            "storage-driver": "overlay2",
            "live-restore": True,
        }

        # Create docker config directory
        self.run("mkdir -p /etc/docker", check=False)

        # Write daemon.json
        config_json = json.dumps(daemon_config, indent=2)
        write_file("/etc/docker/daemon.json", config_json)

        self.logger.info("✓ Docker daemon configured")

    def _configure_permissions(self):
        """Configure Docker permissions for users."""
        self.logger.info("Configuring Docker permissions...")

        # Add current user to docker group
        import os

        current_user = os.environ.get("SUDO_USER", "root")

        self.run(f"usermod -aG docker {current_user}", check=False)

        # Note: User needs to log out and in for group change to take effect
        self.logger.info(f"  Added {current_user} to docker group")
        self.logger.info("  Note: Log out and back in for group change to take effect")

    def _start_services(self):
        """Start Docker services."""
        self.logger.info("Starting Docker services...")

        self.enable_service("docker")
        self.enable_service("containerd")

    def _verify_docker(self):
        """Run Docker hello-world to verify installation."""
        self.logger.info("Verifying Docker installation...")

        result = self.run("docker run --rm hello-world", check=False)

        if "Hello from Docker!" in result.stdout:
            self.logger.info("✓ Docker is working correctly")
        else:
            self.logger.warning("Docker verification may have issues")
            self.logger.debug(result.output)
