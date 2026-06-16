from PyQt6.QtCore import QSettings

from logjam.ui.app import MainWindow
from logjam.ui.controller import AppController
from logjam.ui.log_file_viewer import QLogFileViewer


def _make(qtbot):
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller
    qtbot.addWidget(window)
    controller.threadpool.waitForDone(2000)
    return window, controller


def test_highlight_matches_counts(qtbot):
    viewer = QLogFileViewer()
    qtbot.addWidget(viewer)
    viewer.setPlainText("foo\nfoobar\nbaz")

    assert viewer.highlight_matches("foo") == 2
    assert viewer.highlight_matches("zzz") == 0
    assert viewer.highlight_matches("") == 0


def test_find_next_moves_cursor(qtbot):
    viewer = QLogFileViewer()
    qtbot.addWidget(viewer)
    viewer.setPlainText("alpha\nbeta\nalpha")

    assert viewer.find_next("beta", from_start=True) is True
    assert viewer.textCursor().selectedText() == "beta"
    assert viewer.find_next("nope") is False


def test_find_bar_show_and_hide(qtbot):
    window, _ = _make(qtbot)
    window.textBrowser.setPlainText("foo foo bar")

    window.show_find_bar()
    assert not window.find_bar.isHidden()
    window.find_input.setText("foo")
    assert "2 matches" == window.find_count_label.text()

    window.hide_find_bar()
    assert window.find_bar.isHidden()


def test_recent_files_tracking(qtbot, tmp_path):
    _, controller = _make(qtbot)
    controller.settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )

    controller._add_recent_file("/x/a.log")
    controller._add_recent_file("/x/b.log")
    controller._add_recent_file("/x/a.log")  # re-opening moves it to the front

    assert controller.recent_files()[:2] == ["/x/a.log", "/x/b.log"]


def test_recent_files_capped(qtbot, tmp_path):
    _, controller = _make(qtbot)
    controller.settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    for i in range(10):
        controller._add_recent_file(f"/x/{i}.log")

    assert len(controller.recent_files()) == controller.MAX_RECENT_FILES


def test_close_event_persists_geometry(qtbot, tmp_path):
    window = MainWindow(None)
    qtbot.addWidget(window)
    window.settings = QSettings(
        str(tmp_path / "geom.ini"), QSettings.Format.IniFormat
    )

    window.close()

    assert window.settings.value("window_geometry") is not None
