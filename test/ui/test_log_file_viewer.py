from logjam.ui.log_file_viewer import QLogFileViewer
from logjam.core.file_filter_processor import FilteredLine


def test_set_filtered_lines_preserves_original_numbers(qtbot):
    viewer = QLogFileViewer()
    qtbot.addWidget(viewer)

    viewer.set_filtered_lines(
        [FilteredLine(5, "fifth line"), FilteredLine(12, "twelfth line")]
    )

    assert viewer.toPlainText() == "fifth line\ntwelfth line"
    assert viewer.line_number_for_block(0) == 5
    assert viewer.line_number_for_block(1) == 12


def test_set_text_falls_back_to_sequential_numbers(qtbot):
    viewer = QLogFileViewer()
    qtbot.addWidget(viewer)

    viewer.set_filtered_lines([FilteredLine(99, "x")])
    viewer.setText("a\nb")

    # setText clears the original mapping; gutter is sequential again.
    assert viewer.line_number_for_block(0) == 1
    assert viewer.line_number_for_block(1) == 2
