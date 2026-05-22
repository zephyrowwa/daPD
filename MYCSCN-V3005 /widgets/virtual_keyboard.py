"""Virtual on-screen keyboard widget for touchscreen input."""

from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QColor


class VirtualKeyboard(QWidget):
    """On-screen virtual keyboard that appears when text input is focused."""
    
    key_pressed = pyqtSignal(str)  # Emits character or special key name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:pressed {
                background-color: #555;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton#funcBtn {
                background-color: #5a4a3a;
            }
            QPushButton#funcBtn:pressed {
                background-color: #8a7a6a;
            }
            QLabel {
                color: #888;
                font-size: 9px;
                padding: 4px;
            }
        """)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the keyboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(4)
        
        # Row 1: Numbers
        row1_layout = QHBoxLayout()
        for char in '1234567890':
            btn = self._create_button(char)
            row1_layout.addWidget(btn)
        main_layout.addLayout(row1_layout)
        
        # Row 2: QWERTY
        row2_layout = QHBoxLayout()
        for char in 'QWERTYUIOP':
            btn = self._create_button(char)
            row2_layout.addWidget(btn)
        main_layout.addLayout(row2_layout)
        
        # Row 3: ASDFGH...
        row3_layout = QHBoxLayout()
        for char in 'ASDFGHJKL':
            btn = self._create_button(char)
            row3_layout.addWidget(btn)
        main_layout.addLayout(row3_layout)
        
        # Row 4: ZXCVBN... + Backspace
        row4_layout = QHBoxLayout()
        for char in 'ZXCVBNM':
            btn = self._create_button(char)
            row4_layout.addWidget(btn)
        
        backspace_btn = QPushButton('BACKSPACE')
        backspace_btn.setObjectName('funcBtn')
        backspace_btn.setMinimumWidth(100)
        backspace_btn.clicked.connect(lambda: self.key_pressed.emit('BACKSPACE'))
        row4_layout.addWidget(backspace_btn)
        main_layout.addLayout(row4_layout)
        
        # Row 5: Space, Enter, and Close buttons
        row5_layout = QHBoxLayout()
        
        space_btn = QPushButton('SPACE')
        space_btn.setMinimumWidth(200)
        space_btn.clicked.connect(lambda: self.key_pressed.emit(' '))
        row5_layout.addWidget(space_btn)
        
        enter_btn = QPushButton('ENTER')
        enter_btn.setObjectName('funcBtn')
        enter_btn.setMinimumWidth(100)
        enter_btn.clicked.connect(lambda: self.key_pressed.emit('ENTER'))
        row5_layout.addWidget(enter_btn)
        
        close_btn = QPushButton('CLOSE')
        close_btn.setObjectName('funcBtn')
        close_btn.setMinimumWidth(80)
        close_btn.clicked.connect(self.hide)
        row5_layout.addWidget(close_btn)
        
        main_layout.addLayout(row5_layout)
        
        self.setMinimumSize(600, 200)
        self.hide()
    
    def _create_button(self, char):
        """Create a button for a character."""
        btn = QPushButton(char)
        btn.setMinimumSize(40, 40)
        btn.clicked.connect(lambda: self.key_pressed.emit(char.lower()))
        return btn
    
    def show_at_bottom(self, parent_widget=None):
        """Show the keyboard at the bottom of the screen or parent widget."""
        if parent_widget:
            # Position relative to parent
            geometry = parent_widget.geometry()
            self.move(geometry.x(), geometry.y() + geometry.height() - self.height())
        else:
            # Position at bottom of screen
            screen = self.screen()
            screen_geometry = screen.geometry()
            self.move(
                (screen_geometry.width() - self.width()) // 2,
                screen_geometry.height() - self.height() - 10
            )
        self.show()
    
    def hide_keyboard(self):
        """Hide the keyboard."""
        self.hide()
