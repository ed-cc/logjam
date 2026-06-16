from logjam.ui.app import MainWindow
from logjam.ui.controller import AppController
from logjam.core.filter_config import Filter, LogicalOperator
from test.common import make_input_file


def _make(qtbot):
    window = MainWindow(None)
    controller = AppController(window)
    window.controller = controller
    qtbot.addWidget(window)
    controller.threadpool.waitForDone(2000)
    return window, controller


def test_add_filter_populates_panel(qtbot):
    window, controller = _make(qtbot)

    controller.add_filter(
        Filter(name="alpha", logical_operator=LogicalOperator.OR, filter_strings=["a"])
    )
    controller.add_filter(
        Filter(name="beta", logical_operator=LogicalOperator.OR, filter_strings=["b"])
    )
    controller.threadpool.waitForDone(2000)
    window.refresh_filter_panel()

    labels = [
        window.filter_list.item(i).text() for i in range(window.filter_list.count())
    ]
    assert labels == ["alpha", "beta"]


def test_selecting_filter_changes_active_and_results(qtbot):
    window, controller = _make(qtbot)

    controller.open_file(make_input_file())
    controller.add_filter(
        Filter(name="foos", logical_operator=LogicalOperator.OR, filter_strings=["foo"])
    )
    controller.add_filter(
        Filter(name="quxs", logical_operator=LogicalOperator.OR, filter_strings=["qux"])
    )
    qtbot.waitUntil(
        lambda: window.textBrowser.toPlainText() != "", timeout=3000
    )

    # Select the "foos" filter via the panel and confirm the view follows.
    foos_row = next(
        i
        for i in range(window.filter_list.count())
        if window.filter_list.item(i).text() == "foos"
    )
    window.filter_list.setCurrentRow(foos_row)
    qtbot.waitUntil(
        lambda: "foo bar baz" in window.textBrowser.toPlainText(), timeout=3000
    )
    assert controller.active_filter_name == "foos"
    assert "baz qux" not in window.textBrowser.toPlainText()


def test_remove_filter_picks_new_active(qtbot):
    window, controller = _make(qtbot)
    controller.add_filter(
        Filter(name="one", logical_operator=LogicalOperator.OR, filter_strings=["1"])
    )
    controller.add_filter(
        Filter(name="two", logical_operator=LogicalOperator.OR, filter_strings=["2"])
    )
    controller.threadpool.waitForDone(2000)

    controller.remove_filter("two")
    controller.threadpool.waitForDone(2000)

    assert controller.filter_config.filter_names() == ["one"]
    assert controller.active_filter_name == "one"


def test_duplicate_filter_creates_unique_name(qtbot):
    _, controller = _make(qtbot)
    controller.add_filter(
        Filter(name="base", logical_operator=LogicalOperator.OR, filter_strings=["x"])
    )
    controller.threadpool.waitForDone(2000)

    controller.duplicate_filter("base")
    controller.threadpool.waitForDone(2000)

    assert "base copy" in controller.filter_config.filter_names()
