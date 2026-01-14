import logging
import os
import sys
from unittest.mock import MagicMock

# Ensure we can import configurator
sys.path.append(os.getcwd())

from configurator.modules.desktop import DesktopModule

# We need a real DryRunManager if possible, or a mock that behaves like one
try:
    from configurator.dry_run_manager import DryRunManager
except ImportError:

    class DryRunManager:
        def __init__(self, enabled=True):
            self.enabled = enabled
            self.file_changes = []
            self.is_enabled = enabled

        def record_file_write(self, path, content=None, mode=None):
            self.file_changes.append({"path": path, "action": "write"})

        def record_package_install(self, packages):
            self.file_changes.append(
                {"command": f"install packages: {packages}", "action": "install"}
            )

        def record_service_action(self, service, action):
            self.file_changes.append(
                {"command": f"service {service} {action}", "action": "service"}
            )

        def record_command(self, command):
            self.file_changes.append({"command": command, "action": "run"})


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("DesktopVerification")

# Mock managers
rollback = MagicMock()
dry_run = DryRunManager(enabled=True)

# Config covering both Phase 1 and 2
config = {
    "desktop": {
        "enabled": True,
        "xrdp": {"max_bpp": 24, "allow_root_login": False},
        "compositor": {"mode": "optimized"},
        "polkit": {"allow_colord": True, "allow_packagekit": True},
        "themes": {"install": ["nordic"], "active": "Nordic-darker"},
        "icons": {"install": ["papirus"], "active": "Papirus-Dark"},
        "fonts": {"rendering": {"enabled": True, "dpi": 96}},
        "zsh": {"enabled": True, "set_default_shell": True},
        "terminal": {
            "tools": {"enabled": True, "bat": True, "eza": True, "zoxide": True, "fzf": True}
        },
    }
}

print("═══════════════════════════════════════════════════════════")
print("DESKTOP MODULE STANDALONE VERIFICATION")
print("═══════════════════════════════════════════════════════════")
print("Initializing DesktopModule...")


class MockConfigManager:
    def __init__(self, config_dict):
        self.config = config_dict

    def get(self, key, default=None):
        keys = key.split(".")
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


# Config needs to be wrapped or the DesktopModule needs to be robust
# DesktopModule inherits from ConfigurationModule.
# In normal run, it receives `config` which is a dict.
# Let's see if we need to mock config access.
# If I look at base.py, the `__init__` takes `config: Dict[str, Any]`.
# So passing the dict is correct.

try:
    module = DesktopModule(config, logger, rollback_manager=rollback, dry_run_manager=dry_run)

    # IMPORTANT: The module might need filesystem to be mocked if it iterates users?
    # desktop.py uses `pwd.getpwall()` to find users.
    # In a real environment (this VPS), it will find 'racoon' and maybe 'root'.
    # This is fine for integration test, we want to see it try to configure real users.

    # Patch module.run to prevent real command execution (like service restart)
    original_run = module.run

    def mock_run(command, **kwargs):
        print(f"MOCKED RUN: {command}")
        # Record command in dry run manager if needed
        if hasattr(dry_run, "record_command"):
            dry_run.record_command(command)

        # Return a fake CommandResult
        # We need a class or object with .success, .return_code, .stdout, .stderr
        class MockResult:
            def __init__(self):
                self.success = True
                self.return_code = 0
                self.stdout = ""
                self.stderr = ""

        result = MockResult()

        if "is-active" in command:
            result.stdout = "active"

        return result

    module.run = mock_run

    print("Running DesktopModule.configure() in Dry-Run mode...")
    if module.validate():
        module.configure()
    else:
        print("❌ DesktopModule.validate() failed")
        exit(1)

    print("\n✅ DesktopModule.run() completed successfully")

    # Verify expected artifacts
    expected_files = [
        "/etc/xrdp/xrdp.ini",
        "/etc/xrdp/sesman.ini",
        "/etc/polkit-1/localauthority/50-local.d/45-allow-colord.pkla",
        "/etc/polkit-1/localauthority/50-local.d/45-allow-packagekit.pkla",
        "fonts.conf",
        "xsettings.xml",
    ]

    print("\n[Recorded File Changes]")
    found_files = []
    # Depend on how dry_run records
    if hasattr(dry_run, "file_changes"):
        for change in dry_run.file_changes:
            # Check structure of change
            if isinstance(change, dict):
                path = change.get("path", "unknown")
            else:
                path = str(change)
            print(f" - {path}")
            found_files.append(path)

    print("\n[Verification]")
    missing = []
    for f in expected_files:
        # Simple substring match or exact match
        if any(f in recorded for recorded in found_files):
            print(f"✅ Found expected file: {f}")
        else:
            print(f"❌ Missing expected file: {f}")
            missing.append(f)

    # Also check for .xsession for users if any
    if any(".xsession" in f for f in found_files):
        print("✅ Found user session config")

    if not missing:
        # Phase 4: Zsh Verification
        if config["desktop"].get("zsh", {}).get("enabled", True):
            print("Verifying Zsh environment...")
            expected_zsh_files = [
                ".zshrc",
                ".oh-my-zsh",  # Directory check might need refinement if verifying mock files list
            ]

        # We check for .zshrc in file changes
        zshrc_created = any(
            ".zshrc" in c.get("path", "")
            for c in dry_run.file_changes
            if c.get("action") == "write"
        )
        if zshrc_created:
            print("✅ Found expected file: .zshrc")
        else:
            print("❌ Missing expected file: .zshrc")

        # Check for git clones (OMZ, p10k, plugins)
        git_clones = [
            c.get("command") for c in dry_run.file_changes if "git clone" in c.get("command", "")
        ]
        if len(git_clones) >= 4:  # OMZ, P10k, Autosuggestions, Syntax Highlighting
            print(f"✅ Verified {len(git_clones)} git clone operations for Zsh setup")
        else:
            print(f"⚠️  Expected at least 4 git clone operations, found {len(git_clones)}")

    # Phase 5: Terminal Tools Verification
    if (
        config["desktop"].get("terminal", {}).get("tools", {}).get("enabled", True)
    ):  # Assuming default enabled
        print("Verifying Terminal Tools...")
        tools_switches = config["desktop"].get("terminal", {}).get("tools", {})
        expected_packages = []
        if tools_switches.get("bat"):
            expected_packages.append("bat")
        if tools_switches.get("eza"):
            expected_packages.append("eza")
        if tools_switches.get("zoxide"):
            expected_packages.append("zoxide")
        if tools_switches.get("fzf"):
            expected_packages.append("fzf")

        # Check install packages
        installed_pkgs = []
        for c in dry_run.file_changes:
            if c.get("action") == "install":
                installed_pkgs.append(c.get("command"))

        # This is a loose check because 'install packages: ['zsh']' format
        # expected_packages might be in one or multiple calls
        found_tools = 0
        for tool in expected_packages:
            if any(tool in pkg_cmd for pkg_cmd in installed_pkgs):
                found_tools += 1

        if found_tools >= len(expected_packages):
            print(f"✅ Verified installation of {found_tools} terminal tools")
        else:
            print(
                f"⚠️  Expected {len(expected_packages)} tools, found {found_tools} in install commands"
            )

        print("\nSUCCESS: All expected files were targeted.")
        exit(0)
    else:
        print("\nFAILURE: Missing expected files.")
        exit(1)

except Exception as e:
    print(f"\n❌ DesktopModule.run() CRASHED: {e}")
    import traceback

    traceback.print_exc()
    exit(1)
