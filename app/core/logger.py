"""Logging system with Qt signal support for real-time UI updates."""

import logging
from datetime import datetime
from typing import Optional
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class LogEmitter(QObject):
    """Qt signal emitter for log messages."""
    log_message = pyqtSignal(str, str)  # message, level
    build_output = pyqtSignal(str)  # raw build output


# Global emitter instance
_emitter: Optional[LogEmitter] = None


def get_emitter() -> LogEmitter:
    """Get or create the global log emitter."""
    global _emitter
    if _emitter is None:
        _emitter = LogEmitter()
    return _emitter


class AppLogger:
    """Application logger with UI signal support."""

    def __init__(self, name: str = "PyInstallerBuilder"):
        self.name = name
        self.emitter = get_emitter()
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Setup file-based logging."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _format_message(self, message: str, level: LogLevel) -> str:
        """Format a log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        return f"[{timestamp}] [{level.value}] {message}"

    def _emit(self, message: str, level: LogLevel):
        """Emit a log message through Qt signal."""
        formatted = self._format_message(message, level)
        self.emitter.log_message.emit(formatted, level.value)

    def debug(self, message: str):
        """Log a debug message."""
        self.logger.debug(message)
        self._emit(message, LogLevel.DEBUG)

    def info(self, message: str):
        """Log an info message."""
        self.logger.info(message)
        self._emit(message, LogLevel.INFO)

    def warning(self, message: str):
        """Log a warning message."""
        self.logger.warning(message)
        self._emit(message, LogLevel.WARNING)

    def error(self, message: str):
        """Log an error message."""
        self.logger.error(message)
        self._emit(message, LogLevel.ERROR)

    def success(self, message: str):
        """Log a success message."""
        self.logger.info(f"SUCCESS: {message}")
        self._emit(message, LogLevel.SUCCESS)

    def build_output(self, line: str):
        """Emit raw build output."""
        self.emitter.build_output.emit(line)


# Global logger instance
_app_logger: Optional[AppLogger] = None


def get_logger() -> AppLogger:
    """Get or create the global application logger."""
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger
