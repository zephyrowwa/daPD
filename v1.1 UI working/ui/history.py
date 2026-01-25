# ui/history.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QHBoxLayout
)
from styles import BRAND, MUTED, BORD

from PyQt5.QtWidgets import QScrollArea




class HistoryPage(QWidget):
    def __init__(self, on_back, parent=None):
        
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

        super().__init__(parent)

        back = QPushButton("← Back"); back.clicked.connect(on_back)
        back.setStyleSheet(f"QPushButton{{background:transparent;color:{BRAND};border:2px solid {BRAND};border-radius:8px;padding:6px 12px;font:600 12px 'Segoe UI';}}"
                           "QPushButton:hover{background:rgba(37,99,235,0.06);}")
        header = QHBoxLayout(); header.addWidget(back, 0, Qt.AlignLeft); header.addStretch(1)

        title = QLabel("Previous Scans"); title.setAlignment(Qt.AlignCenter); title.setFont(QFont("Segoe UI", 22, QFont.Bold))

        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Patient", "Severity", "Recommended Action", "Date"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        self.table = table  # stored for later wiring

        # previews (placeholders)
        prev_cap = QLabel("Captured"); prev_cap.setAlignment(Qt.AlignCenter); prev_cap.setFrameShape(QFrame.StyledPanel)
        prev_seg = QLabel("Segmented + Grid"); prev_seg.setAlignment(Qt.AlignCenter); prev_seg.setFrameShape(QFrame.StyledPanel)
        previews = QHBoxLayout(); previews.addWidget(prev_cap, 1); previews.addWidget(prev_seg, 1)

        root = QVBoxLayout(self)
        root.addLayout(header)
        root.addWidget(title)
        root.addSpacing(8)
        root.addWidget(table, 3)
        root.addSpacing(8)
        root.addLayout(previews, 2)
