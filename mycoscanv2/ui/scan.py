# ui/scan.py
# near top
from widgets.touchscroll import TouchScrollArea
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout,
    QSizePolicy, QStackedWidget, QGroupBox, QScrollArea
)
from styles import BRAND, ACCENT, MUTED, BORD


class ScanPage(QWidget):
    """
    Two-step scan UI with right-side controls and scrollable content
    for the small Raspberry Pi touchscreen.
    """
    def __init__(self, on_back, parent=None):
        super().__init__(parent)

        # ---------- Top bar ----------
        btn_back = QPushButton("← Back")
        btn_back.clicked.connect(on_back)
        btn_back.setStyleSheet(
            f"QPushButton{{background:transparent;color:{BRAND};"
            f"border:2px solid {BRAND};border-radius:8px;"
            "padding:4px 10px;font-family:'DejaVu Sans','Segoe UI';"
            "font-size:12px;font-weight:600;}}"
            "QPushButton:hover{background:rgba(37,99,235,0.06);}"
        )
        top = QHBoxLayout()
        top.addWidget(btn_back, 0, Qt.AlignLeft)
        top.addStretch(1)

        # ---------- Stacked content ----------
        self.stack = QStackedWidget(self)

        # === PAGE 1: CAPTURE ===
        self.page_capture = QWidget()
        preview = QLabel("Camera Preview")
        preview.setAlignment(Qt.AlignCenter)
        preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        preview.setMinimumSize(460, 300)
        preview.setStyleSheet(f"border:1px dashed {BORD}; border-radius:12px; color:{MUTED};")

        btn_capture = QPushButton("Capture")
        btn_capture.setFixedWidth(100)
        btn_capture.setMinimumHeight(60)
        btn_capture.setStyleSheet(
            f"QPushButton{{background:{ACCENT};color:white;border:none;"
            "border-radius:10px;padding:8px 14px;"
            "font-family:'DejaVu Sans','Segoe UI';font-size:14px;font-weight:700;}}"
            "QPushButton:hover{background:#15803d;}"
        )
        btn_capture.clicked.connect(self._goto_result)  # UI-only

        right_controls = QVBoxLayout()
        right_controls.addStretch(1)
        right_controls.addWidget(btn_capture, 0, Qt.AlignHCenter)
        right_controls.addStretch(1)

        row = QHBoxLayout(self.page_capture)
        row.addWidget(preview, 3)
        row.addSpacing(8)
        row.addLayout(right_controls, 1)

        # === PAGE 2: RESULT ===
        self.page_result = QWidget()

        # --- scroll area ---
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

        lbl_cap = QLabel("Captured (1:1)")
        lbl_cap.setAlignment(Qt.AlignCenter)
        lbl_cap.setFont(QFont("Segoe UI", 10, QFont.DemiBold))

        lbl_seg = QLabel("Segmented + Grid")
        lbl_seg.setAlignment(Qt.AlignCenter)
        lbl_seg.setFont(QFont("Segoe UI", 10, QFont.DemiBold))

        self.view_cap = QLabel("(captured image)")
        self.view_cap.setAlignment(Qt.AlignCenter)
        self.view_cap.setMinimumSize(220, 220)
        self.view_cap.setStyleSheet(f"border:1px solid {BORD}; border-radius:8px; color:{MUTED};")

        self.view_seg = QLabel("(segmented output)")
        self.view_seg.setAlignment(Qt.AlignCenter)
        self.view_seg.setMinimumSize(220, 220)
        self.view_seg.setStyleSheet(f"border:1px solid {BORD}; border-radius:8px; color:{MUTED};")

        grid = QGridLayout()
        grid.addWidget(lbl_cap, 0, 0)
        grid.addWidget(lbl_seg, 0, 1)
        grid.addWidget(self.view_cap, 1, 0)
        grid.addWidget(self.view_seg, 1, 1)

        self.lbl_severity = QLabel("Severity: —")
        self.lbl_severity.setAlignment(Qt.AlignCenter)
        self.lbl_severity.setFont(QFont("Segoe UI", 11, QFont.Black))

        reco_box = QGroupBox("Recommended Action (coming soon)")
        reco_v = QVBoxLayout(reco_box)
        reco_txt = QLabel("—")
        reco_txt.setAlignment(Qt.AlignCenter)
        reco_txt.setStyleSheet(f"color:{MUTED};")
        reco_v.addWidget(reco_txt)

        # slimmer buttons on the right
        btn_retake = QPushButton("Retake")
        btn_retake.setFixedWidth(110)
        btn_retake.setMinimumHeight(46)
        btn_retake.setStyleSheet(
            f"QPushButton{{background:transparent;color:{BRAND};border:2px solid {BRAND};"
            "border-radius:10px;padding:6px 10px;"
            "font-family:'DejaVu Sans','Segoe UI';font-size:13px;font-weight:700;}}"
            "QPushButton:hover{background:rgba(37,99,235,0.06);}"
        )
        btn_retake.clicked.connect(self._goto_capture)

        btn_save = QPushButton("Save Result")
        btn_save.setFixedWidth(110)
        btn_save.setMinimumHeight(46)
        btn_save.setStyleSheet(
            f"QPushButton{{background:{BRAND};color:white;border:none;"
            "border-radius:10px;padding:6px 10px;"
            "font-family:'DejaVu Sans','Segoe UI';font-size:13px;font-weight:700;}}"
            "QPushButton:hover{{background:#1d4ed8;}}"
        )

        right_res_controls = QVBoxLayout()
        right_res_controls.addStretch(1)
        right_res_controls.addWidget(btn_retake, 0, Qt.AlignHCenter)
        right_res_controls.addSpacing(8)
        right_res_controls.addWidget(btn_save, 0, Qt.AlignHCenter)
        right_res_controls.addStretch(1)

        left_col = QVBoxLayout()
        left_col.addLayout(grid)
        left_col.addSpacing(6)
        left_col.addWidget(self.lbl_severity)
        left_col.addSpacing(4)
        left_col.addWidget(reco_box)
        left_col.addStretch(1)

        inner = QHBoxLayout(container)
        inner.addLayout(left_col, 3)
        inner.addSpacing(8)
        inner.addLayout(right_res_controls, 1)

        layout_result = QVBoxLayout(self.page_result)
        layout_result.addWidget(scroll)

        # add to stack
        self.stack.addWidget(self.page_capture)
        self.stack.addWidget(self.page_result)
        self.stack.setCurrentIndex(0)

        # ---------- Root layout ----------
        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addSpacing(6)
        root.addWidget(self.stack, 1)

    # ----- internal view switches -----
    def _goto_result(self):
        self.stack.setCurrentIndex(1)

    def _goto_capture(self):
        self.stack.setCurrentIndex(0)
