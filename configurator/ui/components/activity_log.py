from textual.app import ComposeResult
from textual.widgets import Log, Static


class ActivityLog(Static):
    """Widget for scrolling activity log."""

    DEFAULT_CSS = """
    ActivityLog {
        height: 100%;
        border: solid green;
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Log(highlight=True, id="log-view")

    def add_line(self, line: str) -> None:
        try:
            log = self.query_one("#log-view", Log)
            log.write_line(line)
        except Exception:
            pass
