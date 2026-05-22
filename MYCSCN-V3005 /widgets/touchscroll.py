# widgets/touchscroll.py
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QScrollArea


class TouchScrollArea(QScrollArea):
    """
    ScrollArea subclass that enables smooth kinetic/momentum scrolling for touchscreens.
    Works well on Raspberry Pi touchscreens and provides Android-like scrolling experience.
    
    Features:
    - Smooth momentum scrolling after finger release
    - Friction to slow down naturally
    - Bounds checking to prevent over-scroll
    - Works with both mouse and touch events
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea { border: none; }")
        # Hide scroll bars for pure touch experience
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Touch/mouse tracking
        self._press_pos = None
        self._last_pos = None
        self._scroll_start = None
        
        # Kinetic scrolling parameters
        self._velocity = 0.0
        self._friction = 0.98  # Friction coefficient (0-1, higher = smoother decay)
        self._min_velocity = 0.1  # Minimum velocity threshold to continue scrolling
        
        # Animation timer for smooth deceleration
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_scroll)
        self._timer.setInterval(16)  # ~60 FPS

    def mousePressEvent(self, event):
        """Record initial touch/mouse position and stop any ongoing scroll."""
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
            self._last_pos = event.pos()
            self._scroll_start = self.verticalScrollBar().value()
            self._velocity = 0.0
            self._timer.stop()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Track drag movement and update scroll position in real-time."""
        if self._press_pos is not None:
            # Calculate displacement
            current_pos = event.pos()
            dy = current_pos.y() - self._last_pos.y()
            
            # Update scroll position (inverse: drag down = scroll up)
            scrollbar = self.verticalScrollBar()
            scrollbar.setValue(scrollbar.value() - dy)
            
            # Calculate velocity with gentler multiplier
            self._velocity = dy * 0.4  # Reduced from 0.7 for less aggressive momentum
            
            self._last_pos = current_pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Release touch/mouse and start kinetic scroll animation."""
        if self._press_pos is not None:
            # Clamp velocity to a gentler range to avoid aggressive bouncing
            self._velocity = max(min(self._velocity, 8.0), -8.0)
            
            # Only start animation if velocity is significant
            if abs(self._velocity) > 0.1:
                self._timer.start()
        
        self._press_pos = None
        self._last_pos = None
        super().mouseReleaseEvent(event)

    def _update_scroll(self):
        """Update scroll position with decreasing velocity (momentum effect)."""
        if abs(self._velocity) < self._min_velocity:
            self._timer.stop()
            self._velocity = 0.0
            return
        
        # Apply friction to velocity for smooth deceleration
        self._velocity *= self._friction
        
        # Update scroll position
        scrollbar = self.verticalScrollBar()
        new_value = scrollbar.value() + int(self._velocity)
        
        # Bounds checking to prevent over-scroll
        new_value = max(0, min(new_value, scrollbar.maximum()))
        scrollbar.setValue(new_value)
        
        # Stop if we hit a boundary
        if new_value <= 0 or new_value >= scrollbar.maximum():
            self._timer.stop()
            self._velocity = 0.0
