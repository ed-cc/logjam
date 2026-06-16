from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QPlainTextEdit, QTextEdit, QWidget
from PyQt6.QtGui import (
    QFont,
    QColor,
    QPainter,
    QPaintEvent,
    QResizeEvent,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)


class QLogFileViewer(QPlainTextEdit):
    def __init__(self, parent=None, is_dark_theme: bool = False):
        super().__init__(parent)
        self.is_dark_theme = is_dark_theme
        self._line_numbers: list[int] = []
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.number_bar = self.NumberBar(self)
        self.update_number_bar_width()

    def setText(self, text: str):
        """Compatibility method for QTextBrowser interface.

        Clears any original line-number mapping so the gutter falls back to
        sequential numbering.
        """
        self._line_numbers = []
        self.setPlainText(text)
        self.update_number_bar_width()

    def set_filtered_lines(self, filtered_lines):
        """Display filtered lines, keeping each line's original source number.

        ``filtered_lines`` is a sequence of objects exposing ``line_number``
        and ``line_content`` (e.g. :class:`FilteredLine`).
        """
        self._line_numbers = [fl.line_number for fl in filtered_lines]
        self.setPlainText("\n".join(fl.line_content for fl in filtered_lines))
        self.update_number_bar_width()

    def highlight_matches(self, text: str) -> int:
        """Highlight every occurrence of ``text`` and return the match count."""
        selections = []
        if text:
            color = QColor("#665c00") if self.is_dark_theme else QColor("#fff2a8")
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            document = self.document()
            cursor = QTextCursor(document)
            while True:
                cursor = document.find(text, cursor)
                if cursor.isNull():
                    break
                selection = QTextEdit.ExtraSelection()
                selection.format = fmt
                selection.cursor = cursor
                selections.append(selection)
        self.setExtraSelections(selections)
        return len(selections)

    def find_next(
        self, text: str, forward: bool = True, from_start: bool = False
    ) -> bool:
        """Move the cursor to the next match of ``text``; return True on a hit."""
        if not text:
            return False
        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        if from_start:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.setTextCursor(cursor)
        return self.find(text, flags)

    def line_number_for_block(self, block_number: int) -> int:
        """Return the original source line number for a displayed block.

        Falls back to 1-based sequential numbering when no mapping is set.
        """
        if 0 <= block_number < len(self._line_numbers):
            return self._line_numbers[block_number]
        return block_number + 1

    def resizeEvent(self, e: QResizeEvent | None):
        """Handle resize events to update number bar position"""
        super().resizeEvent(e)
        if e is not None:
            content_rect = self.contentsRect()
            self.number_bar.setGeometry(
                content_rect.left(),
                content_rect.top(),
                self.number_bar.getWidth(),
                content_rect.height(),
            )

    def paintEvent(self, e: QPaintEvent | None):
        """Override paint event to also update number bar"""
        super().paintEvent(e)
        self.number_bar.update()

    def update_number_bar_width(self):
        """Update the width of the number bar"""
        self.number_bar.updateWidth()

    class NumberBar(QWidget):
        """class that deifnes textEditor numberBar"""

        def __init__(self, editor):
            super().__init__(editor)

            self.editor = editor
            self.editor.blockCountChanged.connect(self.updateWidth)
            self.editor.updateRequest.connect(self.updateContents)
            self._font = QFont()
            if self.editor.is_dark_theme:
                self.numberBarColor = QColor("#656565")
            else:
                self.numberBarColor = QColor("#cacaca")

        def paintEvent(self, a0: QPaintEvent | None):
            if a0 is None:
                return

            painter = QPainter(self)
            painter.fillRect(a0.rect(), self.numberBarColor)

            block = self.editor.firstVisibleBlock()

            while block.isValid():
                blockNumber = block.blockNumber()
                block_top = (
                    self.editor.blockBoundingGeometry(block)
                    .translated(self.editor.contentOffset())
                    .top()
                )

                if not block.isVisible() or block_top >= a0.rect().bottom():
                    break

                if blockNumber == self.editor.textCursor().blockNumber():
                    self._font.setBold(True)
                    if self.editor.is_dark_theme:
                        painter.setPen(QColor("#ffffff"))
                    else:
                        painter.setPen(QColor("#000000"))
                else:
                    self._font.setBold(False)
                    if self.editor.is_dark_theme:
                        painter.setPen(QColor("#cccccc"))
                    else:
                        painter.setPen(QColor("#717171"))
                painter.setFont(self._font)

                margin = 5
                paint_rect = QRect(
                    0,
                    int(block_top),
                    self.width() - margin,
                    self.editor.fontMetrics().height(),
                )
                painter.drawText(
                    paint_rect,
                    Qt.AlignmentFlag.AlignRight,
                    str(self.editor.line_number_for_block(blockNumber)),
                )

                block = block.next()

            painter.end()

            QWidget.paintEvent(self, a0)

        def getWidth(self):
            # Size for the largest line number actually shown so original
            # source numbers (which may exceed the block count) still fit.
            last_block = self.editor.blockCount() - 1
            largest = self.editor.line_number_for_block(last_block)
            width = self.fontMetrics().horizontalAdvance(str(largest)) + 10
            return width

        def updateWidth(self):
            width = self.getWidth()
            if self.width() != width:
                self.setFixedWidth(width)
                self.editor.setViewportMargins(width, 0, 0, 0)

        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update(0, rect.y(), self.width(), rect.height())

            if rect.contains(self.editor.viewport().rect()):
                editor_font_size = self.editor.currentCharFormat().font().pointSize()
                if editor_font_size > 0:
                    number_font_size = max(8, editor_font_size - 1)
                else:
                    number_font_size = 9

                self._font.setPointSize(number_font_size)
                self._font.setStyle(QFont.Style.StyleNormal)
                self.updateWidth()
