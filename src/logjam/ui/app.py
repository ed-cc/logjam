import sys
from PyQt6 import QtWidgets, uic
from logjam.ui.MainWindow import Ui_MainWindow
from logjam.ui.controller import AppController


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, controller: AppController | None, *args, obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.controller = controller
        # Register callbacks
        self.actionOpen.triggered.connect(self.open_file)
        self.actionLoad_Filters.triggered.connect(self.load_filters)

    def open_file(self):
        if not self.controller:
            print("Controller not set")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Open File", "", "Text files (*.txt *.log);;All Files (*)")
        if file_path:
            print(f"Selected file: {file_path}")
        self.controller.open_file(file_path)

    def load_filters(self):
        if not self.controller:
            print("Controller not set")
            return
        file_dialog = QtWidgets.QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, "Open Filter", "", "Json filter files (*.json);;All Files (*)")
        if file_path:
            print(f"Selected filter: {file_path}")
        self.controller.load_filters(file_path)
