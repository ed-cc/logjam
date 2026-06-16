import sys
import logging

from PyQt6 import QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QPalette, QKeySequence, QShortcut
from PyQt6.QtWidgets import QDialog

from logjam.core.filter_config import Filter
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
        self._setup_filter_panel()
        self._setup_find_bar()
        self._setup_recent_files_menu()

        self.settings = QSettings("LogJam", "LogJamApp")
        self._restore_window_state()

        logger.info("MainWindow initialization completed")

    def _setup_find_bar(self):
        """Create the hidden find bar shown with Ctrl+F."""
        self.find_bar = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.find_bar)
        row.setContentsMargins(2, 2, 2, 2)
        row.addWidget(QtWidgets.QLabel("Find:"))
        self.find_input = QtWidgets.QLineEdit()
        self.find_input.textChanged.connect(self._on_find_text_changed)
        self.find_input.returnPressed.connect(lambda: self._find(forward=True))
        row.addWidget(self.find_input)
        self.find_count_label = QtWidgets.QLabel("")
        row.addWidget(self.find_count_label)
        prev_button = QtWidgets.QPushButton("Previous")
        prev_button.clicked.connect(lambda: self._find(forward=False))
        next_button = QtWidgets.QPushButton("Next")
        next_button.clicked.connect(lambda: self._find(forward=True))
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.hide_find_bar)
        row.addWidget(prev_button)
        row.addWidget(next_button)
        row.addWidget(close_button)

        self.centralwidget.layout().addWidget(self.find_bar)
        self.find_bar.hide()

        self.find_action = QtGui.QAction("Find", self)
        self.find_action.setShortcut("Ctrl+F")
        self.find_action.triggered.connect(self.show_find_bar)
        self.addAction(self.find_action)
        self.menuView.addAction(self.find_action)

        QShortcut(QKeySequence("Escape"), self.find_bar, activated=self.hide_find_bar)

    def show_find_bar(self):
        self.find_bar.show()
        self.find_input.setFocus()
        self.find_input.selectAll()
        self._on_find_text_changed(self.find_input.text())

    def hide_find_bar(self):
        self.find_bar.hide()
        self.textBrowser.highlight_matches("")

    def _on_find_text_changed(self, text):
        count = self.textBrowser.highlight_matches(text)
        self.find_count_label.setText(f"{count} matches" if text else "")
        if text:
            self.textBrowser.find_next(text, forward=True, from_start=True)

    def _find(self, forward=True):
        self.textBrowser.find_next(self.find_input.text(), forward=forward)

    def _setup_recent_files_menu(self):
        """Add an 'Open Recent' submenu populated from persisted history."""
        self.recent_menu = self.menuFile.addMenu("Open Recent")
        self.recent_menu.aboutToShow.connect(self._populate_recent_files_menu)

    def _populate_recent_files_menu(self):
        self.recent_menu.clear()
        recent = self.controller.recent_files() if self.controller else []
        if not recent:
            empty = self.recent_menu.addAction("(No recent files)")
            empty.setEnabled(False)
            return
        for path in recent:
            action = self.recent_menu.addAction(path)
            action.triggered.connect(lambda _checked, p=path: self._open_recent(p))

    def _open_recent(self, path):
        if not self.controller:
            return
        file_name = os.path.basename(path)
        self.setWindowTitle(f"LogJam - {file_name}")
        self.update_status_bar(file_name=file_name)
        self.controller.open_file(path)

    def _restore_window_state(self):
        geometry = self.settings.value("window_geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        state = self.settings.value("window_state")
        if state is not None:
            self.restoreState(state)

    def closeEvent(self, event):
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        super().closeEvent(event)

    def _setup_filter_panel(self):
        """Create the dockable panel that lists and manages filters."""
        self.filter_dock = QtWidgets.QDockWidget("Filters", self)
        self.filter_dock.setObjectName("filterDock")

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        self.filter_list = QtWidgets.QListWidget()
        self.filter_list.currentItemChanged.connect(self._on_filter_selected)
        self.filter_list.itemDoubleClicked.connect(lambda _item: self.edit_filter())
        layout.addWidget(self.filter_list)

        button_row = QtWidgets.QHBoxLayout()
        self.add_filter_button = QtWidgets.QPushButton("New")
        self.add_filter_button.clicked.connect(self.new_filter)
        self.edit_filter_button = QtWidgets.QPushButton("Edit")
        self.edit_filter_button.clicked.connect(self.edit_filter)
        self.duplicate_filter_button = QtWidgets.QPushButton("Duplicate")
        self.duplicate_filter_button.clicked.connect(self.duplicate_filter)
        self.remove_filter_button = QtWidgets.QPushButton("Remove")
        self.remove_filter_button.clicked.connect(self.remove_filter)
        for button in (
            self.add_filter_button,
            self.edit_filter_button,
            self.duplicate_filter_button,
            self.remove_filter_button,
        ):
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.filter_dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.filter_dock)
        self.menuView.addAction(self.filter_dock.toggleViewAction())
        self.refresh_filter_panel()

    def refresh_filter_panel(self):
        """Rebuild the filter list to match the controller's configuration."""
        if not hasattr(self, "filter_list"):
            return
        names = []
        if self.controller and self.controller.filter_config:
            names = self.controller.filter_config.filter_names()

        self.filter_list.blockSignals(True)
        self.filter_list.clear()
        self.filter_list.addItems(names)
        active = self.controller.active_filter_name if self.controller else None
        if active in names:
            self.filter_list.setCurrentRow(names.index(active))
        self.filter_list.blockSignals(False)

        has_filters = bool(names)
        self.edit_filter_button.setEnabled(has_filters)
        self.duplicate_filter_button.setEnabled(has_filters)
        self.remove_filter_button.setEnabled(has_filters)

    def _on_filter_selected(self, current, _previous):
        if current and self.controller:
            self.controller.set_active_filter(current.text())

    def _selected_filter_name(self):
        item = self.filter_list.currentItem()
        return item.text() if item else None

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
        default_name = self.controller._unique_name("Filter 1")
        filter = Filter(default_name, LogicalOperator.OR)
        logger.debug("Created new filter with default settings")
        dialog = EditFilterDialog(filter, is_new=True)
        dialog.exec()
        logger.debug("EditFilterDialog executed")
        if dialog.result() == QDialog.DialogCode.Accepted:
            logger.info("User accepted new filter dialog")
            try:
                self.controller.add_filter(filter)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "Duplicate Filter", str(exc))
                return
            logger.info("New filter added to controller")
        else:
            logger.info("User cancelled new filter dialog")

    def edit_filter(self):
        if not self.controller:
            logger.warning("Controller not set")
            return
        name = self._selected_filter_name()
        if name is None and self.controller.filter_config is not None:
            names = self.controller.filter_config.filter_names()
            name = names[0] if names else None
        if name is None:
            logger.warning("No filter available to edit")
            QtWidgets.QMessageBox.warning(
                self, "No Filter", "No filter selected to edit."
            )
            return
        filter = self.controller.filter_config.get_filter_by_name(name)
        logger.info(f"User initiated edit for filter: {filter.name}")
        dialog = EditFilterDialog(filter, is_new=False)
        dialog.exec()
        logger.debug("EditFilterDialog executed")
        if dialog.result() == QDialog.DialogCode.Accepted:
            logger.info("User accepted edit filter dialog")
            try:
                self.controller.replace_filter(name, filter)
            except ValueError as exc:
                QtWidgets.QMessageBox.warning(self, "Rename Failed", str(exc))
                return
            logger.info("Edited filter saved to controller")
        else:
            logger.info("User cancelled edit filter dialog")

    def duplicate_filter(self):
        if not self.controller:
            return
        name = self._selected_filter_name()
        if name:
            self.controller.duplicate_filter(name)

    def remove_filter(self):
        if not self.controller:
            return
        name = self._selected_filter_name()
        if not name:
            return
        confirm = QtWidgets.QMessageBox.question(
            self, "Remove Filter", f"Remove filter '{name}'?"
        )
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            self.controller.remove_filter(name)

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
