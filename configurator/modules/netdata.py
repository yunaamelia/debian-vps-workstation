"""
Netdata module for system monitoring.

Handles:
- Netdata installation
- Basic configuration
- Dashboard access
"""

from configurator.modules.base import ConfigurationModule


class NetdataModule(ConfigurationModule):
    """
    Netdata real-time monitoring module.

    Netdata provides beautiful real-time monitoring dashboards
    for system metrics, applications, and more.
    """

    name = "Netdata"
    description = "Real-time performance monitoring"
    depends_on = ["system"]
    priority = 80
    mandatory = False

    def validate(self) -> bool:
        """Validate Netdata prerequisites."""
        # Check if Netdata is already installed
        if self.command_exists("netdata"):
            self.logger.info("  Netdata is already installed")

        return True

    def configure(self) -> bool:
        """Install and configure Netdata."""
        self.logger.info("Installing Netdata...")

        # 1. Install Netdata
        self._install_netdata()

        # 2. Configure
        self._configure_netdata()

        # 3. Configure firewall (if needed)
        self._configure_firewall()

        # 4. Start service
        self._start_service()

        self.logger.info("✓ Netdata installed")
        return True

    def verify(self) -> bool:
        """Verify Netdata installation."""
        checks_passed = True

        # Check service
        if self.is_service_active("netdata"):
            self.logger.info("✓ Netdata is running")
        else:
            self.logger.error("Netdata is not running!")
            checks_passed = False

        # Check port
        result = self.run("ss -tlnp | grep :19999", check=False)
        if result.success:
            self.logger.info("✓ Netdata dashboard available on port 19999")
        else:
            self.logger.warning("Netdata port 19999 not listening")

        return checks_passed

    def _install_netdata(self):
        """Install Netdata using kickstart script."""
        self.logger.info("Installing Netdata...")

        # Use the official kickstart script
        self.run(
            "curl -fsSL https://get.netdata.cloud/kickstart.sh | "
            "bash -s -- --stable-channel --disable-telemetry --non-interactive",
            check=True,
        )

        self.logger.info("✓ Netdata installed")

    def _configure_netdata(self):
        """Configure Netdata settings."""
        self.logger.info("Configuring Netdata...")

        # Default configuration is usually fine
        # But we can customize if needed

        bind_to = self.get_config("bind_to", "localhost")
        self.get_config("port", 19999)

        # If we want to expose to network
        if bind_to != "localhost":
            config_path = "/etc/netdata/netdata.conf"

            # Create minimal config override
            config = """[web]
    bind to = {bind_to}
    default port = {port}
"""

            with open(config_path, "a") as f:
                f.write(config)

        self.logger.info("✓ Netdata configured")

    def _configure_firewall(self):
        """Configure firewall for Netdata access."""
        bind_to = self.get_config("bind_to", "localhost")
        port = self.get_config("port", 19999)

        # Only open firewall if not bound to localhost
        if bind_to not in ("localhost", "127.0.0.1"):
            self.logger.info(f"Opening port {port}...")
            self.run(f"ufw allow {port}/tcp comment 'Netdata'", check=False)
        else:
            self.logger.info("  Netdata is bound to localhost only")
            self.logger.info("  Use SSH tunnel to access: ssh -L 19999:localhost:19999 user@server")

    def _start_service(self):
        """Start Netdata service."""
        self.logger.info("Starting Netdata...")

        self.enable_service("netdata")

        port = self.get_config("port", 19999)
        self.logger.info(f"✓ Netdata started on port {port}")
        self.logger.info(f"  Access at: http://localhost:{port}")
