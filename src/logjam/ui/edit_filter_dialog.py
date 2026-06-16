import logging
from PyQt6 import QtWidgets
from logjam.core.filter_config import Filter
from logjam.core.logical_operator import LogicalOperator

logger = logging.getLogger(__name__)


class EditFilterDialog(QtWidgets.QDialog):
    def __init__(self, filter: Filter, parent=None, is_new: bool = False):
        """Initialize the dialog for editing or creating a filter."""
        super().__init__(parent)
        self.filter = filter
        self.is_new = is_new
        self.setup_ui()

    def setup_ui(self):
        self.setGeometry(100, 100, 400, 300)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.setWindowTitle("Edit Filter" if not self.is_new else "New Filter")

        self.filter_name_label = QtWidgets.QLabel("Filter Name:")
        self.filter_name_input = QtWidgets.QLineEdit(self)
        if self.filter:
            self.filter_name_input.setText(self.filter.name)
        else:
            self.filter_name_input.setPlaceholderText("Filter 1")

        self.filter_logic_label = QtWidgets.QLabel("Filter Logic:")
        self.filter_logic_input = QtWidgets.QComboBox(self)
        self.filter_logic_input.addItems(LogicalOperator.get_all_operators())
        if self.filter and self.filter.logical_operator:
            self.filter_logic_input.setCurrentText(self.filter.logical_operator.value)
        else:
            self.filter_logic_input.setCurrentText(LogicalOperator.OR.value)

        self.filter_criteria_label = QtWidgets.QLabel("Filter Criteria:")
        self.filter_criteria_input = QtWidgets.QTextEdit(self)
        if self.filter:
            self.filter_criteria_input.setPlainText(
                self.filter.filter_strings_representation()
            )
        else:
            self.filter_criteria_input.setPlaceholderText(
                "Enter filter criteria separated by new lines..."
            )
        self.filter_criteria_regex = QtWidgets.QCheckBox("Use Regular Expression", self)
        if self.filter and self.filter.regex:
            self.filter_criteria_regex.setChecked(True)
        self.filter_criteria_case_sensitive = QtWidgets.QCheckBox(
            "Case Sensitive", self
        )
        if self.filter and self.filter.case_sensitive:
            self.filter_criteria_case_sensitive.setChecked(self.filter.case_sensitive)

        # Working copy of nested sub-filters, written back on accept.
        self.sub_filters = list(self.filter.sub_filters) if self.filter else []
        self.sub_filter_label = QtWidgets.QLabel("Sub-filters:")
        self.sub_filter_list = QtWidgets.QListWidget(self)
        self.sub_filter_list.itemDoubleClicked.connect(
            lambda _item: self._edit_sub_filter()
        )

        sub_button_row = QtWidgets.QHBoxLayout()
        self.add_sub_button = QtWidgets.QPushButton("Add Sub-filter", self)
        self.add_sub_button.clicked.connect(self._add_sub_filter)
        self.edit_sub_button = QtWidgets.QPushButton("Edit Sub-filter", self)
        self.edit_sub_button.clicked.connect(self._edit_sub_filter)
        self.remove_sub_button = QtWidgets.QPushButton("Remove Sub-filter", self)
        self.remove_sub_button.clicked.connect(self._remove_sub_filter)
        for button in (
            self.add_sub_button,
            self.edit_sub_button,
            self.remove_sub_button,
        ):
            sub_button_row.addWidget(button)

        self.main_layout.addWidget(self.filter_name_label)
        self.main_layout.addWidget(self.filter_name_input)
        self.main_layout.addWidget(self.filter_logic_label)
        self.main_layout.addWidget(self.filter_logic_input)
        self.main_layout.addWidget(self.filter_criteria_label)
        self.main_layout.addWidget(self.filter_criteria_input)
        self.main_layout.addWidget(self.filter_criteria_regex)
        self.main_layout.addWidget(self.filter_criteria_case_sensitive)
        self.main_layout.addWidget(self.sub_filter_label)
        self.main_layout.addWidget(self.sub_filter_list)
        self.main_layout.addLayout(sub_button_row)
        self._refresh_sub_filter_list()
        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        )
        self.button_box.accepted.connect(self.accept)
        self.main_layout.addWidget(self.button_box)
        self.button_box.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.button_box.rejected.connect(self.reject)

    def _refresh_sub_filter_list(self):
        self.sub_filter_list.clear()
        for sub in self.sub_filters:
            self.sub_filter_list.addItem(sub.name)
        has_selection = bool(self.sub_filters)
        self.edit_sub_button.setEnabled(has_selection)
        self.remove_sub_button.setEnabled(has_selection)

    def _unique_sub_name(self, base: str) -> str:
        existing = {sub.name for sub in self.sub_filters}
        name = base
        counter = 2
        while name in existing:
            name = f"{base} {counter}"
            counter += 1
        return name

    def _add_sub_filter(self):
        new_sub = Filter(self._unique_sub_name("Sub-filter 1"), LogicalOperator.OR)
        dialog = EditFilterDialog(new_sub, parent=self, is_new=True)
        dialog.exec()
        if dialog.result() == QtWidgets.QDialog.DialogCode.Accepted:
            self.sub_filters.append(new_sub)
            self._refresh_sub_filter_list()

    def _edit_sub_filter(self):
        row = self.sub_filter_list.currentRow()
        if row < 0:
            return
        dialog = EditFilterDialog(self.sub_filters[row], parent=self, is_new=False)
        dialog.exec()
        if dialog.result() == QtWidgets.QDialog.DialogCode.Accepted:
            self._refresh_sub_filter_list()

    def _remove_sub_filter(self):
        row = self.sub_filter_list.currentRow()
        if row < 0:
            return
        del self.sub_filters[row]
        self._refresh_sub_filter_list()

    def accept(self):
        """Override accept to validate and save the filter."""
        filter_name = self.filter_name_input.text().strip()
        if not filter_name:
            QtWidgets.QMessageBox.warning(
                self, "Invalid Input", "Filter name cannot be empty."
            )
            return

        logical_operator = self.filter_logic_input.currentText()
        filter_strings = [
            s.strip()
            for s in self.filter_criteria_input.toPlainText().splitlines()
            if s.strip()
        ]
        regex = self.filter_criteria_regex.isChecked()
        case_sensitive = self.filter_criteria_case_sensitive.isChecked()

        if not filter_strings and not self.sub_filters:
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "A filter needs at least one criterion or sub-filter.",
            )
            return

        self.filter.name = filter_name
        self.filter.logical_operator = LogicalOperator(logical_operator)
        self.filter.regex = regex
        self.filter.case_sensitive = case_sensitive
        self.filter.filter_strings = filter_strings
        self.filter.sub_filters = self.sub_filters

        super().accept()
        self.done(QtWidgets.QDialog.DialogCode.Accepted)
        logger.info(f"New filter created/edited: {repr(self.filter)}")
