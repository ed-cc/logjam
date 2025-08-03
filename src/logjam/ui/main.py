import sys
import logging
import argparse
from PyQt6 import QtWidgets
from logjam.ui.controller import AppController
from logjam.ui.app import MainWindow

def main():
    parser = argparse.ArgumentParser(description="LogJam - A configurable tool for filtering text files")
    parser.add_argument("file", nargs="?", help="Path to the log file to open (positional)")
    parser.add_argument("--file", "-i", dest="file_flag", help="Path to the log file to open (optional flag)")
    parser.add_argument("-f", "--filter", help="Path to the filter configuration file")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller

    file_to_open = args.file or args.file_flag
    if file_to_open:
        controller.open_file(file_to_open)
    if args.filter:
        controller.load_filters(args.filter)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()