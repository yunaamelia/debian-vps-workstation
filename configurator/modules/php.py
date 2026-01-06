"""
PHP module for PHP development environment.

Handles:
- PHP installation
- Composer package manager
- Common extensions
"""

from configurator.modules.base import ConfigurationModule


class PHPModule(ConfigurationModule):
    """
    PHP development environment module.
    """

    name = "PHP"
    description = "Install PHP development environment"
    priority = 45
    mandatory = False

    # Common PHP extensions
    PHP_EXTENSIONS = [
        "cli",
        "common",
        "curl",
        "mbstring",
        "xml",
        "zip",
        "gd",
        "mysql",
        "pgsql",
        "sqlite3",
        "redis",
        "intl",
    ]

    def validate(self) -> bool:
        """Validate PHP prerequisites."""
        # Check if PHP is already installed
        if self.command_exists("php"):
            result = self.run("php --version | head -1", check=False)
            self.logger.info(f"  Found existing PHP: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure PHP."""
        self.logger.info("Installing PHP...")

        # 1. Install PHP
        self._install_php()

        # 2. Install Composer
        self._install_composer()

        self.logger.info("✓ PHP development environment ready")
        return True

    def verify(self) -> bool:
        """Verify PHP installation."""
        checks_passed = True

        # Check php
        result = self.run("php --version | head -1", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.error("PHP not found!")
            checks_passed = False

        # Check composer
        result = self.run("composer --version 2>/dev/null | head -1", check=False)
        if result.success:
            self.logger.info(f"✓ {result.stdout.strip()}")
        else:
            self.logger.warning("Composer not found")

        return checks_passed

    def _install_php(self):
        """Install PHP and extensions."""
        version = self.get_config("version", "8.2")
        extensions = self.get_config("extensions", self.PHP_EXTENSIONS)

        # On Debian Testing/Unstable (like Trixie), hardcoded versions often break.
        # Check if versioned package exists, but generic 'php' is usually safer there.
        use_generic = False
        result = self.run(f"apt-cache show php{version}", check=False)
        
        if not result.success:
            use_generic = True
        
        # If version check passed, we might still want generic if specific extensions are missing
        # But let's trust the check for now, OR valid logic:
        # If we are on Trixie (Debian 13), force generic 'php' metapackage which points to latest (8.2/8.3/8.4)
        
        # Simpler logic: Try to install. If fails, try generic.
        # But install_packages raises exception.
        
        # Improved strategy: Just use generic packages for simplicity unless specific version requested
        # But class has defaults.
        
        if use_generic:
            packages = ["php", "php-cli", "php-common"]
            for ext in extensions:
                 packages.append(f"php-{ext}")
        else:
             # Just because php8.2 exists doesn't mean all extensions do (rare but possible)
             # Let's fallback to generic if we are in a "rolling" distro mood, but 
             # standard logic:
             packages = [f"php{version}"]
             for ext in extensions:
                 packages.append(f"php{version}-{ext}")
        
        try:
             self.install_packages(packages)
        except Exception:
             # If strict version failed, try fallback to generic
             self.logger.warning(f"Failed to install php{version} packages, trying generic 'php'...")
             packages = ["php", "php-cli", "php-common"]
             for ext in extensions:
                 packages.append(f"php-{ext}")
             self.install_packages(packages)

        self.logger.info(f"✓ PHP installed")

    def _install_composer(self):
        """Install Composer package manager."""
        self.logger.info("Installing Composer...")

        # Download installer
        self.run(
            "curl -sS https://getcomposer.org/installer -o /tmp/composer-setup.php",
            check=True,
        )

        # Verify installer (optional but recommended)
        # Install globally
        self.run(
            "php /tmp/composer-setup.php --install-dir=/usr/local/bin --filename=composer",
            check=True,
        )

        # Cleanup
        self.run("rm /tmp/composer-setup.php", check=False)

        self.logger.info("✓ Composer installed")
