"""
Java module for Java development environment.

Handles:
- OpenJDK installation
- Maven/Gradle build tools
- JAVA_HOME configuration
"""

from configurator.modules.base import ConfigurationModule


class JavaModule(ConfigurationModule):
    """
    Java development environment module.

    Installs OpenJDK and optionally Maven/Gradle.
    """

    name = "Java Development"
    description = "OpenJDK environment"
    depends_on = ["system"]
    priority = 44
    mandatory = False

    def validate(self) -> bool:
        """Validate Java prerequisites."""
        # Check if Java is already installed
        if self.command_exists("java"):
            result = self.run("java -version 2>&1 | head -1", check=False)
            self.logger.info(f"  Found existing Java: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure Java."""
        self.logger.info("Installing Java...")

        # 1. Install OpenJDK
        self._install_jdk()

        # 2. Install build tools
        self._install_build_tools()

        # 3. Configure environment
        self._configure_environment()

        self.logger.info("✓ Java development environment ready")
        return True

    def verify(self) -> bool:
        """Verify Java installation."""
        checks_passed = True

        # Check java
        result = self.run("java -version 2>&1 | head -1", check=False)
        if result.success and "openjdk" in result.stdout.lower():
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("Java not found!")
            checks_passed = False

        # Check javac
        result = self.run("javac -version 2>&1", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")

        return checks_passed

    def _install_jdk(self):
        """Install OpenJDK."""
        jdk_version = self.get_config("version", "default")

        if jdk_version == "default":
            jdk_package = "default-jdk"
            headless_package = "default-jdk-headless"
            self.logger.info("Installing default JDK...")
        else:
            jdk_package = f"openjdk-{jdk_version}-jdk"
            headless_package = f"openjdk-{jdk_version}-jdk-headless"
            self.logger.info(f"Installing OpenJDK {jdk_version}...")

        self.install_packages(
            [
                jdk_package,
                headless_package,
            ]
        )

        self.logger.info(f"✓ OpenJDK {jdk_version} installed")

    def _install_build_tools(self):
        """Install Maven and/or Gradle."""
        install_maven = self.get_config("maven", True)
        install_gradle = self.get_config("gradle", False)

        if install_maven:
            self.logger.info("Installing Maven...")
            self.install_packages(["maven"])
            self.logger.info("✓ Maven installed")

        if install_gradle:
            self.logger.info("Installing Gradle...")
            # Gradle is not in default repos, install via SDKMAN or download
            self._install_gradle()

    def _install_gradle(self):
        """Install Gradle from official source."""
        gradle_version = self.get_config("gradle_version", "8.5")

        # Download Gradle
        gradle_url = f"https://services.gradle.org/distributions/gradle-{gradle_version}-bin.zip"

        self.run("apt-get install -y unzip", check=False)
        self.run(f"curl -fsSL {gradle_url} -o /tmp/gradle.zip", check=True)
        self.run("unzip -d /opt /tmp/gradle.zip", check=True)
        self.run(f"ln -sf /opt/gradle-{gradle_version} /opt/gradle", check=True)
        self.run("ln -sf /opt/gradle/bin/gradle /usr/local/bin/gradle", check=True)
        self.run("rm /tmp/gradle.zip", check=False)

        self.logger.info(f"✓ Gradle {gradle_version} installed")

    def _configure_environment(self):
        """Configure JAVA_HOME."""
        jdk_version = self.get_config("version", "17")

        java_env = f"""
# Java environment
export JAVA_HOME=/usr/lib/jvm/java-{jdk_version}-openjdk-amd64
export PATH=$PATH:$JAVA_HOME/bin
"""

        # Add to /etc/profile.d
        with open("/etc/profile.d/java.sh", "w") as f:
            f.write(java_env)

        self.run("chmod +x /etc/profile.d/java.sh", check=False)

        self.logger.info("✓ JAVA_HOME configured")
