# ui/scan/scan_page.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QPushButton
from styles import BRAND
from ui.scan.camera_view import CameraView
from ui.scan.result_view import ResultView
from analysis.segmentation import NailSegmentation, run_full_analysis


class ScanPage(QWidget):



    """Controller that switches between CameraView and ResultView."""

    def __init__(self, on_back, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.on_back = on_back


        # Main stacked pages (camera + result)
        self.stack = QStackedWidget(self)
        self.camera_view = CameraView(on_capture=self.show_result_page)
        self.result_view = ResultView(on_newscan=self.show_camera_page, db=self.db)
        self.stack.addWidget(self.camera_view)
        self.stack.addWidget(self.result_view)

        MODEL_PATH = "best.pt"
        self.segmenter = NailSegmentation(MODEL_PATH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Floating Back button — always visible and above everything
        self.btn_back = QPushButton("←")
        self.btn_back.setParent(self)
        self.btn_back.setFixedSize(48, 32)
        self.btn_back.clicked.connect(self.handle_back)
        self.btn_back.raise_()  # ensure on top of all
        self.btn_back.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,0.85);
                color: {BRAND};
                border: 1.5px solid {BRAND};
                border-radius: 6px;
                font-family: 'DejaVu Sans','Segoe UI';
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.95); }}
            """
        )

        # Ensure the button is initially visible
        self.btn_back.show()

    # ---------- Event Handlers ----------
    def showEvent(self, e):
        """Whenever the Scan page becomes visible again, make sure the camera runs."""
        try:
            self.camera_view.start_camera()
        except Exception:
            pass
        # keep the floating back button on top
        self.btn_back.raise_()
        super().showEvent(e)

    def resizeEvent(self, event):
        """Keep the back button in the top-left corner."""
        self.btn_back.move(10, 10)
        super().resizeEvent(event)

    def handle_back(self):
        """Back to landing: stop camera cleanly, then navigate out."""
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        self.on_back()

    # ---------- Page Navigation ----------
    def show_result_page(self, cropped_bgr):
        print("[ScanPage] Running YOLO segmentation + OSI scoring...")
        result_img, severity, recommendation = run_full_analysis(
            "best.pt",
            cropped_bgr
        )
        self.result_view.show_result(result_img, severity, recommendation, cropped_bgr)
        self.stack.setCurrentWidget(self.result_view)
        self.btn_back.raise_()

    def show_camera_page(self):
        """Return from result → camera preview, (re)start camera."""
        try:
            self.camera_view.start_camera()
        except Exception:
            pass
        self.stack.setCurrentWidget(self.camera_view)
        self.btn_back.raise_()
        print("[ScanPage] Returning to camera preview.")

    def closeEvent(self, e):
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        super().closeEvent(e)
