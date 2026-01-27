# ui/scan/result_view.py
from time import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QGroupBox, QInputDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont
import os, cv2
from styles import BRAND, ACCENT, BORD, MUTED



class LoadingOverlay(QFrame):
    """Minimal medical-aesthetic loading overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        
        # White background that covers everything
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: #ffffff;
                border: none;
            }
        """)
        
        # Center container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 24px;
            }
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)
        container_layout.setAlignment(Qt.AlignCenter)
        
        # Animated spinner (using unicode character)
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setFont(QFont("Arial", 32))
        self.spinner_label.setStyleSheet("color: #3b82f6;")
        
        # Status text
        self.status_label = QLabel("Processing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_font = QFont("Arial", 14)
        status_font.setWeight(QFont.Normal)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #1f2937; letter-spacing: 0.5px;")
        
        # Subtitle
        self.subtitle_label = QLabel()
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_font = QFont("Arial", 11)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: #6b7280;")
        
        container_layout.addWidget(self.spinner_label)
        container_layout.addWidget(self.status_label)
        container_layout.addWidget(self.subtitle_label)
        
        layout.addWidget(container, alignment=Qt.AlignCenter)
        
        # Animation timer
        self.spinner_frames = ["◐", "◓", "◑", "◒"]
        self.current_frame = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_spinner)
        
    def start(self, status_text="Processing...", subtitle=""):
        """Start loading animation."""
        from PyQt5.QtWidgets import QApplication
        self.status_label.setText(status_text)
        self.subtitle_label.setText(subtitle)
        self.current_frame = 0
        self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()
        self.timer.start(150)
        QApplication.processEvents()
    
    def stop(self):
        """Stop loading animation."""
        from PyQt5.QtWidgets import QApplication
        self.timer.stop()
        self.hide()
        QApplication.processEvents()
    
    def update_status(self, status_text, subtitle=""):
        """Update status text during loading."""
        from PyQt5.QtWidgets import QApplication
        self.status_label.setText(status_text)
        self.subtitle_label.setText(subtitle)
        QApplication.processEvents()
    
    def animate_spinner(self):
        """Animate spinner."""
        self.spinner_label.setText(self.spinner_frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.spinner_frames)


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

        # ===== LOADING OVERLAY =====
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.hide()

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

    def resizeEvent(self, event):
        """Update loading overlay size when window is resized."""
        super().resizeEvent(event)
        self.loading_overlay.setGeometry(self.rect())

    def show_results(self, cropped_nails):
        print(f"[ResultView] Displaying {len(cropped_nails)} detected toenails...")

        self.clear_results()

        # Create a grid layout for toenails (2 columns)
        grid_layout = QVBoxLayout()
        grid_layout.setSpacing(12)
        
        for i in range(0, len(cropped_nails), 2):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(12)
            
            # First toenail in row
            nail1 = cropped_nails[i]
            seg_classes_1 = nail1.get("segmentation_classes", [])
            seg_viz_1 = nail1.get("segmentation_visualization")
            card1 = self.create_toenail_card(nail1["image"], seg_viz_1, nail1["confidence"], i + 1, seg_classes_1)
            row_layout.addWidget(card1)
            
            # Second toenail in row (if exists)
            if i + 1 < len(cropped_nails):
                nail2 = cropped_nails[i + 1]
                seg_classes_2 = nail2.get("segmentation_classes", [])
                seg_viz_2 = nail2.get("segmentation_visualization")
                card2 = self.create_toenail_card(nail2["image"], seg_viz_2, nail2["confidence"], i + 2, seg_classes_2)
                row_layout.addWidget(card2)
            else:
                row_layout.addStretch()
            
            grid_layout.addLayout(row_layout)
        
        self.results_layout.addLayout(grid_layout)
        self.results_layout.addStretch()
    
    def create_toenail_card(self, nail_img, seg_visualization, confidence, nail_number, segmentation_classes=None):
        """Display a single detected toenail with segmentation visualization."""
        from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
        from PyQt5.QtGui import QImage, QPixmap
        import cv2

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Toenail segmentation visualization - square display
        img_label = QLabel()
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setMinimumHeight(160)
        img_label.setMinimumWidth(160)
        img_label.setMaximumHeight(160)
        img_label.setMaximumWidth(160)

        # Use segmentation visualization if available, otherwise use raw image
        display_img = seg_visualization if seg_visualization is not None else nail_img
        
        if display_img is not None:
            rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            # Scale to exact size to maintain square
            scaled_pix = pix.scaledToWidth(160, Qt.SmoothTransformation)
            img_label.setPixmap(scaled_pix)

        # Detection confidence info
        info_label = QLabel(f"#{nail_number} | {confidence:.2f}")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet(
            "font-weight: 600; font-size: 12px; padding: 4px;"
        )

        layout.addWidget(img_label)
        layout.addWidget(info_label)

        # Segmentation classes detected in this toenail
        if segmentation_classes:
            classes_text = ", ".join([f"{c['class']}" for c in segmentation_classes])
            classes_label = QLabel(f"Classes: {classes_text}")
            classes_label.setAlignment(Qt.AlignCenter)
            classes_label.setStyleSheet(
                "font-size: 11px; color: #666; padding: 4px; font-style: italic;"
            )
            classes_label.setWordWrap(True)
            layout.addWidget(classes_label)
        else:
            classes_label = QLabel("Classes: —")
            classes_label.setAlignment(Qt.AlignCenter)
            classes_label.setStyleSheet(
                "font-size: 11px; color: #999; padding: 4px;"
            )
            layout.addWidget(classes_label)

        return card

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



