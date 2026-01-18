from unittest.mock import MagicMock, Mock, patch

from configurator.core.reporter.rich_reporter import RichProgressReporter


def test_rich_reporter_creation():
    reporter = RichProgressReporter()
    assert reporter is not None


@patch("configurator.core.reporter.rich_reporter.Live")
def test_rich_reporter_start(mock_live):
    console = MagicMock()
    console.__enter__.return_value = console
    console.__exit__.return_value = None

    reporter = RichProgressReporter(console=console)
    # Mock progress to avoid issues
    reporter.progress = Mock()

    reporter.start("Test")
    assert console.print.called
    # We expect Live to be instantiated and started
    mock_live.assert_called()
    mock_live.return_value.start.assert_called_once()


def test_rich_reporter_update():
    console = Mock()
    reporter = RichProgressReporter(console=console)
    # Mock the internal progress object to check calls
    reporter.progress = Mock()

    # Must add a task first
    reporter.start_phase("Test Phase")
    reporter.update("message", True)

    # Verify update was called on progress object
    assert reporter.progress.update.called
    # Check that it was called with status
    args, kwargs = reporter.progress.update.call_args
    assert "status" in kwargs or len(args) > 1


def test_rich_reporter_summary():
    console = Mock()
    reporter = RichProgressReporter(console=console)
    reporter.show_summary({"mod1": True, "mod2": False})
    # Should print a table
    assert console.print.called
