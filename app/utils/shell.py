"""Shell utilities for subprocess execution."""

import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Callable, Any
from dataclasses import dataclass


@dataclass
class ProcessResult:
    """Result of a subprocess execution."""
    return_code: int
    stdout: str
    stderr: str
    success: bool


def get_python_executable() -> str:
    """Get the current Python executable path."""
    return sys.executable


def run_command(
    command: List[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    timeout: Optional[int] = None
) -> ProcessResult:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        return ProcessResult(
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            success=result.returncode == 0
        )
    except subprocess.TimeoutExpired as e:
        return ProcessResult(
            return_code=-1,
            stdout=e.stdout or "",
            stderr=f"Command timed out after {timeout} seconds",
            success=False
        )
    except Exception as e:
        return ProcessResult(
            return_code=-1,
            stdout="",
            stderr=str(e),
            success=False
        )


def run_command_stream(
    command: List[str],
    output_callback: Callable[[str], Any],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None
) -> ProcessResult:
    """Run a command with streaming output."""
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )

        stdout_lines = []
        for line in iter(process.stdout.readline, ''):
            if line:
                stdout_lines.append(line)
                output_callback(line.rstrip())

        process.wait()

        return ProcessResult(
            return_code=process.returncode,
            stdout=''.join(stdout_lines),
            stderr="",
            success=process.returncode == 0
        )
    except Exception as e:
        return ProcessResult(
            return_code=-1,
            stdout="",
            stderr=str(e),
            success=False
        )


def open_folder(path: Path) -> bool:
    """Open a folder in the system file explorer."""
    try:
        if sys.platform == 'win32':
            subprocess.run(['explorer', str(path)], check=False)
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)], check=False)
        else:
            subprocess.run(['xdg-open', str(path)], check=False)
        return True
    except Exception:
        return False
