from logjam.ui.app import MainWindow
from logjam.ui.controller import AppController
from logjam.core.filter_config import FilterConfig, Filter, LogicalOperator
from test.common import make_input_file, make_filter_config_file


def _make_controller(qtbot):
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller
    qtbot.addWidget(window)
    controller.threadpool.waitForDone(2000)
    return window, controller


def test_filter_file_path_defaults_to_none(qtbot):
    _, controller = _make_controller(qtbot)
    # Previously this attribute was never initialised, so saving before
    # loading a filter raised AttributeError.
    assert controller.filter_file_path is None


def test_run_filter_processing_combines_file_and_config(qtbot):
    _, controller = _make_controller(qtbot)

    config = FilterConfig()
    config.add_filter(
        Filter(name="f", logical_operator=LogicalOperator.OR, filter_strings=["foo"])
    )
    controller.file_filter_processor.file_path = make_input_file()
    controller.file_filter_processor.filter_config = config

    result = controller._run_filter_processing()
    assert "foo bar baz" in result
    assert "baz qux" not in result


def test_open_file_then_load_filter_updates_view(qtbot):
    window, controller = _make_controller(qtbot)

    controller.open_file(make_input_file())
    controller.load_filters(make_filter_config_file())

    qtbot.waitUntil(
        lambda: "foo bar baz" in window.textBrowser.toPlainText(), timeout=3000
    )
    assert "baz qux" not in window.textBrowser.toPlainText()
