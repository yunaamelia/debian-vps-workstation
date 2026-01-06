"""
Command execution utilities with error handling.
"""

import shlex
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Union

from configurator.exceptions import ModuleExecutionError


@dataclass
class CommandResult:
    """Result of a command execution."""

    command: str
    return_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        """Check if command was successful."""
        return self.return_code == 0

    @property
    def output(self) -> str:
        """Get combined stdout and stderr."""
        return f"{self.stdout}\n{self.stderr}".strip()


def run_command(
    command: Union[str, List[str]],
    check: bool = True,
    capture_output: bool = True,
    shell: bool = False,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    timeout: Optional[int] = None,
    input_text: Optional[str] = None,
) -> CommandResult:
    """
    Run a shell command and return the result.

    Args:
        command: Command to run (string or list of arguments)
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout and stderr
        shell: Run command in shell
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        input_text: Input to send to stdin

    Returns:
        CommandResult with return code, stdout, and stderr

    Raises:
        ModuleExecutionError if check=True and command fails
    """
    # Convert string to list if not using shell
    cmd_list: Union[List[str], str]
    if isinstance(command, str) and not shell:
        cmd_list = shlex.split(command)
    else:
        cmd_list = command if isinstance(command, list) else command

    # Build command string for logging
    cmd_str = command if isinstance(command, str) else " ".join(command)

    try:
        result = subprocess.run(
            cmd_list,
            shell=shell,
            cwd=cwd,
            env=env,
            timeout=timeout,
            input=input_text,
            capture_output=capture_output,
            text=True,
        )

        cmd_result = CommandResult(
            command=cmd_str,
            return_code=result.returncode,
            stdout=result.stdout if capture_output else "",
            stderr=result.stderr if capture_output else "",
        )

        if check and result.returncode != 0:
            raise ModuleExecutionError(
                what=f"Command failed: {cmd_str}",
                why=f"Exit code: {result.returncode}\n{result.stderr.strip()}",
                how="Check the command output above for details. You may need to:\n"
                "1. Check if required packages are installed\n"
                "2. Verify you have the necessary permissions\n"
                "3. Check your internet connection",
            )

        return cmd_result

    except subprocess.TimeoutExpired:
        raise ModuleExecutionError(
            what=f"Command timed out: {cmd_str}",
            why=f"Command did not complete within {timeout} seconds",
            how="This might indicate a hung process or network issue. Try:\n"
            "1. Check your internet connection\n"
            "2. Increase the timeout if this is expected\n"
            "3. Run the command manually to debug",
        )
    except FileNotFoundError:
        raise ModuleExecutionError(
            what=f"Command not found: {cmd_str.split()[0]}",
            why="The command or program is not installed",
            how="Install the required package:\n" f"  sudo apt-get install {cmd_str.split()[0]}",
        )


def run_command_with_output(
    command: Union[str, List[str]],
    check: bool = True,
    shell: bool = False,
    cwd: Optional[str] = None,
) -> str:
    """
    Run a command and return just the stdout.

    This is a convenience wrapper around run_command for simple cases.

    Args:
        command: Command to run
        check: Raise exception on non-zero exit code
        shell: Run command in shell
        cwd: Working directory

    Returns:
        stdout from the command
    """
    result = run_command(command, check=check, shell=shell, cwd=cwd)
    return result.stdout.strip()


def command_exists(command: str) -> bool:
    """
    Check if a command exists on the system.

    Args:
        command: Command name to check

    Returns:
        True if command exists
    """
    result = run_command(f"which {command}", check=False)
    return result.success


def get_package_version(package: str) -> Optional[str]:
    """
    Get the installed version of a package.

    Args:
        package: Package name

    Returns:
        Version string or None if not installed
    """
    result = run_command(
        f"dpkg-query -W -f='${{Version}}' {package}",
        check=False,
        shell=True,
    )
    return result.stdout.strip() if result.success else None


def is_service_active(service: str) -> bool:
    """
    Check if a systemd service is active.

    Args:
        service: Service name

    Returns:
        True if service is active
    """
    result = run_command(f"systemctl is-active {service}", check=False)
    return result.stdout.strip() == "active"


def is_service_enabled(service: str) -> bool:
    """
    Check if a systemd service is enabled.

    Args:
        service: Service name

    Returns:
        True if service is enabled
    """
    result = run_command(f"systemctl is-enabled {service}", check=False)
    return result.stdout.strip() == "enabled"
