"""
CLI commands for monitoring and observability.

Adds commands:
- vps-configurator monitoring status
- vps-configurator monitoring metrics
- vps-configurator monitoring logs
- vps-configurator monitoring alerts
- vps-configurator monitoring circuit-breakers
"""

import json
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.group(name="monitoring")
def monitoring_group():
    """Monitoring and observability commands."""
    pass


@monitoring_group.command(name="status")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def status_command(output_json):
    """
    Show current system status.

    Displays circuit breakers, health checks, and resource usage.
    """
    try:
        import logging

        from configurator.core.health import HealthCheckService

        health_service = HealthCheckService(logging.getLogger())
        health_results = health_service.check_all()
        summary = health_service.get_summary()

        if output_json:
            output = {
                "overall_status": summary["overall_status"].value,
                "services": {
                    name: {
                        "status": check.status.value,
                        "response_time_ms": check.response_time_ms,
                        "error": check.error_message,
                    }
                    for name, check in health_results.items()
                },
                "summary": {
                    "total": summary["total_services"],
                    "healthy": summary["healthy"],
                    "degraded": summary["degraded"],
                    "unhealthy": summary["unhealthy"],
                },
            }
            console.print_json(json.dumps(output, indent=2))
        else:
            console.print("\n[bold cyan]System Health Status[/bold cyan]\n")

            status_color = {"healthy": "green", "degraded": "yellow", "unhealthy": "red"}.get(
                summary["overall_status"].value, "white"
            )

            console.print(
                Panel(
                    f"[{status_color}]{summary['overall_status'].value.upper()}[/{status_color}]",
                    title="Overall Status",
                    border_style=status_color,
                )
            )

            table = Table(title="Service Health", box=box.ROUNDED)
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Response Time", justify="right")
            table.add_column("Error", style="red")

            for name, check in health_results.items():
                status_icon = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
                    check.status.value, "❓"
                )

                table.add_row(
                    name,
                    f"{status_icon} {check.status.value}",
                    f"{check.response_time_ms:.0f}ms",
                    check.error_message or "-",
                )

            console.print(table)
            console.print(
                f"\n[dim]Total: {summary['total_services']} | "
                f"[green]Healthy: {summary['healthy']}[/green] | "
                f"[yellow]Degraded: {summary['degraded']}[/yellow] | "
                f"[red]Unhealthy: {summary['unhealthy']}[/red][/dim]\n"
            )

    except ImportError as e:
        console.print(f"[red]Error: Required module not available - {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@monitoring_group.command(name="metrics")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["prometheus", "json"]),
    default="prometheus",
    help="Output format",
)
@click.option("--output", "-o", type=click.Path(), help="Output file (default: stdout)")
def metrics_command(output_format, output):
    """
    Export metrics.

    Formats:
    - prometheus: Prometheus text format
    - json: JSON format
    """
    try:
        from configurator.observability.metrics import get_metrics

        metrics = get_metrics()
        metrics.update_resource_metrics()

        if output_format == "prometheus":
            content = metrics.export_prometheus()
        else:
            content = metrics.export_json()

        if output:
            Path(output).parent.mkdir(parents=True, exist_ok=True)
            with open(output, "w") as f:
                f.write(content)
            console.print(f"[green]✓[/green] Metrics exported to: {output}")
        else:
            console.print(content)

    except ImportError:
        console.print("[red]Error: Observability module not available[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@monitoring_group.command(name="circuit-breakers")
def circuit_breakers_command():
    """Show circuit breaker status."""
    try:
        import logging

        from configurator.core.network import NetworkOperationWrapper

        config = {}
        try:
            from configurator.config import ConfigManager

            config_manager = ConfigManager()
            config = config_manager.config
        except Exception:
            pass

        wrapper = NetworkOperationWrapper(config, logging.getLogger())
        status = wrapper.get_circuit_breaker_status()

        if not status:
            console.print("[yellow]No circuit breakers configured[/yellow]")
            return

        console.print("\n[bold cyan]Circuit Breaker Status[/bold cyan]\n")

        table = Table(box=box.ROUNDED)
        table.add_column("Service", style="cyan")
        table.add_column("State", style="magenta")
        table.add_column("Failures", justify="right", style="red")
        table.add_column("Successes", justify="right", style="green")
        table.add_column("Total Calls", justify="right")
        table.add_column("Failure Rate", justify="right")

        for service_name, cb_status in status.items():
            state = cb_status["state"]
            failures = cb_status["failure_count"]
            successes = cb_status.get("success_count", 0)
            total = cb_status["total_calls"]

            state_icon = {"CLOSED": "🟢", "HALF_OPEN": "🟡", "OPEN": "🔴"}.get(state, "⚪")

            failure_rate = (failures / total * 100) if total > 0 else 0

            table.add_row(
                service_name,
                f"{state_icon} {state}",
                str(failures),
                str(successes),
                str(total),
                f"{failure_rate:.1f}%",
            )

        console.print(table)
        console.print()

    except ImportError:
        console.print("[red]Error: Network module not available[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@monitoring_group.command(name="logs")
@click.option("--tail", "-n", type=int, default=50, help="Number of lines to show")
@click.argument(
    "log_file", type=click.Path(exists=True), default="logs/install.log", required=False
)
def logs_command(tail, log_file):
    """View recent logs."""
    try:
        if not Path(log_file).exists():
            console.print(f"[yellow]Log file not found: {log_file}[/yellow]")
            return

        console.print(f"\n[dim]Last {tail} lines from {log_file}:[/dim]\n")

        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-tail:]:
                try:
                    entry = json.loads(line)
                    level_colors = {
                        "DEBUG": "dim",
                        "INFO": "cyan",
                        "WARNING": "yellow",
                        "ERROR": "red",
                        "CRITICAL": "bold red",
                    }
                    color = level_colors.get(entry.get("level"), "white")
                    console.print(
                        f"[{color}]{entry.get('timestamp')} [{entry.get('level')}] {entry.get('message')}[/{color}]"
                    )
                except json.JSONDecodeError:
                    console.print(line.strip())

        console.print()

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@monitoring_group.command(name="alerts")
@click.option(
    "--severity",
    type=click.Choice(["info", "warning", "error", "critical"]),
    help="Filter by severity",
)
@click.option("--hours", type=int, default=24, help="Show alerts from last N hours")
def alerts_command(severity, hours):
    """
    View recent alerts.
    """
    # Load alerts from file (if using file channel)
    alert_file = Path("/var/log/vps-configurator/alerts.log")

    if not alert_file.exists():
        console.print("[yellow]No alerts found[/yellow]")
        return

    # Parse alerts
    alerts = []
    with open(alert_file, "r") as f:
        for line in f:
            try:
                alert_data = json.loads(line)
                alerts.append(alert_data)
            except json.JSONDecodeError:
                continue

    # Filter by time and severity
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(hours=hours)

    filtered = []
    for alert in alerts:
        try:
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time > cutoff:
                if not severity or alert["severity"] == severity:
                    filtered.append(alert)
        except (ValueError, KeyError):
            continue

    if not filtered:
        console.print(f"[yellow]No alerts in the last {hours} hours[/yellow]")
        return

    # Display alerts
    console.print(f"\n[bold cyan]Alerts (Last {hours} hours)[/bold cyan]\n")

    for alert in sorted(filtered, key=lambda a: a["timestamp"], reverse=True):
        severity_colors = {
            "info": "cyan",
            "warning": "yellow",
            "error": "red",
            "critical": "bold red",
        }

        color = severity_colors.get(alert["severity"], "white")

        console.print(
            Panel(
                f"[{color}]{alert['title']}[/{color}]\n\n"
                f"{alert['message']}\n\n"
                f"[dim]Source: {alert['source']} | Time: {alert['timestamp']}[/dim]",
                title=f"[{color}]{alert['severity'].upper()}[/{color}]",
                border_style=color,
            )
        )


@monitoring_group.command(name="dashboard")
@click.option("--update-interval", type=float, default=2.0, help="Update interval in seconds")
def dashboard_command(update_interval):
    """
    Launch real-time monitoring dashboard.

    Displays live installation progress, metrics, and system status.
    Press Ctrl+C to exit.
    """
    try:
        from configurator.observability.dashboard import InstallationDashboard

        dashboard = InstallationDashboard()

        console.print("[cyan]Starting dashboard...[/cyan]")
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        dashboard.start()

        # Keep running until interrupted
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            dashboard.stop()
            console.print("\n[dim]Dashboard closed[/dim]")

    except ImportError:
        console.print("[red]Error: Rich library required for dashboard[/red]")
        console.print("[yellow]Install with: pip install rich[/yellow]")


# Register commands with main CLI
def register_monitoring_commands(cli):
    """Register monitoring commands with main CLI."""
    cli.add_command(monitoring_group)
