"""
DevOps tools module.

Handles:
- Ansible
- Terraform
- kubectl
- Helm
- AWS CLI
- Cloud tools
"""

from pathlib import Path

from configurator.modules.base import ConfigurationModule


class DevOpsModule(ConfigurationModule):
    """
    DevOps tools installation module.

    Installs common DevOps and cloud infrastructure tools.
    """

    name = "DevOps Tools"
    description = "Kubectl, Helm, Terraform, Ansible"
    depends_on = ["system", "docker"]
    priority = 53
    mandatory = False

    def validate(self) -> bool:
        """Validate prerequisites."""
        return True

    def configure(self) -> bool:
        """Install DevOps tools."""
        self.logger.info("Installing DevOps tools...")

        # 1. Ansible
        if self.get_config("ansible", True):
            self._install_ansible()

        # 2. Terraform
        if self.get_config("terraform", True):
            self._install_terraform()

        # 3. kubectl
        if self.get_config("kubectl", True):
            self._install_kubectl()

        # 4. Helm
        if self.get_config("helm", True):
            self._install_helm()

        # 5. AWS CLI
        if self.get_config("awscli", False):
            self._install_awscli()

        self.logger.info("✓ DevOps tools installed")
        return True

    def verify(self) -> bool:
        """Verify installation."""
        checks_passed = True

        if self.get_config("ansible", True):
            if self.command_exists("ansible"):
                result = self.run("ansible --version | head -1", check=False)
                self.logger.info(f"✓ {result.stdout.strip()}")
            else:
                self.logger.warning("Ansible not found")

        if self.get_config("terraform", True):
            if self.command_exists("terraform"):
                result = self.run("terraform version | head -1", check=False)
                self.logger.info(f"✓ {result.stdout.strip()}")
            else:
                self.logger.warning("Terraform not found")

        if self.get_config("kubectl", True):
            if self.command_exists("kubectl"):
                result = self.run(
                    "kubectl version --client --short 2>/dev/null || kubectl version --client",
                    check=False,
                )
                self.logger.info("✓ kubectl installed")
            else:
                self.logger.warning("kubectl not found")

        if self.get_config("helm", True):
            if self.command_exists("helm"):
                result = self.run("helm version --short", check=False)
                self.logger.info(f"✓ Helm: {result.stdout.strip()}")
            else:
                self.logger.warning("Helm not found")

        return checks_passed

    def _install_ansible(self):
        """Install Ansible."""
        self.logger.info("Installing Ansible...")

        # Install via pip for latest version
        self.install_packages(["python3-pip", "python3-venv"])
        self.run("pip3 install --break-system-packages ansible ansible-lint", check=True)

        self.logger.info("✓ Ansible installed")

    def _install_terraform(self):
        """Install Terraform from HashiCorp."""
        self.logger.info("Installing Terraform...")

        # Add HashiCorp GPG key and repo
        self.run(
            "curl -fsSL https://apt.releases.hashicorp.com/gpg | "
            "gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg",
            check=True,
        )

        self.run(
            "echo 'deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] "
            "https://apt.releases.hashicorp.com bookworm main' | "
            "tee /etc/apt/sources.list.d/hashicorp.list",
            check=True,
        )

        self.run("apt-get update", check=True)
        self.install_packages(["terraform"], update_cache=False)

        self.logger.info("✓ Terraform installed")

    def _install_kubectl(self):
        """Install kubectl."""
        self.logger.info("Installing kubectl...")

        # Download latest stable version
        self.run(
            "curl -fsSL 'https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl' "
            "-o /usr/local/bin/kubectl",
            check=True,
        )

        self.run("chmod +x /usr/local/bin/kubectl", check=True)

        # Enable bash completion
        completion_file = Path("/etc/bash_completion.d/kubectl")
        if not completion_file.exists():
            self.run(
                "kubectl completion bash > /etc/bash_completion.d/kubectl 2>/dev/null || true",
                check=False,
            )

        self.logger.info("✓ kubectl installed")

    def _install_helm(self):
        """Install Helm."""
        self.logger.info("Installing Helm...")

        # Use official install script
        self.run(
            "curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",
            check=True,
        )

        # Enable bash completion
        completion_file = Path("/etc/bash_completion.d/helm")
        if not completion_file.exists():
            self.run(
                "helm completion bash > /etc/bash_completion.d/helm 2>/dev/null || true",
                check=False,
            )

        self.logger.info("✓ Helm installed")

    def _install_awscli(self):
        """Install AWS CLI v2."""
        self.logger.info("Installing AWS CLI...")

        # Download and install AWS CLI v2
        self.run(
            "curl -fsSL 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o /tmp/awscliv2.zip",
            check=True,
        )

        self.run("unzip -o /tmp/awscliv2.zip -d /tmp/", check=True)
        self.run("/tmp/aws/install --update", check=True)
        self.run("rm -rf /tmp/awscliv2.zip /tmp/aws", check=False)

        self.logger.info("✓ AWS CLI installed")
