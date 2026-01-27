# widgets/touchscroll.py
from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtWidgets import QScrollArea


class TouchScrollArea(QScrollArea):
    """
    ScrollArea subclass that enables kinetic / momentum scrolling by finger drag.
    Works well on Raspberry Pi touchscreens.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; }")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._press_pos = None
        self._scroll_start = None
        self._velocity = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_scroll)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
            self._scroll_start = self.verticalScrollBar().value()
            self._velocity = 0
            self._timer.stop()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press_pos is not None:
            dy = event.pos().y() - self._press_pos.y()
            self.verticalScrollBar().setValue(self._scroll_start - dy)
            # simple velocity estimation
            self._velocity = -dy
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._press_pos is not None:
            # start kinetic scroll
            self._velocity = max(min(self._velocity, 60), -60)
            self._timer.start(16)
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def _update_scroll(self):
        sb = self.verticalScrollBar()
        sb.setValue(sb.value() + int(self._velocity))
        # friction
        self._velocity *= 0.90
        if abs(self._velocity) < 0.5:
            self._timer.stop()
