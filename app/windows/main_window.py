"""Main application window for PyInstaller Advanced Builder."""

import sys
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog, QTextEdit,
    QComboBox, QCheckBox, QGroupBox, QTabWidget, QStatusBar,
    QMenuBar, QMenu, QAction, QToolBar, QSplitter, QFrame,
    QMessageBox, QInputDialog, QProgressBar, QDialog
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QTextCursor, QColor, QIcon

from app import __version__, __app_name__
from app.core.builder import Builder, BuildResult, BuildStatus
from app.core.config_manager import (
    get_config_manager, ConfigManager, BuildConfig, InstallerConfig
)
from app.core.logger import get_logger, get_emitter, LogLevel
from app.core.plugin_loader import get_plugin_loader
from app.utils.validators import (
    validate_python_script, validate_requirements_file,
    validate_icon_file, validate_output_directory
)
from app.utils.paths import get_default_output_dir
from app.utils.shell import open_folder
from app.windows.dialogs import (
    HiddenImportsDialog, DataFilesDialog, InstallerSettingsDialog,
    PresetsDialog, AboutDialog
)


class LogConsole(QTextEdit):
    """Custom text edit for displaying build logs with color coding."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setLineWrapMode(QTextEdit.NoWrap)

        # Color mapping for log levels
        self.colors = {
            "DEBUG": QColor("#888888"),
            "INFO": QColor("#FFFFFF"),
            "WARNING": QColor("#FFA500"),
            "ERROR": QColor("#FF4444"),
            "SUCCESS": QColor("#44FF44")
        }

    def append_log(self, message: str, level: str = "INFO"):
        """Append a log message with appropriate coloring."""
        color = self.colors.get(level, self.colors["INFO"])
        self.setTextColor(color)
        self.append(message)
        self.moveCursor(QTextCursor.End)

    def append_output(self, line: str):
        """Append raw build output."""
        # Detect errors in output
        lower_line = line.lower()
        if "error" in lower_line or "failed" in lower_line:
            self.setTextColor(self.colors["ERROR"])
        elif "warning" in lower_line:
            self.setTextColor(self.colors["WARNING"])
        elif "success" in lower_line or "completed" in lower_line:
            self.setTextColor(self.colors["SUCCESS"])
        else:
            self.setTextColor(self.colors["INFO"])

        self.append(line)
        self.moveCursor(QTextCursor.End)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.config_manager = get_config_manager()
        self.logger = get_logger()
        self.builder = Builder()
        self.plugin_loader = get_plugin_loader()

        self._is_dark_theme = self.config_manager.config.theme == "dark"

        self._setup_window()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_ui()
        self._setup_statusbar()
        self._connect_signals()
        self._apply_theme()
        self._load_config()

    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.setMinimumSize(1200, 950)
        self.resize(1350, 1020)

    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction("&Open Script...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._browse_script)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_preset_action = QAction("&Save Preset...", self)
        save_preset_action.setShortcut("Ctrl+S")
        save_preset_action.triggered.connect(self._save_preset)
        file_menu.addAction(save_preset_action)

        load_preset_action = QAction("&Load Preset...", self)
        load_preset_action.setShortcut("Ctrl+L")
        load_preset_action.triggered.connect(self._load_preset)
        file_menu.addAction(load_preset_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Build menu
        build_menu = menubar.addMenu("&Build")

        build_action = QAction("&Build", self)
        build_action.setShortcut("F5")
        build_action.triggered.connect(self._start_build)
        build_menu.addAction(build_action)

        cancel_action = QAction("&Cancel Build", self)
        cancel_action.setShortcut("Ctrl+Break")
        cancel_action.triggered.connect(self._cancel_build)
        build_menu.addAction(cancel_action)

        build_menu.addSeparator()

        open_output_action = QAction("&Open Output Folder", self)
        open_output_action.triggered.connect(self._open_output_folder)
        build_menu.addAction(open_output_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        self.theme_action = QAction("&Toggle Theme", self)
        self.theme_action.setShortcut("Ctrl+T")
        self.theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self.theme_action)

        clear_logs_action = QAction("&Clear Logs", self)
        clear_logs_action.setShortcut("Ctrl+Shift+C")
        clear_logs_action.triggered.connect(self._clear_logs)
        view_menu.addAction(clear_logs_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        hidden_imports_action = QAction("&Hidden Imports...", self)
        hidden_imports_action.triggered.connect(self._show_hidden_imports)
        tools_menu.addAction(hidden_imports_action)

        data_files_action = QAction("&Data Files...", self)
        data_files_action.triggered.connect(self._show_data_files)
        tools_menu.addAction(data_files_action)

        tools_menu.addSeparator()

        installer_action = QAction("&Installer Settings...", self)
        installer_action.triggered.connect(self._show_installer_settings)
        tools_menu.addAction(installer_action)

        tools_menu.addSeparator()

        plugins_action = QAction("&Reload Plugins", self)
        plugins_action.triggered.connect(self._reload_plugins)
        tools_menu.addAction(plugins_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Setup toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Build button
        self.build_btn = QPushButton("Build")
        self.build_btn.setMinimumWidth(80)
        self.build_btn.clicked.connect(self._start_build)
        self.build_btn.setToolTip("Start building the executable (F5)")
        toolbar.addWidget(self.build_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setMinimumWidth(80)
        self.cancel_btn.clicked.connect(self._cancel_build)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setToolTip("Cancel current build")
        toolbar.addWidget(self.cancel_btn)

        toolbar.addSeparator()

        # Theme toggle
        self.theme_btn = QPushButton("Toggle Theme")
        self.theme_btn.clicked.connect(self._toggle_theme)
        self.theme_btn.setToolTip("Switch between dark and light theme (Ctrl+T)")
        toolbar.addWidget(self.theme_btn)

    def _setup_ui(self):
        """Setup main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create splitter for main content and logs
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # Top section: Settings
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for different settings
        tab_widget = QTabWidget()
        settings_layout.addWidget(tab_widget)

        # Basic Settings Tab
        basic_tab = self._create_basic_tab()
        tab_widget.addTab(basic_tab, "Basic Settings")

        # Advanced Settings Tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Installer Tab (Placeholder)
        installer_tab = self._create_installer_tab()
        tab_widget.addTab(installer_tab, "Installer")

        # Plugins Tab
        plugins_tab = self._create_plugins_tab()
        tab_widget.addTab(plugins_tab, "Plugins")

        splitter.addWidget(settings_widget)

        # Bottom section: Log console
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_header = QHBoxLayout()
        log_label = QLabel("Build Output")
        log_label.setStyleSheet("font-weight: bold;")
        log_header.addWidget(log_label)

        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(90)
        clear_btn.clicked.connect(self._clear_logs)
        log_header.addWidget(clear_btn)

        log_layout.addLayout(log_header)

        self.log_console = LogConsole()
        log_layout.addWidget(self.log_console)

        splitter.addWidget(log_widget)

        # Set splitter sizes (55% settings, 45% logs)
        splitter.setSizes([550, 450])

    def _create_basic_tab(self) -> QWidget:
        """Create basic settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Script path
        script_layout = QHBoxLayout()
        self.script_edit = QLineEdit()
        self.script_edit.setPlaceholderText("Select your main Python script (.py)")
        self.script_edit.setToolTip("The main Python script that will be converted to an executable")
        script_layout.addWidget(self.script_edit)
        script_btn = QPushButton("Browse...")
        script_btn.clicked.connect(self._browse_script)
        script_layout.addWidget(script_btn)
        layout.addRow("Main Script:", script_layout)

        # Requirements path
        req_layout = QHBoxLayout()
        self.req_edit = QLineEdit()
        self.req_edit.setPlaceholderText("Optional: Select requirements.txt")
        self.req_edit.setToolTip("Requirements file for automatic dependency installation")
        req_layout.addWidget(self.req_edit)
        req_btn = QPushButton("Browse...")
        req_btn.clicked.connect(self._browse_requirements)
        req_layout.addWidget(req_btn)
        layout.addRow("Requirements:", req_layout)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Select output directory")
        self.output_edit.setText(str(get_default_output_dir()))
        self.output_edit.setToolTip("Directory where the built executable will be saved")
        output_layout.addWidget(self.output_edit)
        output_btn = QPushButton("Browse...")
        output_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(output_btn)
        layout.addRow("Output Directory:", output_layout)

        # Application name
        self.app_name_edit = QLineEdit()
        self.app_name_edit.setPlaceholderText("Optional: Custom application name")
        self.app_name_edit.setToolTip("Name for the output executable (defaults to script name)")
        layout.addRow("App Name:", self.app_name_edit)

        # Icon path
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("Optional: Select application icon (.ico)")
        self.icon_edit.setToolTip("Icon file for the executable (Windows .ico format)")
        icon_layout.addWidget(self.icon_edit)
        icon_btn = QPushButton("Browse...")
        icon_btn.clicked.connect(self._browse_icon)
        icon_layout.addWidget(icon_btn)
        layout.addRow("Icon:", icon_layout)

        # Build options group
        options_group = QGroupBox("Build Options")
        options_layout = QHBoxLayout(options_group)

        # One file / One directory
        self.onefile_check = QCheckBox("One File")
        self.onefile_check.setChecked(True)
        self.onefile_check.setToolTip("Create a single executable file (--onefile)")
        options_layout.addWidget(self.onefile_check)

        self.onedir_check = QCheckBox("One Directory")
        self.onedir_check.setToolTip("Create a directory with executable and dependencies (--onedir)")
        options_layout.addWidget(self.onedir_check)

        # Make mutually exclusive
        self.onefile_check.stateChanged.connect(
            lambda s: self.onedir_check.setChecked(not s) if s else None
        )
        self.onedir_check.stateChanged.connect(
            lambda s: self.onefile_check.setChecked(not s) if s else None
        )

        options_layout.addSpacing(30)

        # Console mode
        self.console_check = QCheckBox("Console Window")
        self.console_check.setChecked(True)
        self.console_check.setToolTip("Show console window when running (uncheck for GUI apps)")
        options_layout.addWidget(self.console_check)

        options_layout.addSpacing(30)

        # Clean build
        self.clean_check = QCheckBox("Clean Build")
        self.clean_check.setChecked(True)
        self.clean_check.setToolTip("Remove previous build cache before building (--clean)")
        options_layout.addWidget(self.clean_check)

        options_layout.addStretch()

        layout.addRow(options_group)

        return tab

    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Hidden imports section
        hidden_group = QGroupBox("Hidden Imports")
        hidden_layout = QHBoxLayout(hidden_group)
        self.hidden_imports_label = QLabel("No hidden imports configured")
        hidden_layout.addWidget(self.hidden_imports_label)
        hidden_btn = QPushButton("Configure...")
        hidden_btn.clicked.connect(self._show_hidden_imports)
        hidden_layout.addWidget(hidden_btn)
        layout.addWidget(hidden_group)

        # Exclude modules section
        exclude_group = QGroupBox("Exclude Modules")
        exclude_layout = QVBoxLayout(exclude_group)
        self.exclude_modules_edit = QLineEdit()
        self.exclude_modules_edit.setPlaceholderText("e.g., tkinter, numpy, matplotlib")
        self.exclude_modules_edit.setToolTip(
            "Exclude specific modules from the final executable.\n"
            "Enter comma-separated module names (e.g., tkinter, numpy)"
        )
        exclude_layout.addWidget(self.exclude_modules_edit)
        layout.addWidget(exclude_group)

        # Data files section
        data_group = QGroupBox("Data Files")
        data_layout = QHBoxLayout(data_group)
        self.data_files_label = QLabel("No data files configured")
        data_layout.addWidget(self.data_files_label)
        data_btn = QPushButton("Configure...")
        data_btn.clicked.connect(self._show_data_files)
        data_layout.addWidget(data_btn)
        layout.addWidget(data_group)

        # Additional arguments
        args_group = QGroupBox("Additional PyInstaller Arguments")
        args_layout = QVBoxLayout(args_group)
        self.additional_args_edit = QLineEdit()
        self.additional_args_edit.setPlaceholderText("e.g., --clean --debug=all")
        self.additional_args_edit.setToolTip("Additional command line arguments to pass to PyInstaller")
        args_layout.addWidget(self.additional_args_edit)
        layout.addWidget(args_group)

        # Python interpreter selection
        interp_group = QGroupBox("Python Interpreter")
        interp_layout = QHBoxLayout(interp_group)
        self.interp_combo = QComboBox()
        self.interp_combo.addItem(f"Current: {sys.executable}")
        self.interp_combo.setToolTip("Select Python interpreter to use for building")
        interp_layout.addWidget(self.interp_combo)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_interpreters)
        interp_layout.addWidget(refresh_btn)
        layout.addWidget(interp_group)

        layout.addStretch()

        return tab

    def _create_installer_tab(self) -> QWidget:
        """Create installer settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Info label
        info_label = QLabel(
            "Configure installer creation settings.\n"
            "After building with PyInstaller, an installer can be created using NSIS or Inno Setup."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Enable checkbox
        self.installer_enable_check = QCheckBox("Enable installer creation after build")
        self.installer_enable_check.setToolTip("Create an installer package after successful build")
        layout.addWidget(self.installer_enable_check)

        # Settings button
        settings_btn = QPushButton("Configure Installer Settings...")
        settings_btn.clicked.connect(self._show_installer_settings)
        settings_btn.setMaximumWidth(250)
        layout.addWidget(settings_btn)

        # Status
        self.installer_status_label = QLabel("Installer: Not configured")
        self.installer_status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.installer_status_label)

        layout.addStretch()

        # Note about requirements
        note = QLabel(
            "Note: NSIS (nullsoft.com) or Inno Setup (jrsoftware.org) must be installed\n"
            "on your system for installer creation to work."
        )
        note.setStyleSheet("color: gray;")
        layout.addWidget(note)

        return tab

    def _create_plugins_tab(self) -> QWidget:
        """Create plugins tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Available Plugins")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)

        reload_btn = QPushButton("Reload Plugins")
        reload_btn.clicked.connect(self._reload_plugins)
        header_layout.addWidget(reload_btn)

        layout.addLayout(header_layout)

        # Plugins list
        self.plugins_list = QTextEdit()
        self.plugins_list.setReadOnly(True)
        self._update_plugins_list()
        layout.addWidget(self.plugins_list)

        # Info
        info = QLabel(
            "Plugins extend the build process with custom tasks.\n"
            "Place plugin files (.py) in the 'plugins' folder."
        )
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)

        return tab

    def _setup_statusbar(self):
        """Setup status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

        self.statusbar.showMessage("Ready")

    def _connect_signals(self):
        """Connect logger signals to UI."""
        emitter = get_emitter()
        emitter.log_message.connect(self.log_console.append_log)
        emitter.build_output.connect(self.log_console.append_output)

    def _apply_theme(self):
        """Apply current theme to the application."""
        if self._is_dark_theme:
            self._apply_dark_theme()
        else:
            self._apply_light_theme()

    def _apply_dark_theme(self):
        """Apply dark theme stylesheet."""
        stylesheet = """
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 5px;
                color: #ffffff;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #4a4a4a;
                color: #888888;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
            QMenuBar {
                background-color: #2d2d2d;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #0078d4;
            }
            QToolBar {
                background-color: #2d2d2d;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #5c5c5c;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c6c6c;
            }
        """
        self.setStyleSheet(stylesheet)

    def _apply_light_theme(self):
        """Apply light theme stylesheet."""
        stylesheet = """
            QMainWindow, QWidget {
                background-color: #f5f5f5;
                color: #000000;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                color: #000000;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
            }
            QCheckBox {
                spacing: 8px;
            }
            QStatusBar {
                background-color: #0078d4;
                color: white;
            }
            QMenuBar {
                background-color: #e0e0e0;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QToolBar {
                background-color: #e0e0e0;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """
        self.setStyleSheet(stylesheet)

    def _toggle_theme(self):
        """Toggle between dark and light themes."""
        self._is_dark_theme = not self._is_dark_theme
        self._apply_theme()
        self.config_manager.set("theme", "dark" if self._is_dark_theme else "light")
        self.logger.info(f"Theme changed to {'dark' if self._is_dark_theme else 'light'}")

    def _load_config(self):
        """Load configuration into UI."""
        config = self.config_manager.config.build_config

        self.script_edit.setText(config.script_path)
        self.req_edit.setText(config.requirements_path)
        self.output_edit.setText(config.output_dir or str(get_default_output_dir()))
        self.app_name_edit.setText(config.app_name)
        self.icon_edit.setText(config.icon_path)
        self.onefile_check.setChecked(config.one_file)
        self.onedir_check.setChecked(not config.one_file)
        self.console_check.setChecked(config.console_mode)
        self.clean_check.setChecked(config.clean_build)
        self.additional_args_edit.setText(config.additional_args)

        # Exclude modules (convert list to comma-separated string)
        self.exclude_modules_edit.setText(", ".join(config.exclude_modules))

        # Update labels
        self._update_hidden_imports_label()
        self._update_data_files_label()

        # Installer
        self.installer_enable_check.setChecked(
            self.config_manager.config.installer_config.enabled
        )

    def _save_config(self):
        """Save current UI state to configuration."""
        config = self.config_manager.config.build_config
        config.script_path = self.script_edit.text()
        config.requirements_path = self.req_edit.text()
        config.output_dir = self.output_edit.text()
        config.app_name = self.app_name_edit.text()
        config.icon_path = self.icon_edit.text()
        config.one_file = self.onefile_check.isChecked()
        config.console_mode = self.console_check.isChecked()
        config.clean_build = self.clean_check.isChecked()
        config.additional_args = self.additional_args_edit.text()

        # Exclude modules (convert comma-separated string to list)
        exclude_text = self.exclude_modules_edit.text()
        config.exclude_modules = [m.strip() for m in exclude_text.split(",") if m.strip()]

        self.config_manager.config.installer_config.enabled = (
            self.installer_enable_check.isChecked()
        )

        self.config_manager.save()

    def _get_build_config(self) -> BuildConfig:
        """Get current build configuration from UI."""
        # Parse exclude modules from comma-separated text
        exclude_text = self.exclude_modules_edit.text()
        exclude_modules = [m.strip() for m in exclude_text.split(",") if m.strip()]

        return BuildConfig(
            script_path=self.script_edit.text(),
            requirements_path=self.req_edit.text(),
            output_dir=self.output_edit.text(),
            icon_path=self.icon_edit.text(),
            app_name=self.app_name_edit.text(),
            one_file=self.onefile_check.isChecked(),
            console_mode=self.console_check.isChecked(),
            clean_build=self.clean_check.isChecked(),
            hidden_imports=self.config_manager.config.build_config.hidden_imports,
            exclude_modules=exclude_modules,
            data_files=self.config_manager.config.build_config.data_files,
            additional_args=self.additional_args_edit.text()
        )

    # File browser methods
    def _browse_script(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Python Script",
            self.config_manager.config.last_script_dir,
            "Python Files (*.py)"
        )
        if path:
            self.script_edit.setText(path)
            self.config_manager.set("last_script_dir", str(Path(path).parent))

    def _browse_requirements(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Requirements File", "",
            "Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.req_edit.setText(path)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory",
            self.config_manager.config.last_output_dir
        )
        if path:
            self.output_edit.setText(path)
            self.config_manager.set("last_output_dir", path)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon File", "",
            "Icon Files (*.ico)"
        )
        if path:
            self.icon_edit.setText(path)

    # Build methods
    def _validate_inputs(self) -> bool:
        """Validate all inputs before build."""
        # Script validation
        valid, msg = validate_python_script(self.script_edit.text())
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return False

        # Requirements validation
        valid, msg = validate_requirements_file(self.req_edit.text())
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return False

        # Icon validation
        valid, msg = validate_icon_file(self.icon_edit.text())
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return False

        # Output directory validation
        valid, msg = validate_output_directory(self.output_edit.text())
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return False

        return True

    def _start_build(self):
        """Start the build process."""
        if self.builder.is_building():
            QMessageBox.warning(self, "Build in Progress", "A build is already running.")
            return

        if not self._validate_inputs():
            return

        self._save_config()

        # Update UI state
        self.build_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        self.log_console.clear()
        self.statusbar.showMessage("Building...")
        self.logger.info("Starting build process...")

        # Get configuration
        build_config = self._get_build_config()

        # Get selected Python interpreter
        python_path = None
        interp_text = self.interp_combo.currentText()
        if not interp_text.startswith("Current:"):
            python_path = interp_text

        # Start build
        self.builder.start_build(
            config=build_config,
            on_output=self._on_build_output,
            on_finished=self._on_build_finished,
            on_status=self._on_build_status,
            python_path=python_path
        )

    def _cancel_build(self):
        """Cancel the current build."""
        if self.builder.is_building():
            self.builder.cancel_build()
            self.logger.warning("Build cancelled by user")
            self.statusbar.showMessage("Build cancelled")

    def _on_build_output(self, line: str):
        """Handle build output line."""
        self.log_console.append_output(line)

    def _on_build_status(self, status: str):
        """Handle build status update."""
        self.statusbar.showMessage(status)

    def _on_build_finished(self, result: BuildResult):
        """Handle build completion."""
        # Update UI state
        self.build_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        if result.status == BuildStatus.SUCCESS:
            self.statusbar.showMessage(
                f"Build completed successfully in {result.build_time:.1f}s"
            )
            self.logger.success(f"Build completed in {result.build_time:.1f}s")

            # Open output folder if configured
            if self.config_manager.config.auto_open_output and result.output_path:
                open_folder(result.output_path)

            # Run post-build plugins
            self._run_post_build_plugins(result)

        elif result.status == BuildStatus.FAILED:
            self.statusbar.showMessage("Build failed")
            self.logger.error(f"Build failed: {result.error_message}")
            QMessageBox.critical(
                self, "Build Failed",
                f"The build process failed:\n{result.error_message}"
            )

        elif result.status == BuildStatus.CANCELLED:
            self.statusbar.showMessage("Build cancelled")

    def _run_post_build_plugins(self, result: BuildResult):
        """Run post-build plugins."""
        plugins = self.plugin_loader.get_post_build_plugins()
        if not plugins:
            return

        context = {
            'build_config': self._get_build_config(),
            'output_path': result.output_path,
            'build_result': result,
            'app_config': self.config_manager.config
        }

        results = self.plugin_loader.execute_post_build_plugins(context)
        for name, success in results.items():
            if success:
                self.logger.info(f"Plugin '{name}' executed successfully")
            else:
                self.logger.warning(f"Plugin '{name}' failed")

    # Dialog methods
    def _show_hidden_imports(self):
        """Show hidden imports dialog."""
        dialog = HiddenImportsDialog(
            self.config_manager.config.build_config.hidden_imports,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.config_manager.config.build_config.hidden_imports = dialog.get_imports()
            self.config_manager.save()
            self._update_hidden_imports_label()

    def _show_data_files(self):
        """Show data files dialog."""
        dialog = DataFilesDialog(
            self.config_manager.config.build_config.data_files,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.config_manager.config.build_config.data_files = dialog.get_data_files()
            self.config_manager.save()
            self._update_data_files_label()

    def _show_installer_settings(self):
        """Show installer settings dialog."""
        dialog = InstallerSettingsDialog(
            self.config_manager.config.installer_config,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            self.config_manager.config.installer_config = dialog.get_config()
            self.config_manager.save()
            self._update_installer_status()

    def _show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()

    # Helper methods
    def _update_hidden_imports_label(self):
        count = len(self.config_manager.config.build_config.hidden_imports)
        self.hidden_imports_label.setText(
            f"{count} hidden import(s) configured" if count else "No hidden imports configured"
        )

    def _update_data_files_label(self):
        count = len(self.config_manager.config.build_config.data_files)
        self.data_files_label.setText(
            f"{count} data file(s) configured" if count else "No data files configured"
        )

    def _update_installer_status(self):
        config = self.config_manager.config.installer_config
        if config.enabled:
            self.installer_status_label.setText(
                f"Installer: {config.installer_type.upper()} - {config.app_name or 'Not named'}"
            )
        else:
            self.installer_status_label.setText("Installer: Disabled")

    def _update_plugins_list(self):
        plugins = self.plugin_loader.get_all_plugins()
        if plugins:
            text = ""
            for plugin in plugins:
                info = plugin.get_info()
                text += f"[{info.plugin_type}] {info.name} v{info.version}\n"
                text += f"  {info.description}\n"
                text += f"  Author: {info.author}\n\n"
            self.plugins_list.setText(text)
        else:
            self.plugins_list.setText("No plugins loaded.\n\nPlace .py plugin files in the 'plugins' folder.")

    def _refresh_interpreters(self):
        """Refresh list of Python interpreters."""
        from app.core.venv_manager import VenvManager
        venv_manager = VenvManager()

        self.interp_combo.clear()
        self.interp_combo.addItem(f"Current: {sys.executable}")

        for interp in venv_manager.get_python_interpreters():
            if interp != sys.executable:
                self.interp_combo.addItem(interp)

    def _new_project(self):
        """Clear all fields for a new project."""
        self.script_edit.clear()
        self.req_edit.clear()
        self.app_name_edit.clear()
        self.icon_edit.clear()
        self.additional_args_edit.clear()
        self.exclude_modules_edit.clear()
        self.onefile_check.setChecked(True)
        self.console_check.setChecked(True)
        self.clean_check.setChecked(True)
        self.config_manager.config.build_config.hidden_imports = []
        self.config_manager.config.build_config.exclude_modules = []
        self.config_manager.config.build_config.data_files = []
        self._update_hidden_imports_label()
        self._update_data_files_label()
        self.log_console.clear()
        self.statusbar.showMessage("New project")

    def _save_preset(self):
        """Save current settings as a preset."""
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if ok and name:
            config = self._get_build_config()
            self.config_manager.save_preset(name, config)
            self.logger.info(f"Preset '{name}' saved")

    def _load_preset(self):
        """Load a saved preset."""
        dialog = PresetsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            preset_name = dialog.get_selected_preset()
            if preset_name:
                config = self.config_manager.load_preset(preset_name)
                if config:
                    self.config_manager.config.build_config = config
                    self._load_config()
                    self.logger.info(f"Preset '{preset_name}' loaded")

    def _open_output_folder(self):
        """Open the output folder in file explorer."""
        output_dir = self.output_edit.text()
        if output_dir and Path(output_dir).exists():
            open_folder(Path(output_dir))
        else:
            QMessageBox.warning(self, "Error", "Output directory does not exist.")

    def _clear_logs(self):
        """Clear the log console."""
        self.log_console.clear()

    def _reload_plugins(self):
        """Reload all plugins."""
        self.plugin_loader.reload_plugins()
        self._update_plugins_list()
        self.logger.info("Plugins reloaded")

    def closeEvent(self, event):
        """Handle window close event."""
        self._save_config()
        event.accept()
