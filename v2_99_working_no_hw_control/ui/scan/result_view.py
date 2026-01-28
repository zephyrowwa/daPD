# ui/scan/result_view.py
from time import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QFrame, QSizePolicy, QGroupBox, QInputDialog, QMessageBox, QDialog, QComboBox, QLineEdit
)
from PyQt5.QtGui import QPixmap, QImage, QFont
import os, cv2
from styles import BRAND, ACCENT, BORD, MUTED
from database.db_manager_v2 import DatabaseManagerV2



class LoadingOverlay(QFrame):
    """Minimal medical-aesthetic loading overlay."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.NoFrame)
        
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
    """Displays results for both left and right feet."""

    def __init__(self, on_newscan):
        super().__init__()
        self.on_newscan = on_newscan
        self.db = DatabaseManagerV2()
        self.current_feet_data = None  # Store for saving

        # ===== ROOT LAYOUT =====
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(10)

        # ===== LOADING OVERLAY =====
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.hide()

        # ===== SCROLL AREA FOR RESULTS =====
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
        self.btn_save.clicked.connect(self.show_save_dialog)

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

    def show_results(self, feet_data):
        """Display results for both left and right feet."""
        print(f"[ResultView] Displaying results for both feet...")
        
        # Store feet_data for saving later
        self.current_feet_data = feet_data
        
        self.clear_results()
        
        # Process and display Right foot
        if "right" in feet_data:
            right_data = feet_data["right"]
            self._create_foot_section("Right Foot", right_data)
        
        # Process and display Left foot
        if "left" in feet_data:
            left_data = feet_data["left"]
            self._create_foot_section("Left Foot", left_data)
        
        self.results_layout.addStretch()
    
    def _create_foot_section(self, foot_name, foot_data):
        """Create a section for one foot's results."""
        # Section frame
        section_frame = QFrame()
        section_frame.setStyleSheet("""
            QFrame {
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        section_layout = QVBoxLayout(section_frame)
        section_layout.setSpacing(12)
        
        # Foot name header
        header = QLabel(foot_name)
        header.setFont(QFont("Segoe UI", 13, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #1f2937; padding: 8px;")
        section_layout.addWidget(header)
        
        # Full detection visualization
        if "image" in foot_data:
            viz_label = self._create_detection_visualization(foot_data)
            section_layout.addWidget(viz_label)
        
        # Cropped toenails
        if "cropped_nails" in foot_data:
            nails = foot_data["cropped_nails"]
            if nails:
                nails_label = QLabel("Detected Toenails")
                nails_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
                nails_label.setStyleSheet("color: #374151; padding: 8px 0px;")
                section_layout.addWidget(nails_label)
                
                # Grid layout for toenails
                grid_layout = QVBoxLayout()
                grid_layout.setSpacing(12)
                
                for i in range(0, len(nails), 2):
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(12)
                    
                    # First toenail
                    nail1 = nails[i]
                    card1 = self.create_toenail_card(
                        nail1["image"],
                        nail1.get("segmentation_visualization"),
                        nail1["confidence"],
                        i + 1,
                        nail1.get("segmentation_classes"),
                        nail1.get("osi_result")
                    )
                    row_layout.addWidget(card1)
                    
                    # Second toenail (if exists)
                    if i + 1 < len(nails):
                        nail2 = nails[i + 1]
                        card2 = self.create_toenail_card(
                            nail2["image"],
                            nail2.get("segmentation_visualization"),
                            nail2["confidence"],
                            i + 2,
                            nail2.get("segmentation_classes"),
                            nail2.get("osi_result")
                        )
                        row_layout.addWidget(card2)
                    else:
                        row_layout.addStretch()
                    
                    grid_layout.addLayout(row_layout)
                
                section_layout.addLayout(grid_layout)
        
        self.results_layout.addWidget(section_frame)
    
    def _create_detection_visualization(self, foot_data):
        """Create visualization of full image with detections."""
        # Use pre-made detection visualization from scan processing
        img = foot_data.get("detection_visualization")
        if img is None:
            img = foot_data.get("image")
        
        if img is None:
            empty_label = QLabel("No image available")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999;")
            return empty_label
        
        # Convert to QPixmap
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Scale to fit (max width 500px)
        scaled_pixmap = pixmap.scaledToWidth(500, Qt.SmoothTransformation)
        
        label = QLabel()
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        
        return label
    
    def create_toenail_card(self, nail_img, seg_visualization, confidence, nail_number, segmentation_classes=None, osi_result=None):
        """Display original and grid-analyzed nail side by side with OSI grading."""
        from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout
        from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
        import cv2

        card = QFrame()
        card.setMinimumHeight(300)
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Top row: Original image and Grid visualization side by side (CENTERED)
        images_row = QHBoxLayout()
        images_row.setSpacing(12)
        images_row.setContentsMargins(0, 0, 0, 0)
        
        # Left: Original toenail image
        original_container = QFrame()
        original_container.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;")
        original_container_layout = QVBoxLayout(original_container)
        original_container_layout.setContentsMargins(4, 4, 4, 4)
        
        original_label = QLabel()
        original_label.setAlignment(Qt.AlignCenter)
        original_label.setMinimumHeight(160)
        original_label.setMinimumWidth(160)
        
        if nail_img is not None:
            rgb = cv2.cvtColor(nail_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            scaled_pix = pix.scaledToWidth(160, Qt.SmoothTransformation)
            original_label.setPixmap(scaled_pix)
        
        original_container_layout.addWidget(original_label)
        
        # Right: Grid visualization
        grid_container = QFrame()
        grid_container.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;")
        grid_container_layout = QVBoxLayout(grid_container)
        grid_container_layout.setContentsMargins(4, 4, 4, 4)
        
        grid_label = QLabel()
        grid_label.setAlignment(Qt.AlignCenter)
        grid_label.setMinimumHeight(160)
        grid_label.setMinimumWidth(160)
        
        # Use OSI grid visualization if available
        if osi_result and "grid_visualization" in osi_result:
            display_img = osi_result["grid_visualization"]
        else:
            display_img = seg_visualization if seg_visualization is not None else nail_img
        
        if display_img is not None:
            rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            scaled_pix = pix.scaledToWidth(160, Qt.SmoothTransformation)
            grid_label.setPixmap(scaled_pix)
        
        grid_container_layout.addWidget(grid_label)
        
        images_row.addStretch()
        images_row.addWidget(original_container)
        images_row.addWidget(grid_container)
        images_row.addStretch()
        layout.addLayout(images_row)

        # OSI Score and Severity Display
        # Always try to extract and display OSI score, even from incomplete data
        osi_data = None
        if osi_result is not None and isinstance(osi_result, dict):
            osi_data = osi_result.get("osi_score", {})
        
        # Verify osi_data is a valid dict without errors
        if isinstance(osi_data, dict) and osi_data and "error" not in osi_data:
            osi_score = osi_data.get("total_osi_score", 0)
            severity = osi_data.get("severity", "Unknown")
            area_pct = osi_data.get("area_percent", 0)
            
            # Determine color based on severity
            if severity == "Clinically Cured / No involvement":
                severity_color = "#22c55e"  # Green
                severity_bg = "#dcfce7"
                severity_short = "Healthy"
            elif severity == "Mild":
                severity_color = "#3b82f6"  # Blue
                severity_bg = "#dbeafe"
                severity_short = "Mild"
            elif severity == "Moderate":
                severity_color = "#f59e0b"  # Amber
                severity_bg = "#fef3c7"
                severity_short = "Moderate"
            else:  # Severe or Unknown
                severity_color = "#ef4444"  # Red
                severity_bg = "#fee2e2"
                severity_short = "Severe" if severity == "Severe" else severity
            
            # Changed format: "Nail #X | [Grading]"
            header_label = QLabel(f"Nail #{nail_number} | {severity_short}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet(f"""
                font-weight: 700; 
                font-size: 11px; 
                color: #333;
                padding: 4px;
            """)
            layout.addWidget(header_label)
            
            osi_label = QLabel(f"OSI: {osi_score}/25")
            osi_label.setAlignment(Qt.AlignCenter)
            osi_label.setStyleSheet(f"""
                font-weight: 700; 
                font-size: 12px; 
                color: {severity_color};
                padding: 4px;
                background: {severity_bg};
                border-radius: 4px;
            """)
            layout.addWidget(osi_label)
            
            area_label = QLabel(f"Affected Area: {area_pct:.1f}%")
            area_label.setAlignment(Qt.AlignCenter)
            area_label.setStyleSheet("font-size: 9px; color: #666; padding: 2px;")
            layout.addWidget(area_label)
        else:
            # osi_data is invalid, None, or has error - show generic nail info
            header_label = QLabel(f"Nail #{nail_number}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("font-weight: 700; font-size: 12px; color: #333; padding: 4px;")
            layout.addWidget(header_label)
            
            grading_label = QLabel("Unable to calculate grading")
            grading_label.setAlignment(Qt.AlignCenter)
            grading_label.setStyleSheet("font-size: 10px; color: #999; padding: 4px;")
            layout.addWidget(grading_label)

        return card

    def show_save_dialog(self):
        """Show dialog for saving scan result with patient info."""
        if not self.current_feet_data:
            QMessageBox.warning(self, "No Data", "No scan data to save.")
            return
        
        dialog = SaveScanDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            patient_name = dialog.patient_name.strip()
            status = dialog.status_combo.currentText()
            
            if not patient_name:
                QMessageBox.warning(self, "Input Error", "Please enter a patient name.")
                return
            
            try:
                self.save_scan_to_db(patient_name, status)
                QMessageBox.information(self, "Saved", f"Scan for {patient_name} saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save scan: {str(e)}")

    def save_scan_to_db(self, patient_name: str, status: str):
        """Save complete scan with all images and data."""
        if not self.current_feet_data:
            raise ValueError("No scan data available")
        
        # Get or create patient
        patient = self.db.get_patient_by_name(patient_name)
        if not patient:
            patient_id = self.db.add_patient(patient_name, status)
        else:
            patient_id = patient["id"]
            # Update status if needed
            if patient["status"] != status:
                self.db.update_patient(patient_id, status=status)
        
        # Determine overall severity (most dominant)
        all_severities = []
        for side in ["left", "right"]:
            cropped_nails = self.current_feet_data.get(side, {}).get("cropped_nails", [])
            for nail in cropped_nails:
                osi_result = nail.get("osi_result", {})
                severity = osi_result.get("osi_score", {}).get("severity", "Unknown")
                all_severities.append(severity)
        
        # Map severity to priority and get most severe
        severity_priority = {
            "Clinically Cured / No involvement": 0,
            "Mild": 1,
            "Moderate": 2,
            "Severe": 3,
            "Unknown": -1
        }
        overall_severity = max(all_severities, key=lambda x: severity_priority.get(x, -1)) if all_severities else "Unknown"
        
        # Save to database
        scan_id = self.db.add_scan(patient_id, self.current_feet_data, overall_severity)
        print(f"[ResultView] Saved scan {scan_id} for patient {patient_name}")


class SaveScanDialog(QDialog):
    """Dialog to get patient name and status for saving scan."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Save Scan")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Patient name input
        name_label = QLabel("Patient Name:")
        name_label.setStyleSheet("font-weight: 700;")
        
        self.name_input_widget = QLineEdit()
        self.name_input_widget.setPlaceholderText("Enter patient name")
        self.name_input_widget.setFixedHeight(36)
        layout.addWidget(name_label)
        layout.addWidget(self.name_input_widget)
        
        # Status dropdown
        status_label = QLabel("Patient Status:")
        status_label.setStyleSheet("font-weight: 700;")
        self.status_combo = QComboBox()
        self.status_combo.addItems(["under monitoring", "follow up", "done"])
        self.status_combo.setFixedHeight(36)
        layout.addWidget(status_label)
        layout.addWidget(self.status_combo)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        btn_save = QPushButton("Save")
        btn_save.setFixedSize(100, 40)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {BRAND};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #1d4ed8;
            }}
        """)
        btn_save.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setFixedSize(100, 40)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: #e5e7eb;
                color: #374151;
                border: none;
                border-radius: 4px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #d1d5db;
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
    
    def accept(self):
        """Override accept to get patient name."""
        self.patient_name = self.name_input_widget.text()
        super().accept()
