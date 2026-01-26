# ui/scan/result_view.py
from time import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QGroupBox, QInputDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
import os, cv2
from styles import BRAND, ACCENT, BORD, MUTED



def bgr_to_qpixmap(frame_bgr, fit=(280, 280)):
    """Convert BGR ndarray to scaled QPixmap."""
    if frame_bgr is None:
        return QPixmap()
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    pix = QPixmap.fromImage(qimg)
    if fit:
        return pix.scaled(fit[0], fit[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pix


class ResultView(QWidget):
    """Displays YOLO-segmented image, OSI grid, severity, and recommendation."""

    def __init__(self, on_newscan, db):
        super().__init__()
        self.on_newscan = on_newscan
        self.db = db

        self.segmented_img = None
        self.captured_path = None
        self.segmented_path = None
        self.severity = None
        self.recommend = None

        # ===== ROOT LAYOUT =====
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        # ===== SCROLL AREA FOR MULTI-NAIL RESULTS =====
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(16)

        self.results_scroll.setWidget(self.results_container)
        root.addWidget(self.results_scroll, 1)

        # ===== ACTION BUTTONS =====
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)

        self.btn_newscan = QPushButton("New Scan")
        self.btn_newscan.setFixedSize(140, 44)
        self.btn_newscan.clicked.connect(self.on_newscan)

        self.btn_save = QPushButton("Save Result")
        self.btn_save.setFixedSize(140, 44)
        self.btn_save.clicked.connect(self.save_to_db)

        btn_row.addWidget(self.btn_newscan)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.btn_save)

        root.addLayout(btn_row)


    # =======================================================
    #             UI UPDATE ENTRY POINT
    # =======================================================

    def clear_results(self):
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


    def show_results(self, results):
        print(f"[ResultView] Nails detected: {len(results)}")

        self.clear_results()

        for res in results:
            card = self.create_nail_card(
                res["image"],
                res["severity"]
            )
            self.results_layout.addWidget(card)

        self.results_layout.addStretch()

    def update_image(self, img_bgr):
        """Display OpenCV BGR image in QLabel."""
        import cv2
        from PyQt5.QtGui import QImage, QPixmap

        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )

        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )


    def save_to_db(self):
        if not self.captured_path or not self.segmented_path:
            QMessageBox.warning(self, "No image", "Nothing to save.")
            return
        name, ok = QInputDialog.getText(self, "Save Scan", "Enter patient name:")
        if not ok or not name.strip():
            return
        try:
            scan_id = self.db.add_scan(
                patient_name=name.strip(),
                severity=self.severity,
                captured_path=self.captured_path,
                segmented_path=self.segmented_path,
                recommended_action=self.recommend or "",
            )
            QMessageBox.information(self, "Saved", f"Scan #{scan_id} saved.")
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Failed to save: {e}")


    def create_nail_card(self, img, severity):
        from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
        from PyQt5.QtGui import QImage, QPixmap
        import cv2

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(card)

        # Image
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setFixedHeight(200)

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)

        img_label.setPixmap(pix.scaled(
            img_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

        # Severity
        sev_label = QLabel(f"Severity: {severity}")
        sev_label.setAlignment(Qt.AlignCenter)
        sev_label.setStyleSheet(
            "font-weight: 600; font-size: 15px;"
        )

        layout.addWidget(img_label)
        layout.addWidget(sev_label)

        return card
