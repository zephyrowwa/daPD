# ui/scan/source_selection.py
"""
Source selection page: Choose between capturing images or uploading them.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt5.QtGui import QFont
from styles import BRAND, ACCENT, MUTED


def primary_button(text):
    """Create primary button matching landing page style."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"QPushButton{{background:{BRAND};color:white;border:none;border-radius:10px;padding:10px 18px;}}"
                    "QPushButton:hover{background:#1d4ed8;} QPushButton:pressed{background:#1e40af;}")
    return b


def outline_button(text):
    """Create outline button matching landing page style."""
    b = QPushButton(text)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(f"QPushButton{{background:transparent;color:{BRAND};border:2px solid {BRAND};border-radius:10px;padding:10px 18px;}}"
                    "QPushButton:hover{background:rgba(37,99,235,0.06);} QPushButton:pressed{background:rgba(37,99,235,0.12);}")
    return b


class SourceSelection(QWidget):
    """Page to select image source: Capture or Upload."""
    
    def __init__(self, on_capture, on_upload, on_back):
        super().__init__()
        self.on_capture = on_capture
        self.on_upload = on_upload
        self.on_back = on_back
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(24)
        main_layout.addStretch()
        
        # Title
        title_label = QLabel("How would you like to scan?")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 18)
        title_font.setWeight(QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #1f2937; padding: 12px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("You will need to provide both left and right foot scans")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Segoe UI", 11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #6b7280; padding: 8px;")
        main_layout.addWidget(subtitle_label)
        
        main_layout.addSpacing(20)
        
        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(16)
        button_row.addStretch()
        
        # Capture button
        self.btn_capture = primary_button("📷 Capture Images")
        self.btn_capture.setMinimumSize(180, 56)
        self.btn_capture.clicked.connect(self.on_capture)
        button_row.addWidget(self.btn_capture)
        
        # Upload button
        self.btn_upload = outline_button("📁 Upload Images")
        self.btn_upload.setMinimumSize(180, 56)
        self.btn_upload.clicked.connect(self.on_upload)
        button_row.addWidget(self.btn_upload)
        
        button_row.addStretch()
        main_layout.addLayout(button_row)
        
        main_layout.addStretch()
