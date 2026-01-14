import os
import sys

# Add current dir to path - must be before local imports
sys.path.insert(0, os.getcwd())

import logging  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from configurator.modules.desktop import DesktopModule  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO)


def verify_fix():
    print("Verifying XRDP configuration fix...", flush=True)

    # Mock resources
    # FIX: Constructor takes config dict, not manager
    module = DesktopModule(config={})

    module.run = MagicMock()
    module.run.return_value.success = True
    module.get_config = MagicMock(
        side_effect=lambda k, d=None: {
            "desktop.xrdp.max_bpp": 24,
            "desktop.xrdp.security_layer": "tls",
            "desktop.xrdp.tcp_nodelay": True,
            "desktop.xrdp.bitmap_cache": True,
        }.get(k, d)
    )

    # Mock file writing to capture content
    written_files = {}

    def mock_write_file(path, content, **kwargs):
        written_files[path] = content
        print(f"Captured write to {path}", flush=True)

    # Patch modules
    with (
        patch("configurator.modules.desktop.write_file", side_effect=mock_write_file),
        patch("configurator.modules.desktop.backup_file"),
    ):
        # Run the optimization method
        # We need to bypass the dry_run check or ensure it's False
        module.dry_run = False
        module._optimize_xrdp_performance()

        # Verify xrdp.ini content
        xrdp_content = written_files.get("/etc/xrdp/xrdp.ini", "")

        issues = []
        if "max_bpp=24" not in xrdp_content:
            issues.append(f"FAIL: max_bpp=24 not found. Found: {xrdp_content.find('max_bpp')}")
        if "security_layer=tls" not in xrdp_content:
            issues.append("FAIL: security_layer=tls not found")
        if "{max_bpp}" in xrdp_content:
            issues.append("FAIL: Template variable {max_bpp} check failed (was not replaced)")

        # Verify sesman.ini content
        sesman_content = written_files.get("/etc/xrdp/sesman.ini", "")
        if "MaxSessions=10" not in sesman_content:
            issues.append("FAIL: MaxSessions=10 not found in sesman.ini")

        if issues:
            print("\n❌ Verification Failed:", flush=True)
            for issue in issues:
                print(f"  - {issue}", flush=True)
            sys.exit(1)
        else:
            print("\n✅ Verification Successful!", flush=True)
            print("  - max_bpp is correctly set to 24", flush=True)
            print("  - security_layer is correctly set to tls", flush=True)
            print("  - MaxSessions is 10", flush=True)
            print("  - Template variables are correctly substituted", flush=True)


verify_fix()
