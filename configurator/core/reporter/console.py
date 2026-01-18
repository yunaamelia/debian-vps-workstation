from typing import Dict, Optional

from configurator.core.reporter.base import ReporterInterface


class ConsoleReporter(ReporterInterface):
    """Simple console reporter implementation."""

    def start(self, title: str = "Installation"):
        print(f"=== {title} ===")

    def start_phase(self, name: str, total_steps: int = 0):
        print(f"\n[PHASE] {name} ({total_steps} steps)")

    def update(self, message: str, success: bool = True, module: Optional[str] = None):
        prefix = f"[{module}] " if module else ""
        status = "OK" if success else "FAIL"
        print(f"  - {prefix}{message}... {status}")

    def update_progress(
        self,
        percent: int,
        current: Optional[int] = None,
        total: Optional[int] = None,
        module: Optional[str] = None,
    ):
        pass  # Simple console doesn't do progress bars to avoid log spam

    def complete_phase(self, success: bool = True, module: Optional[str] = None):
        prefix = f"[{module}] " if module else ""
        status = "COMPLETED" if success else "FAILED"
        print(f"[PHASE] {prefix}{status}")

    def show_summary(self, results: Dict[str, bool]):
        print("\n=== SUMMARY ===")
        for module, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {module}")

    def error(self, message: str):
        print(f"ERROR: {message}")

    def warning(self, message: str):
        print(f"WARNING: {message}")

    def info(self, message: str):
        print(f"INFO: {message}")

    def show_next_steps(self, reboot_required: bool = False, **kwargs):
        print("\nNext Steps:")
        if reboot_required:
            print("  * Reboot your system to apply all changes: sudo reboot")
        print("  * Verify installation: vps-configurator verify")
