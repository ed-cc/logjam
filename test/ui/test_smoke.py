from logjam.ui.app import MainWindow
from logjam.ui.controller import AppController


def test_mainwindow_constructs(qtbot):
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller
    qtbot.addWidget(window)

    # Wait for the background startup worker to settle.
    controller.threadpool.waitForDone(2000)

    assert window.windowTitle() == "LogJam"
    assert window.controller is controller
