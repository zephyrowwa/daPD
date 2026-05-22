# ui/landing.py
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QIcon
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from styles import BRAND, MUTED
import os

def h1(t): 
    l=QLabel(t); l.setAlignment(Qt.AlignCenter); l.setFont(QFont("Segoe UI",26,QFont.Bold)); l.setStyleSheet("color:#111827;"); return l
def sub(t):
    l=QLabel(t); l.setAlignment(Qt.AlignCenter); l.setWordWrap(True); l.setFont(QFont("Segoe UI",11)); l.setStyleSheet(f"color:{MUTED};"); return l

def primary(text):
    b=QPushButton(text); b.setCursor(Qt.PointingHandCursor); b.setMinimumSize(180, 56)
    b.setStyleSheet(f"QPushButton{{background:{BRAND};color:white;border:none;border-radius:10px;padding:10px 18px;}}"
                    "QPushButton:hover{background:#1d4ed8;} QPushButton:pressed{background:#1e40af;}")
    return b

def outline(text):
    b=QPushButton(text); b.setCursor(Qt.PointingHandCursor); b.setMinimumSize(180, 56)
    b.setStyleSheet(f"QPushButton{{background:transparent;color:{BRAND};border:2px solid {BRAND};border-radius:10px;padding:10px 18px;}}"
                    "QPushButton:hover{background:rgba(37,99,235,0.06);} QPushButton:pressed{background:rgba(37,99,235,0.12);}")
    return b

class LandingPage(QWidget):
    def __init__(self, on_start_scan, on_view_history, on_servo_control=None, parent=None):
        super().__init__(parent); self.setObjectName("Canvas")
        title = h1("Welcome to MycoScan")
        subtitle = sub("Deep Learning assisted nail analysis for onychomycosis.\nChoose an option to get started.")
        start = primary("Start a Scan"); start.clicked.connect(on_start_scan)
        hist  = outline("View Previous Scans"); hist.clicked.connect(on_view_history)
        badge = self._badge()

        # Exit button in top right
        exit_btn = QPushButton()
        exit_btn.setFixedSize(50, 50)
        exit_btn.setCursor(Qt.PointingHandCursor)
        
        # Load and set the X icon
        x_icon_path = os.path.join(os.path.dirname(__file__), "x.svg")
        if os.path.exists(x_icon_path):
            x_icon = QIcon(x_icon_path)
            exit_btn.setIcon(x_icon)
            exit_btn.setIconSize(QSize(32, 32))
        
        exit_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
            """
        )
        exit_btn.clicked.connect(lambda: __import__('sys').exit(0))

        row = QHBoxLayout(); row.addStretch(1); row.addWidget(start); row.addSpacing(12); row.addWidget(hist); row.addStretch(1)
        root = QVBoxLayout(self)
        
        # Top bar with exit button
        top_bar = QHBoxLayout()
        top_bar.addStretch(1)
        top_bar.addWidget(exit_btn, 0, Qt.AlignRight | Qt.AlignTop)
        top_bar.setContentsMargins(0, 8, 16, 0)
        top_bar.setSpacing(0)
        root.addLayout(top_bar)
        
        root.addSpacing(16); root.addWidget(badge, 0, Qt.AlignCenter)
        root.addSpacing(6); root.addWidget(title); root.addWidget(subtitle)
        root.addSpacing(18); root.addLayout(row); root.addStretch(1)

    def _badge(self):
        size=QSize(96,96); pix=QPixmap(size); pix.fill(Qt.transparent)
        p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing,True)
        p.setBrush(QColor(BRAND)); p.setPen(Qt.NoPen); p.drawEllipse(0,0,size.width(),size.height())
        p.setBrush(QColor(255,255,255,230)); p.drawEllipse(16,16,64,64)
        p.setBrush(QColor(22,163,74)); p.drawEllipse(56,24,14,14); p.end()
        l=QLabel(); l.setPixmap(pix); l.setFixedSize(size); return l
