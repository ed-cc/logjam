from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWidgets import QPlainTextEdit, QWidget
from PyQt6.QtGui import QFont, QColor, QPainter, QPaintEvent, QResizeEvent


class QLogFileViewer(QPlainTextEdit):
    def __init__(self, parent=None, is_dark_theme: bool = False):
        super().__init__(parent)
        self.is_dark_theme = is_dark_theme
        self.setReadOnly(True)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.number_bar = self.NumberBar(self)
        self.update_number_bar_width()

    def setText(self, text: str):
        """Compatibility method for QTextBrowser interface"""
        self.setPlainText(text)

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
                    paint_rect, Qt.AlignmentFlag.AlignRight, str(blockNumber + 1)
                )

                block = block.next()

            painter.end()

            QWidget.paintEvent(self, a0)

        def getWidth(self):
            count = self.editor.blockCount()
            width = self.fontMetrics().horizontalAdvance(str(count)) + 10
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
