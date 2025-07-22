import sys
from PyQt6 import QtWidgets
from logjam.ui.controller import AppController
from logjam.ui.app import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller
    window.show()
    app.exec()

if __name__ == "__main__":
    main()