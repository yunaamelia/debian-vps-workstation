"""
WireGuard module for VPN server.

Handles:
- WireGuard installation
- Server configuration
- Key generation
- Client configuration generation
"""

from pathlib import Path

from configurator.modules.base import ConfigurationModule
from configurator.utils.network import get_public_ip


class WireGuardModule(ConfigurationModule):
    """
    WireGuard VPN server module.

    Sets up a WireGuard VPN server for secure remote access.
    """

    name = "WireGuard"
    description = "WireGuard VPN server"
    depends_on = ["system", "security"]
    priority = 70
    mandatory = False

    def validate(self) -> bool:
        """Validate WireGuard prerequisites."""
        # Check if WireGuard is already installed
        if self.command_exists("wg"):
            result = self.run("wg --version", check=False)
            self.logger.info(f"  Found existing WireGuard: {result.stdout.strip()}")

        return True

    def configure(self) -> bool:
        """Install and configure WireGuard."""
        self.logger.info("Installing WireGuard VPN...")

        # 1. Install WireGuard
        self._install_wireguard()

        # 2. Generate keys
        self._generate_keys()

        # 3. Configure server
        self._configure_server()

        # 4. Enable IP forwarding
        self._enable_ip_forwarding()

        # 5. Configure firewall
        self._configure_firewall()

        # 6. Start service
        self._start_service()

        # 7. Generate sample client config
        self._generate_client_config()

        self.logger.info("✓ WireGuard VPN installed")
        return True

    def verify(self) -> bool:
        """Verify WireGuard installation."""
        checks_passed = True

        # Check wg command
        if not self.command_exists("wg"):
            self.logger.error("WireGuard not installed!")
            checks_passed = False
        else:
            self.logger.info("✓ WireGuard installed")

        # Check service
        if self.is_service_active("wg-quick@wg0"):
            self.logger.info("✓ WireGuard service is running")
        else:
            self.logger.warning("WireGuard service is not running")

        return checks_passed

    def _install_wireguard(self):
        """Install WireGuard packages."""
        self.logger.info("Installing WireGuard...")
        self.install_packages(["wireguard", "wireguard-tools"])

    def _generate_keys(self):
        """Generate server keys."""
        self.logger.info("Generating keys...")

        wg_dir = Path("/etc/wireguard")
        wg_dir.mkdir(mode=0o700, exist_ok=True)

        # Generate server private key
        result = self.run("wg genkey", check=True)
        server_private = result.stdout.strip()

        # Generate server public key
        result = self.run(f"echo '{server_private}' | wg pubkey", check=True)
        server_public = result.stdout.strip()

        # Save keys
        (wg_dir / "server_private.key").write_text(server_private)
        (wg_dir / "server_public.key").write_text(server_public)

        self.run("chmod 600 /etc/wireguard/server_private.key", check=True)

        self.state["server_private"] = server_private
        self.state["server_public"] = server_public

        self.logger.info("✓ Keys generated")

    def _configure_server(self):
        """Configure WireGuard server."""
        self.logger.info("Configuring server...")

        port = self.get_config("port", 51820)
        self.get_config("subnet", "10.0.0.0/24")
        self.get_config("server_ip", "10.0.0.1")

        # Get network interface
        result = self.run(
            "ip route | grep default | awk '{print $5}' | head -1",
            check=True,
        )
        interface = result.stdout.strip() or "eth0"

        server_private = (
            self.state.get("server_private")
            or Path("/etc/wireguard/server_private.key").read_text().strip()
        )

        config = """[Interface]
PrivateKey = {server_private}
Address = {server_ip}/24
ListenPort = {port}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o {interface} -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o {interface} -j MASQUERADE

# Add peers below
# [Peer]
# PublicKey = <client_public_key>
# AllowedIPs = 10.0.0.2/32
"""

        config_path = Path("/etc/wireguard/wg0.conf")
        config_path.write_text(config)
        self.run("chmod 600 /etc/wireguard/wg0.conf", check=True)

        self.state["port"] = port
        self.state["interface"] = interface

        self.logger.info("✓ Server configured")

    def _enable_ip_forwarding(self):
        """Enable IP forwarding for VPN routing."""
        self.logger.info("Enabling IP forwarding...")

        # Enable immediately
        self.run("sysctl -w net.ipv4.ip_forward=1", check=True)

        # Make persistent
        sysctl_conf = "/etc/sysctl.d/99-wireguard.conf"
        Path(sysctl_conf).write_text("net.ipv4.ip_forward=1\n")

        self.logger.info("✓ IP forwarding enabled")

    def _configure_firewall(self):
        """Configure UFW for WireGuard."""
        port = self.state.get("port", 51820)

        self.logger.info(f"Opening UDP port {port}...")

        self.run(f"ufw allow {port}/udp comment 'WireGuard VPN'", check=False)

        self.logger.info("✓ Firewall configured")

    def _start_service(self):
        """Start WireGuard service."""
        self.logger.info("Starting WireGuard...")

        self.enable_service("wg-quick@wg0")

        self.logger.info("✓ WireGuard started")

    def _generate_client_config(self):
        """Generate a sample client configuration."""
        self.logger.info("Generating sample client configuration...")

        # Generate client keys
        result = self.run("wg genkey", check=True)
        client_private = result.stdout.strip()

        result = self.run(f"echo '{client_private}' | wg pubkey", check=True)
        client_public = result.stdout.strip()

        # Get server info
        server_public = (
            self.state.get("server_public")
            or Path("/etc/wireguard/server_public.key").read_text().strip()
        )
        self.state.get("port", 51820)

        # Get public IP
        get_public_ip() or "YOUR_SERVER_IP"

        client_config = """[Interface]
PrivateKey = {client_private}
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = {server_public}
Endpoint = {public_ip}:{port}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

        # Save client config
        client_dir = Path("/etc/wireguard/clients")
        client_dir.mkdir(exist_ok=True)

        (client_dir / "client1.conf").write_text(client_config)
        (client_dir / "client1.key").write_text(client_private)
        (client_dir / "client1.pub").write_text(client_public)

        self.logger.info("✓ Sample client configuration created")
        self.logger.info("  Client config: /etc/wireguard/clients/client1.conf")
        self.logger.info(
            f"  Add peer to server: wg set wg0 peer {client_public} allowed-ips 10.0.0.2/32"
        )
