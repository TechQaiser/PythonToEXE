"""PyInstaller build process manager."""

import sys
import os
from pathlib import Path
from typing import List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtCore import QThread, pyqtSignal

from app.core.config_manager import BuildConfig
from app.core.logger import get_logger
from app.utils.shell import run_command_stream, get_python_executable, open_folder


class BuildStatus(Enum):
    """Build status enumeration."""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BuildResult:
    """Result of a build operation."""
    status: BuildStatus
    output_path: Optional[Path] = None
    error_message: str = ""
    build_time: float = 0.0


class BuildWorker(QThread):
    """Worker thread for running PyInstaller builds."""

    # Signals
    output_line = pyqtSignal(str)
    build_finished = pyqtSignal(object)  # BuildResult
    status_changed = pyqtSignal(str)  # status message

    def __init__(self, config: BuildConfig, python_path: Optional[str] = None):
        super().__init__()
        self.config = config
        self.python_path = python_path or get_python_executable()
        self.logger = get_logger()
        self._cancelled = False

    def cancel(self):
        """Request cancellation of the build."""
        self._cancelled = True

    def _build_command(self) -> List[str]:
        """Build the PyInstaller command from config."""
        cmd = [self.python_path, "-m", "PyInstaller"]

        # Script path (required)
        script_path = self.config.script_path
        if not script_path:
            raise ValueError("Script path is required")

        # One file vs one directory
        if self.config.one_file:
            cmd.append("--onefile")
        else:
            cmd.append("--onedir")

        # Console mode
        if not self.config.console_mode:
            cmd.append("--noconsole")

        # Clean build (remove previous build cache)
        if self.config.clean_build:
            cmd.append("--clean")

        # Don't ask for confirmation to overwrite
        cmd.append("--noconfirm")

        # Output directory
        if self.config.output_dir:
            cmd.extend(["--distpath", self.config.output_dir])

        # Application name
        if self.config.app_name:
            cmd.extend(["--name", self.config.app_name])

        # Icon
        if self.config.icon_path and Path(self.config.icon_path).exists():
            cmd.extend(["--icon", self.config.icon_path])

        # Hidden imports
        for hidden_import in self.config.hidden_imports:
            if hidden_import.strip():
                cmd.extend(["--hidden-import", hidden_import.strip()])

        # Exclude modules
        for exclude_module in self.config.exclude_modules:
            if exclude_module.strip():
                cmd.extend(["--exclude-module", exclude_module.strip()])

        # Data files (handle OS-specific path separator)
        # PyInstaller uses ; on Windows and : on Linux/Mac
        path_sep = ';' if sys.platform == 'win32' else ':'
        for data_file in self.config.data_files:
            if data_file.strip():
                # Convert stored format (always ;) to OS-specific format
                normalized = data_file.strip().replace(';', path_sep)
                cmd.extend(["--add-data", normalized])

        # Additional arguments (user-provided raw args)
        if self.config.additional_args:
            additional = self.config.additional_args.split()
            cmd.extend(additional)

        # Finally, the script
        cmd.append(script_path)

        return cmd

    def run(self):
        """Execute the build process."""
        import time
        start_time = time.time()

        try:
            self.status_changed.emit("Preparing build...")
            self.logger.info("Starting PyInstaller build")

            # Build command
            cmd = self._build_command()
            self.logger.info(f"Command: {' '.join(cmd)}")
            self.output_line.emit(f">>> {' '.join(cmd)}\n")

            self.status_changed.emit("Building...")

            # Run the build
            def output_callback(line: str):
                if not self._cancelled:
                    self.output_line.emit(line)

            result = run_command_stream(
                cmd,
                output_callback=output_callback,
                cwd=Path(self.config.script_path).parent if self.config.script_path else None
            )

            build_time = time.time() - start_time

            if self._cancelled:
                self.build_finished.emit(BuildResult(
                    status=BuildStatus.CANCELLED,
                    build_time=build_time
                ))
                return

            if result.success:
                output_path = Path(self.config.output_dir) if self.config.output_dir else None
                self.logger.success(f"Build completed in {build_time:.1f}s")
                self.build_finished.emit(BuildResult(
                    status=BuildStatus.SUCCESS,
                    output_path=output_path,
                    build_time=build_time
                ))
            else:
                self.logger.error("Build failed")
                self.build_finished.emit(BuildResult(
                    status=BuildStatus.FAILED,
                    error_message=result.stderr or "Build failed",
                    build_time=build_time
                ))

        except Exception as e:
            build_time = time.time() - start_time
            self.logger.error(f"Build error: {str(e)}")
            self.build_finished.emit(BuildResult(
                status=BuildStatus.FAILED,
                error_message=str(e),
                build_time=build_time
            ))


class Builder:
    """High-level builder interface."""

    def __init__(self):
        self.logger = get_logger()
        self.current_worker: Optional[BuildWorker] = None

    def start_build(
        self,
        config: BuildConfig,
        on_output: Optional[Callable[[str], None]] = None,
        on_finished: Optional[Callable[[BuildResult], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
        python_path: Optional[str] = None
    ) -> BuildWorker:
        """Start a new build process."""
        if self.current_worker and self.current_worker.isRunning():
            raise RuntimeError("A build is already in progress")

        self.current_worker = BuildWorker(config, python_path)

        if on_output:
            self.current_worker.output_line.connect(on_output)
        if on_finished:
            self.current_worker.build_finished.connect(on_finished)
        if on_status:
            self.current_worker.status_changed.connect(on_status)

        self.current_worker.start()
        return self.current_worker

    def cancel_build(self):
        """Cancel the current build."""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.cancel()
            self.current_worker.terminate()
            self.current_worker.wait()

    def is_building(self) -> bool:
        """Check if a build is in progress."""
        return self.current_worker is not None and self.current_worker.isRunning()

    @staticmethod
    def open_output_folder(path: Path) -> bool:
        """Open the build output folder."""
        return open_folder(path)
