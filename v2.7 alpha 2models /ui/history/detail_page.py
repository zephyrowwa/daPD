# ui/history/detail_page.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
import cv2, os


def bgr_to_qpixmap(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class DetailPage(QDialog):
    """Modal popup showing scan details and image."""

    def __init__(self, name, severity, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Details")
        self.setModal(True)  # ✅ block background while open
        self.setFixedSize(420, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 16px;
            }
            QLabel {
                color: #111827;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title labels
        lbl_title = QLabel(f"👤 Patient: {name}")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font:700 18px 'Segoe UI';")

        lbl_sev = QLabel(f"🩺 Severity: {severity}")
        lbl_sev.setAlignment(Qt.AlignCenter)
        lbl_sev.setStyleSheet("font:600 16px 'Segoe UI'; color:#1f2937;")

        # Image preview
        lbl_img = QLabel()
        lbl_img.setAlignment(Qt.AlignCenter)
        lbl_img.setStyleSheet("border:1px solid #d1d5db; border-radius:8px; background:#f9fafb;")
        if os.path.exists(image_path):
            img = cv2.imread(image_path)
            pix = bgr_to_qpixmap(img).scaled(360, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_img.setPixmap(pix)
        else:
            lbl_img.setText("Image not found")

        # Close button
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(42)
        btn_close.clicked.connect(self.accept)  # ✅ closes dialog

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_sev)
        layout.addWidget(lbl_img)
        layout.addStretch(1)
        layout.addWidget(btn_close, 0, Qt.AlignCenter)
