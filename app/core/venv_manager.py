"""Virtual environment management module."""

import sys
import os
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass

from PyQt5.QtCore import QThread, pyqtSignal

from app.core.logger import get_logger
from app.utils.shell import run_command, run_command_stream, ProcessResult


@dataclass
class VenvInfo:
    """Information about a virtual environment."""
    path: Path
    python_path: Path
    pip_path: Path
    exists: bool
    python_version: str = ""


class VenvWorker(QThread):
    """Worker thread for venv operations."""

    output_line = pyqtSignal(str)
    operation_finished = pyqtSignal(bool, str)  # success, message
    progress = pyqtSignal(str)  # status message

    def __init__(self, operation: str, venv_path: Path, requirements_path: Optional[Path] = None):
        super().__init__()
        self.operation = operation
        self.venv_path = venv_path
        self.requirements_path = requirements_path
        self.logger = get_logger()

    def run(self):
        """Execute the venv operation."""
        if self.operation == "create":
            self._create_venv()
        elif self.operation == "install":
            self._install_requirements()
        elif self.operation == "delete":
            self._delete_venv()

    def _create_venv(self):
        """Create a new virtual environment."""
        try:
            self.progress.emit("Creating virtual environment...")
            self.output_line.emit(f"Creating venv at: {self.venv_path}")

            cmd = [sys.executable, "-m", "venv", str(self.venv_path)]

            def output_callback(line: str):
                self.output_line.emit(line)

            result = run_command_stream(cmd, output_callback)

            if result.success:
                self.logger.success("Virtual environment created successfully")
                self.operation_finished.emit(True, "Virtual environment created")
            else:
                self.logger.error(f"Failed to create venv: {result.stderr}")
                self.operation_finished.emit(False, f"Failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Venv creation error: {str(e)}")
            self.operation_finished.emit(False, str(e))

    def _install_requirements(self):
        """Install requirements in the virtual environment."""
        try:
            if not self.requirements_path or not self.requirements_path.exists():
                self.operation_finished.emit(False, "Requirements file not found")
                return

            self.progress.emit("Installing requirements...")

            # Get pip path
            if sys.platform == 'win32':
                pip_path = self.venv_path / "Scripts" / "pip.exe"
            else:
                pip_path = self.venv_path / "bin" / "pip"

            if not pip_path.exists():
                self.operation_finished.emit(False, "Pip not found in virtual environment")
                return

            cmd = [str(pip_path), "install", "-r", str(self.requirements_path)]

            def output_callback(line: str):
                self.output_line.emit(line)

            result = run_command_stream(cmd, output_callback)

            if result.success:
                self.logger.success("Requirements installed successfully")
                self.operation_finished.emit(True, "Requirements installed")
            else:
                self.logger.error(f"Failed to install requirements: {result.stderr}")
                self.operation_finished.emit(False, f"Failed: {result.stderr}")

        except Exception as e:
            self.logger.error(f"Requirements installation error: {str(e)}")
            self.operation_finished.emit(False, str(e))

    def _delete_venv(self):
        """Delete the virtual environment."""
        import shutil
        try:
            self.progress.emit("Deleting virtual environment...")

            if self.venv_path.exists():
                shutil.rmtree(self.venv_path)
                self.logger.success("Virtual environment deleted")
                self.operation_finished.emit(True, "Virtual environment deleted")
            else:
                self.operation_finished.emit(False, "Virtual environment not found")

        except Exception as e:
            self.logger.error(f"Venv deletion error: {str(e)}")
            self.operation_finished.emit(False, str(e))


class VenvManager:
    """Manages virtual environments for builds."""

    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home() / ".pyinstaller_builder" / "venvs"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger()
        self.current_worker: Optional[VenvWorker] = None

    def get_venv_info(self, name: str) -> VenvInfo:
        """Get information about a virtual environment."""
        venv_path = self.base_path / name

        if sys.platform == 'win32':
            python_path = venv_path / "Scripts" / "python.exe"
            pip_path = venv_path / "Scripts" / "pip.exe"
        else:
            python_path = venv_path / "bin" / "python"
            pip_path = venv_path / "bin" / "pip"

        exists = venv_path.exists() and python_path.exists()

        python_version = ""
        if exists:
            result = run_command([str(python_path), "--version"])
            if result.success:
                python_version = result.stdout.strip()

        return VenvInfo(
            path=venv_path,
            python_path=python_path,
            pip_path=pip_path,
            exists=exists,
            python_version=python_version
        )

    def create_venv(
        self,
        name: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> VenvWorker:
        """Create a new virtual environment."""
        venv_path = self.base_path / name

        self.current_worker = VenvWorker("create", venv_path)

        if on_output:
            self.current_worker.output_line.connect(on_output)
        if on_finished:
            self.current_worker.operation_finished.connect(on_finished)
        if on_progress:
            self.current_worker.progress.connect(on_progress)

        self.current_worker.start()
        return self.current_worker

    def install_requirements(
        self,
        name: str,
        requirements_path: Path,
        on_output: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[bool, str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> VenvWorker:
        """Install requirements in a virtual environment."""
        venv_path = self.base_path / name

        self.current_worker = VenvWorker("install", venv_path, requirements_path)

        if on_output:
            self.current_worker.output_line.connect(on_output)
        if on_finished:
            self.current_worker.operation_finished.connect(on_finished)
        if on_progress:
            self.current_worker.progress.connect(on_progress)

        self.current_worker.start()
        return self.current_worker

    def delete_venv(
        self,
        name: str,
        on_finished: Optional[Callable[[bool, str], None]] = None
    ) -> VenvWorker:
        """Delete a virtual environment."""
        venv_path = self.base_path / name

        self.current_worker = VenvWorker("delete", venv_path)

        if on_finished:
            self.current_worker.operation_finished.connect(on_finished)

        self.current_worker.start()
        return self.current_worker

    def list_venvs(self) -> List[VenvInfo]:
        """List all virtual environments."""
        venvs = []
        if self.base_path.exists():
            for item in self.base_path.iterdir():
                if item.is_dir():
                    venvs.append(self.get_venv_info(item.name))
        return venvs

    def get_python_interpreters(self) -> List[str]:
        """Get list of available Python interpreters."""
        interpreters = [sys.executable]

        # Add venv interpreters
        for venv in self.list_venvs():
            if venv.exists:
                interpreters.append(str(venv.python_path))

        return interpreters
