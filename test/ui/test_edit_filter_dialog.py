from PyQt6 import QtWidgets

from logjam.ui.edit_filter_dialog import EditFilterDialog
from logjam.core.filter_config import Filter, LogicalOperator


def test_dialog_lists_existing_sub_filters(qtbot):
    sub = Filter("child", LogicalOperator.OR, filter_strings=["x"])
    parent = Filter(
        "parent", LogicalOperator.OR, filter_strings=["y"], sub_filters=[sub]
    )
    dialog = EditFilterDialog(parent)
    qtbot.addWidget(dialog)

    assert dialog.sub_filter_list.count() == 1
    assert dialog.sub_filter_list.item(0).text() == "child"


def test_accept_persists_criteria_and_sub_filters(qtbot):
    f = Filter("f", LogicalOperator.AND, filter_strings=["old"])
    dialog = EditFilterDialog(f)
    qtbot.addWidget(dialog)

    dialog.filter_name_input.setText("renamed")
    dialog.filter_logic_input.setCurrentText("OR")
    dialog.filter_criteria_input.setPlainText("a\nb")
    dialog.sub_filters.append(
        Filter("child", LogicalOperator.OR, filter_strings=["z"])
    )

    dialog.accept()

    assert f.name == "renamed"
    assert f.logical_operator == LogicalOperator.OR
    assert f.filter_strings == ["a", "b"]
    assert [s.name for s in f.sub_filters] == ["child"]


def test_accept_allows_filter_with_only_sub_filters(qtbot):
    f = Filter("f", LogicalOperator.OR)
    dialog = EditFilterDialog(f, is_new=True)
    qtbot.addWidget(dialog)

    dialog.filter_name_input.setText("f")
    dialog.sub_filters.append(
        Filter("child", LogicalOperator.OR, filter_strings=["z"])
    )

    dialog.accept()

    assert dialog.result() == QtWidgets.QDialog.DialogCode.Accepted
    assert f.filter_strings == []
    assert f.sub_filters[0].name == "child"


def test_remove_sub_filter(qtbot):
    sub = Filter("child", LogicalOperator.OR, filter_strings=["x"])
    parent = Filter("parent", LogicalOperator.OR, sub_filters=[sub])
    dialog = EditFilterDialog(parent)
    qtbot.addWidget(dialog)

    dialog.sub_filter_list.setCurrentRow(0)
    dialog._remove_sub_filter()

    assert dialog.sub_filter_list.count() == 0
    assert dialog.sub_filters == []
