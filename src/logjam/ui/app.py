import sys
import logging

from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QDialog

from logjam.core.filter_config import Filter, FilterConfig
from logjam.core.logical_operator import LogicalOperator
from logjam.ui.MainWindow import Ui_MainWindow
from logjam.ui.controller import AppController
from logjam.ui.edit_filter_dialog import EditFilterDialog
from logjam.ui.log_file_viewer import QLogFileViewer
import os

logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, controller: AppController | None, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing MainWindow")
        self.setupUi(self)
        self.setWindowTitle("LogJam")

        # Replace textBrowser with QLogFileViewer
        self._replace_text_browser_with_log_viewer()
        logger.info("Replaced textBrowser with QLogFileViewer")

        self.controller = controller

        self.actionOpen.triggered.connect(self.open_file)
        self.actionOpen_Filter.triggered.connect(self.load_filters)
        self.actionNew_Filter.triggered.connect(self.new_filter)
        self.actionEdit_Current_Filter.triggered.connect(self.edit_filter)
        self.actionSave_As.triggered.connect(self.save_filter_as)
        self.actionSave.triggered.connect(self.save_current_filter)

        self.actionOpen.setShortcut("Ctrl+O")
        self.actionOpen_Filter.setShortcut("Ctrl+Shift+O")
        self.actionNew_Filter.setShortcut("Ctrl+N")
        self.actionEdit_Current_Filter.setShortcut("Ctrl+E")
        self.actionSave.setShortcut("Ctrl+S")
        self.actionSave_As.setShortcut("Ctrl+Shift+S")

        self._setup_status_bar()

        logger.info("MainWindow initialization completed")

    def _setup_status_bar(self):
        """Initialize the status bar with permanent widgets"""
        self.file_info_label = QtWidgets.QLabel("No file loaded")
        self.statusbar.addPermanentWidget(self.file_info_label)

        self.filter_info_label = QtWidgets.QLabel("No filter")
        self.statusbar.addPermanentWidget(self.filter_info_label)

        self.line_count_label = QtWidgets.QLabel("0 lines")
        self.statusbar.addPermanentWidget(self.line_count_label)

        self.statusbar.showMessage("Ready")

    def update_status_bar(self, file_name=None, filter_name=None, line_count=None):
        """Update status bar information"""
        if file_name:
            self.file_info_label.setText(f"File: {file_name}")
        if filter_name:
            self.filter_info_label.setText(f"Filter: {filter_name}")
        if line_count is not None:
            self.line_count_label.setText(f"{line_count} lines")

    def _replace_text_browser_with_log_viewer(self):
        """Replace the default textBrowser with QLogFileViewer"""
        logger.debug("Starting textBrowser replacement")
        parent_widget = self.textBrowser.parent()

        self.textBrowser.setParent(None)
        logger.debug("Removed original textBrowser")

        is_dark = self._is_dark_theme()
        logger.info(f"Detected theme: {'dark' if is_dark else 'light'}")

        # Create the new QLogFileViewer
        self.textBrowser = QLogFileViewer(
            parent=self.centralwidget, is_dark_theme=is_dark
        )

        # Clear any existing layout and create a new one
        if self.centralwidget.layout():
            QtWidgets.QWidget().setLayout(
                self.centralwidget.layout()
            )  # Remove existing layout

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self.textBrowser)
        self.centralwidget.setLayout(layout)

        # Set monospaced font with cross-platform compatibility
        from PyQt6.QtGui import QFont

        monospace_font = QFont()
        monospace_font.setFamilies(
            [
                "SF Mono",
                "Consolas",
                "Menlo",
                "Monaco",
                "DejaVu Sans Mono",
                "Courier New",
                "monospace",
            ]
        )
        monospace_font.setPointSize(10)
        self.textBrowser.setFont(monospace_font)

        # Ensure the text browser expands to fill available space
        self.textBrowser.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.textBrowser.setObjectName("textBrowser")
        logger.debug("QLogFileViewer created and configured")

    def _is_dark_theme(self) -> bool:
        """Check if the application is using a dark theme"""
        palette = self.palette()
        window_color = palette.color(QPalette.ColorRole.Window)
        return window_color.lightness() < 128

    def open_file(self):
        logger.info("User initiated file open dialog")
        if not self.controller:
            logger.warning("Controller not set")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open File", "", "Text files (*.txt *.log);;All Files (*)"
        )
        if file_path:
            logger.info(f"User selected file: {file_path}")
            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"LogJam - {file_name}")
            # Update status bar
            self.update_status_bar(file_name=file_name)
            self.statusbar.showMessage(f"Loading {file_name}...", 2000)
            self.controller.open_file(file_path)
        else:
            logger.info("User cancelled file selection")

    def load_filters(self):
        logger.info("User initiated filter open dialog")
        if not self.controller:
            logger.warning("Controller not set")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open Filter", "", "Json filter files (*.json);;All Files (*)"
        )
        if file_path:
            logger.info(f"User selected filter file: {file_path}")
            filter_name = os.path.basename(file_path)
            self.update_status_bar(filter_name=filter_name)
            self.statusbar.showMessage(f"Loading filter {filter_name}...", 2000)
            self.controller.load_filters(file_path)
        else:
            logger.info("User cancelled filter selection")

    def new_filter(self):
        logger.info("User initiated new filter creation")
        if not self.controller:
            logger.warning("Controller not set")
            return
        filter = Filter("Filter 1", LogicalOperator.OR)
        logger.debug("Created new filter with default settings")
        dialog = EditFilterDialog(filter, is_new=True)
        dialog.exec()
        logger.debug("EditFilterDialog executed")
        if dialog.result() == QDialog.DialogCode.Accepted:
            logger.info("User accepted new filter dialog")
            filter_config = FilterConfig()
            filter_config.add_filter(filter)
            self.controller.set_filter_config(filter_config, is_new=True)
            logger.info("New filter configuration set in controller")
        else:
            logger.info("User cancelled new filter dialog")

    def edit_filter(self):
        if not self.controller:
            logger.warning("Controller not set")
            return
        if self.controller.filter_config is not None:
            filter = self.controller.filter_config.get_first_filter()
        else:
            logger.warning("No filter configuration available to edit")
            QtWidgets.QMessageBox.warning(
                self, "No Filter Config", "No filter configuration available to edit."
            )
            return
        logger.info(f"User initiated edit for filter: {filter.name}")
        dialog = EditFilterDialog(filter, is_new=False)
        dialog.exec()
        logger.debug("EditFilterDialog executed")
        if dialog.result() == QDialog.DialogCode.Accepted:
            logger.info("User accepted edit filter dialog")
            filter_config = FilterConfig()
            filter_config.add_filter(filter)
            self.controller.set_filter_config(filter_config)
            logger.info("Edited filter configuration set in controller")
        else:
            logger.info("User cancelled edit filter dialog")

    def save_filter_as(self):
        if not self.controller:
            logger.warning("Controller not set")
            return
        if self.controller.filter_config is None:
            logger.warning("No filter configuration available to save")
            QtWidgets.QMessageBox.warning(
                self, "No Filter Config", "No filter configuration available to save."
            )
            return
        file_dialog = QtWidgets.QFileDialog(self)

        file_dialog.setWindowTitle("Save Filter Configuration As")
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Filter", "", "Json filter files (*.json);;All Files (*)"
        )
        if file_path:
            logger.info(f"User selected save path: {file_path}")
            self.controller.filter_config.to_file(file_path)
            logger.info(f"Filter configuration saved to: {file_path}")
        else:
            logger.info("User cancelled save filter dialog")

    def save_current_filter(self):
        if not self.controller:
            logger.warning("Controller not set")
            return
        if self.controller.filter_config is None:
            logger.warning("No filter configuration available to save")
            QtWidgets.QMessageBox.warning(
                self, "No Filter Config", "No filter configuration available to save."
            )
            return
        if self.controller.filter_file_path:
            try:
                self.controller.filter_config.to_file(self.controller.filter_file_path)
                QtWidgets.QMessageBox.information(
                    self, "Save Filter", "Filter configuration saved successfully."
                )
                logger.info(
                    f"Filter configuration saved to: {self.controller.filter_file_path}"
                )
            except Exception as e:
                logger.error(f"Error saving filter configuration: {e}")
                QtWidgets.QMessageBox.critical(
                    self, "Save Error", f"Error saving filter configuration: {e}"
                )
        else:
            logger.info("No filter file path set, using save as dialog")
            self.save_filter_as()
