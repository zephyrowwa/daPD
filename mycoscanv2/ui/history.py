# ui/history.py
import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFrame, QScrollArea
)
from styles import BRAND, MUTED, BORD
from widgets.touchscroll import TouchScrollArea


def _thumb(path, size=(120,120)):
    if not os.path.exists(path): 
        return QPixmap()
    pix = QPixmap(path)
    return pix.scaled(size[0], size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)


class HistoryPage(QWidget):
    def __init__(self, on_back, parent=None):
        super().__init__(parent)

        back = QPushButton("← Back")
        back.clicked.connect(on_back)
        back.setStyleSheet(
            f"QPushButton{{background:transparent;color:{BRAND};"
            f"border:2px solid {BRAND};border-radius:8px;"
            "padding:4px 10px;font-family:'DejaVu Sans','Segoe UI';"
            "font-size:12px;font-weight:600;}}"
            "QPushButton:hover{background:rgba(37,99,235,0.06);}"
        )
        header = QHBoxLayout()
        header.addWidget(back, 0, Qt.AlignLeft)
        header.addStretch(1)

        title = QLabel("Previous Scans")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))

        # main content wrapped in scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                background: #f1f5f9;
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #9ca3af;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
        """)
        container = QWidget()
        scroll.setWidget(container)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Patient", "Severity", "Recommended Action", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        # previews
        self.prev_cap = QLabel("Captured")
        self.prev_cap.setAlignment(Qt.AlignCenter)
        self.prev_cap.setFrameShape(QFrame.StyledPanel)

        self.prev_seg = QLabel("Segmented + Grid")
        self.prev_seg.setAlignment(Qt.AlignCenter)
        self.prev_seg.setFrameShape(QFrame.StyledPanel)

        previews = QHBoxLayout()
        previews.addWidget(self.prev_cap, 1)
        previews.addWidget(self.prev_seg, 1)

        layout_inside = QVBoxLayout(container)
        layout_inside.addWidget(self.table)
        layout_inside.addSpacing(8)
        layout_inside.addLayout(previews)

        # root layout
        root = QVBoxLayout(self)
        root.addLayout(header)
        root.addWidget(title)
        root.addSpacing(6)
        root.addWidget(scroll)

        # dummy sample data for UI preview (optional)
        self._load_dummy_rows()

    def _load_dummy_rows(self):
        # purely for UI preview; remove later
        for i in range(8):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(f"Patient {i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem("Moderate"))
            self.table.setItem(i, 2, QTableWidgetItem("Consult dermatologist"))
            self.table.setItem(i, 3, QTableWidgetItem("2025-10-23"))
