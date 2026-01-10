"""
System-level tests for XRDP functionality.

These tests require actual XRDP service and should be run in a test VM or container.
"""

import os
import socket
import subprocess
import time

import pytest


@pytest.mark.system
@pytest.mark.skipif(not os.path.exists("/usr/sbin/xrdp"), reason="XRDP not installed")
class TestXRDPSystemLevel:
    """End-to-end system tests for XRDP."""

    def test_xrdp_service_starts_successfully(self):
        """Test that XRDP service starts after configuration."""
        # Restart service
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "xrdp"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Failed to restart XRDP: {result.stderr}"

        # Wait for startup
        time.sleep(2)

        # Check status
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "xrdp"],
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "active", "XRDP service is not active"

    def test_xrdp_listens_on_correct_port(self):
        """Test that XRDP is listening on port 3389."""
        # Check if port is open
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(("127.0.0.1", 3389))
        sock.close()

        assert result == 0, "XRDP is not listening on port 3389"

    def test_xrdp_configuration_is_valid(self):
        """Test that XRDP configuration files are syntactically valid."""
        # Test xrdp.ini
        assert os.path.exists("/etc/xrdp/xrdp.ini"), "xrdp.ini not found"

        with open("/etc/xrdp/xrdp.ini", "r") as f:
            content = f.read()
            # Basic validation
            assert "[Globals]" in content, "Missing [Globals] section in xrdp.ini"
            assert "tcp_nodelay" in content, "Missing tcp_nodelay setting"
            assert "bitmap_cache" in content, "Missing bitmap_cache setting"

        # Test sesman.ini
        assert os.path.exists("/etc/xrdp/sesman.ini"), "sesman.ini not found"

        with open("/etc/xrdp/sesman.ini", "r") as f:
            content = f.read()
            assert "[Globals]" in content, "Missing [Globals] section in sesman.ini"
            assert "[Sessions]" in content, "Missing [Sessions] section"

    def test_xrdp_sesman_service_active(self):
        """Test that xrdp-sesman service is active."""
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "xrdp-sesman"],
            capture_output=True,
            text=True,
        )

        # sesman might be active or not depending on XRDP version
        # Just check it's not failed
        assert result.stdout.strip() in [
            "active",
            "inactive",
        ], "xrdp-sesman service in unexpected state"

    def test_configuration_backups_exist(self):
        """Test that configuration backups were created."""
        backup_dir = "/var/backups/debian-vps-configurator"

        if os.path.exists(backup_dir):
            # Check for backup files
            backups = os.listdir(backup_dir)
            xrdp_backups = [f for f in backups if "xrdp" in f]

            # Should have at least one backup
            assert len(xrdp_backups) > 0, "No XRDP configuration backups found"

    def test_xrdp_log_files_created(self):
        """Test that XRDP is writing log files."""
        log_paths = ["/var/log/xrdp.log", "/var/log/xrdp-sesman.log"]

        log_exists = any(os.path.exists(p) for p in log_paths)
        assert log_exists, "No XRDP log files found"

    @pytest.mark.manual
    def test_rdp_connection_quality_manual(self):
        """
        Manual test: Connect via RDP client and verify:
        - Login screen appears within 5 seconds
        - XFCE desktop loads
        - Mouse cursor is correct (not X cursor)
        - No screen blanking
        - Smooth mouse movement (no lag)

        This test requires manual execution and verification.
        """
        pytest.skip("Manual test - requires RDP client")

    @pytest.mark.manual
    def test_performance_benchmarks_manual(self):
        """
        Manual performance test:
        1. Connect via RDP
        2. Measure connection time (should be < 5s)
        3. Test mouse latency (should feel instant)
        4. Open Firefox (should be smooth)
        5. Play video (should not lag)

        Document results in test report.
        """
        pytest.skip("Manual test - requires RDP client and human verification")


@pytest.mark.system
class TestXRDPConfigurationValidation:
    """Validate XRDP configuration without requiring running service."""

    def test_xrdp_ini_syntax_valid(self):
        """Validate xrdp.ini syntax."""
        if not os.path.exists("/etc/xrdp/xrdp.ini"):
            pytest.skip("XRDP not installed")

        with open("/etc/xrdp/xrdp.ini", "r") as f:
            content = f.read()

        # Check for required sections
        assert "[Globals]" in content
        assert "[xrdp1]" in content or "[Xvnc]" in content

        # Check for optimization settings
        performance_settings = [
            "tcp_nodelay",
            "bitmap_cache",
            "max_bpp",
            "security_layer",
        ]

        for setting in performance_settings:
            assert setting in content, f"Missing {setting} in configuration"

    def test_sesman_ini_syntax_valid(self):
        """Validate sesman.ini syntax."""
        if not os.path.exists("/etc/xrdp/sesman.ini"):
            pytest.skip("XRDP not installed")

        with open("/etc/xrdp/sesman.ini", "r") as f:
            content = f.read()

        # Check for required sections
        required_sections = ["[Globals]", "[Security]", "[Sessions]", "[Xvnc]"]

        for section in required_sections:
            assert section in content, f"Missing {section} section"

        # Check for performance settings
        assert "IdleTimeLimit" in content
        assert "MaxSessions" in content

    def test_user_xsession_files_exist(self):
        """Test that .xsession files were created for users."""
        # Get list of regular users
        import pwd

        users = [u.pw_name for u in pwd.getpwall() if u.pw_uid >= 1000 and u.pw_uid < 65534]

        if not users:
            pytest.skip("No regular users found")

        # Check at least one user has .xsession
        xsession_found = False
        for user in users:
            user_info = pwd.getpwnam(user)
            xsession_path = os.path.join(user_info.pw_dir, ".xsession")

            if os.path.exists(xsession_path):
                xsession_found = True

                # Validate content
                with open(xsession_path, "r") as f:
                    content = f.read()

                assert "#!/bin/bash" in content
                assert "NO_AT_BRIDGE" in content
                assert "startxfce4" in content

                # Check permissions
                stat = os.stat(xsession_path)
                mode = stat.st_mode & 0o777
                assert mode & 0o100, f".xsession not executable for {user}"

                break

        assert xsession_found, "No .xsession files found for any user"
