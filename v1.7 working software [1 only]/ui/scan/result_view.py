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
        # connect
        

        # make scrollable (to fit on 7-inch screen)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        scroll.setWidget(container)
        main = QVBoxLayout(container)
        main.setAlignment(Qt.AlignTop)

        # ---------- RESULT CONTAINER ----------
        result_frame = QFrame()
        result_frame.setStyleSheet(f"QFrame{{border:1.5px solid {BORD}; border-radius:12px;}}")
        result_layout = QHBoxLayout(result_frame)
        result_layout.setContentsMargins(10, 10, 10, 10)

        # left side — segmented image
        self.lbl_segmented = QLabel("Segmented + Grid")
        self.lbl_segmented.setAlignment(Qt.AlignCenter)
        self.lbl_segmented.setMinimumSize(280, 280)
        self.lbl_segmented.setStyleSheet(f"border:1px solid {BORD}; border-radius:8px; color:{MUTED};")
        result_layout.addWidget(self.lbl_segmented, 2)

        # right side — info panel
        info_panel = QVBoxLayout()
        self.lbl_severity = QLabel("Severity: —")
        self.lbl_severity.setAlignment(Qt.AlignCenter)
        self.lbl_severity.setStyleSheet(
            "font: 700 14px 'Segoe UI'; color: #111827; padding:4px;"
        )

        self.reco_box = QGroupBox("Recommended Action")
        reco_v = QVBoxLayout(self.reco_box)
        self.lbl_recommend = QLabel("—")
        self.lbl_recommend.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.lbl_recommend.setWordWrap(True)
        self.lbl_recommend.setStyleSheet(f"color:{MUTED}; padding:4px;")
        reco_v.addWidget(self.lbl_recommend)
        info_panel.addWidget(self.lbl_severity)
        info_panel.addWidget(self.reco_box)
        info_panel.addStretch(1)

        result_layout.addLayout(info_panel, 3)

        # ---------- ACTION BUTTONS ----------
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)

        self.btn_newscan = QPushButton("New Scan")
        self.btn_newscan.setFixedSize(130, 44)
        self.btn_newscan.setStyleSheet(
            f"QPushButton{{background:transparent;color:{BRAND};border:2px solid {BRAND};"
            "border-radius:10px;padding:6px 10px;font-family:'DejaVu Sans','Segoe UI';"
            "font-size:13px;font-weight:700;}}"
            "QPushButton:hover{{background:rgba(37,99,235,0.06);}}"
        )
        self.btn_newscan.clicked.connect(on_newscan)

        self.btn_save = QPushButton("Save Result")
        

        self.btn_save.setFixedSize(130, 44)
        self.btn_save.setStyleSheet(
            f"QPushButton{{background:{ACCENT};color:white;border:none;"
            "border-radius:10px;padding:8px 14px;font-family:'DejaVu Sans','Segoe UI';"
            "font-size:13px;font-weight:700;}}"
            "QPushButton:hover{{background:#15803d;}}"
        )
        # self.btn_save.clicked.connect(self.save_result)
        self.btn_save.clicked.connect(self.save_to_db)

        btn_row.addWidget(self.btn_newscan)
        btn_row.addSpacing(12)
        btn_row.addWidget(self.btn_save)

        # ---------- assemble ----------
        main.addWidget(result_frame)
        main.addSpacing(12)
        main.addLayout(btn_row)
        main.addStretch(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(scroll)

    # =======================================================
    #             UI UPDATE ENTRY POINT
    # =======================================================
    # def show_result(self, segmented_bgr, severity_text="—", recommendation="—"):
    #     self.segmented_img = segmented_bgr
    #     self.lbl_segmented.setPixmap(bgr_to_qpixmap(segmented_bgr))
    #     self.lbl_severity.setText(f"Severity: {severity_text}")
    #     self.lbl_recommend.setText(recommendation)

    # def save_result(self):
    #     if self.segmented_img is None:
    #         QMessageBox.warning(self, "No Image", "No segmented image to save.")
    #         return
    #     name, ok = QInputDialog.getText(self, "Save Scan", "Enter patient name:")
    #     if not ok or not name.strip():
    #         return
    #     # extract plain severity text (remove label prefix)
    #     sev = self.lbl_severity.text().replace("Severity:", "").strip()
    #     reco = self.lbl_recommend.text().strip()
    #     try:
    #         self.db.add_scan(name.strip(), sev, reco, self.segmented_img)
    #         QMessageBox.information(self, "Saved", f"Scan for '{name.strip()}' saved.")
    #     except Exception as e:
    #         QMessageBox.critical(self, "DB Error", f"Failed to save: {e}")


    def show_result(self, segmented_bgr, severity_text, recommendation, captured_img):
        """Store the displayed result and prepare for saving."""
        self.segmented_img = segmented_bgr
        self.severity = severity_text
        self.recommend = recommendation

        # save temp files
        os.makedirs("data/scans", exist_ok=True)
        captured_path = os.path.join("data/scans", f"cap_{int(time())}.jpg")
        segmented_path = os.path.join("data/scans", f"seg_{int(time())}.jpg")
        cv2.imwrite(captured_path, captured_img)
        cv2.imwrite(segmented_path, segmented_bgr)

        self.captured_path = captured_path
        self.segmented_path = segmented_path

        self.lbl_segmented.setPixmap(bgr_to_qpixmap(segmented_bgr))
        self.lbl_severity.setText(f"Severity: {severity_text}")
        self.lbl_recommend.setText(recommendation)

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