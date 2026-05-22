"""
Scan Detail View - Page for viewing complete scan details within app UI
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame
)
from PyQt5.QtGui import QPixmap, QImage, QFont
import cv2
import numpy as np
from styles import BRAND
from widgets.touchscroll import TouchScrollArea


class ScanDetailView(QWidget):
    """Page showing complete scan details within app UI (not modal)."""
    
    def __init__(self, on_back):
        super().__init__()
        self.on_back = on_back
        self.current_patient_id = None
        self.current_db = None
        
        # Build basic layout
        self._build_ui()
    
    def _build_ui(self):
        """Build the page layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # ===== HEADER =====
        header_layout = QHBoxLayout()
        
        btn_back = QPushButton("← Back")
        btn_back.setFixedSize(80, 36)
        btn_back.clicked.connect(self.on_back)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {BRAND};
                border: 2px solid {BRAND};
                border-radius: 6px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(37, 99, 235, 0.1);
            }}
        """)
        
        self.title_label = QLabel("Scan Details")
        title_font = QFont("Segoe UI", 16)
        title_font.setWeight(QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1f2937;")
        
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #6b7280; font-size: 11px;")
        
        header_layout.addWidget(btn_back)
        header_layout.addSpacing(12)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.info_label)
        
        layout.addLayout(header_layout)
        
        # ===== SCROLL AREA FOR CONTENT =====
        scroll = TouchScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("TouchScrollArea { border: none; background-color: #fafafa; }")
        
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setSpacing(12)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self.content_container)
        layout.addWidget(scroll, 1)
    
    def show_scan(self, patient_id, db):
        """Load and display a patient's scan."""
        self.current_patient_id = patient_id
        self.current_db = db
        
        # Clear previous content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get patient and scans
        patient = db.get_patient(patient_id)
        scans = db.get_scans_by_patient(patient_id)
        
        if not patient or not scans:
            msg = QLabel("No scans found for this patient.")
            msg.setAlignment(Qt.AlignCenter)
            self.content_layout.addWidget(msg)
            self.title_label.setText("Scan Details")
            self.info_label.setText("")
            return
        
        # Use most recent scan
        scan = scans[0]
        
        # Update header
        self.title_label.setText(f"Scan Details: {patient['name']}")
        self.info_label.setText(f"Status: {patient['status']} | {scan['date']} {scan['time']}")
        
        # Get images and nail data
        images_dict = scan.get("images", {})
        nails_list = scan.get("nails", [])
        
        # ===== LEFT FOOT SECTION =====
        # Use detection visualization if available, otherwise use full image
        left_foot_img = images_dict.get("left_foot_detection") or images_dict.get("left_foot_full")
        left_nails = [n for n in nails_list if n.get("side") == "left"]
        
        if left_foot_img or left_nails:
            self.content_layout.addWidget(
                self._create_foot_section("Left Foot", left_foot_img, left_nails, images_dict, db)
            )
        
        # ===== RIGHT FOOT SECTION =====
        # Use detection visualization if available, otherwise use full image
        right_foot_img = images_dict.get("right_foot_detection") or images_dict.get("right_foot_full")
        right_nails = [n for n in nails_list if n.get("side") == "right"]
        
        if right_foot_img or right_nails:
            self.content_layout.addWidget(
                self._create_foot_section("Right Foot", right_foot_img, right_nails, images_dict, db)
            )
        
        self.content_layout.addStretch()
    
    def _create_foot_section(self, foot_name, full_image_path, nails, images_dict, db):
        """Create a section for one foot."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background-color: white;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setSpacing(10)
        
        # Foot title
        title = QLabel(foot_name)
        title_font = QFont("Segoe UI", 12)
        title_font.setWeight(QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1f2937;")
        layout.addWidget(title)
        
        # Full foot image with detection (will be detection visualization if available)
        if full_image_path:
            img = db.get_image(full_image_path)
            if img is not None:
                img_label = QLabel()
                img_label.setAlignment(Qt.AlignCenter)
                pixmap = self._cv_to_qpixmap(img, max_height=200)
                img_label.setPixmap(pixmap)
                
                frame = QFrame()
                frame.setStyleSheet("border: 1px solid #e5e7eb; border-radius: 4px; background-color: #f9fafb;")
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(0, 0, 0, 0)
                frame_layout.addWidget(img_label)
                
                layout.addWidget(frame)
        
        # Nails for this foot
        if nails:
            for nail in nails:
                nail_card = self._create_nail_card(nail, images_dict, db)
                layout.addWidget(nail_card)
        
        return section
    
    def _create_nail_card(self, nail, images_dict, db):
        """Create a card for a single nail."""
        card = QFrame()
        card.setMinimumHeight(450)
        card.setMaximumWidth(700)
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Nail info
        side = nail.get("side", "unknown")
        nail_num = nail.get("nail_number", "?")
        severity = nail.get("severity", "Unknown")
        osi_score = nail.get("osi_score", 0)
        affected_area = nail.get("affected_area_percent", 0)
        
        # Severity color
        severity_colors = {
            "Clinically Cured / No involvement": ("#22c55e", "#dcfce7"),
            "Mild": ("#3b82f6", "#dbeafe"),
            "Moderate": ("#f59e0b", "#fef3c7"),
            "Severe": ("#ef4444", "#fee2e2"),
        }
        color, bg = severity_colors.get(severity, ("#999", "#f0f0f0"))
        severity_short = "Healthy" if severity == "Clinically Cured / No involvement" else severity
        is_healthy = (severity == "Clinically Cured / No involvement")
        
        # Header
        header = QLabel(f"Nail #{nail_num} | {severity_short}")
        header.setStyleSheet(f"font-weight: 700; font-size: 11px; background-color: {bg}; padding: 4px; border-radius: 3px;")
        layout.addWidget(header)
        
        # Metrics
        metrics_text = f"OSI: {osi_score}/25 | Affected Area: {affected_area:.1f}%"
        metrics = QLabel(metrics_text)
        metrics.setStyleSheet(f"font-size: 10px; color: {color}; font-weight: 700;")
        layout.addWidget(metrics)
        
        key_prefix = f"{side}_nail_{nail_num}"
        nail_img_dict = images_dict.get(key_prefix, {})
        
        if isinstance(nail_img_dict, dict):
            if is_healthy:
                # HEALTHY: Show only original image (centered, large - 300x300)
                images_row = QHBoxLayout()
                images_row.setSpacing(0)
                images_row.setContentsMargins(0, 0, 0, 0)
                
                original_path = nail_img_dict.get("original")
                if original_path:
                    img = db.get_image(original_path)
                    if img is not None:
                        original_container = QFrame()
                        original_container.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;")
                        original_container_layout = QVBoxLayout(original_container)
                        original_container_layout.setContentsMargins(8, 8, 8, 8)
                        original_container_layout.setAlignment(Qt.AlignCenter)
                        
                        img_label = QLabel()
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setMinimumHeight(300)
                        img_label.setMinimumWidth(300)
                        
                        pixmap = self._cv_to_qpixmap(img, max_width=300)
                        img_label.setPixmap(pixmap)
                        
                        original_container_layout.addWidget(img_label)
                        images_row.addStretch()
                        images_row.addWidget(original_container)
                        images_row.addStretch()
                
                layout.addLayout(images_row)
            else:
                # AFFECTED: Show original + grid side by side (250x250 each)
                images_row = QHBoxLayout()
                images_row.setSpacing(16)
                images_row.setContentsMargins(0, 0, 0, 0)
                images_row.setAlignment(Qt.AlignCenter)
                
                # Left: Original image
                original_path = nail_img_dict.get("original")
                if original_path:
                    img = db.get_image(original_path)
                    if img is not None:
                        original_container = QFrame()
                        original_container.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;")
                        original_container_layout = QVBoxLayout(original_container)
                        original_container_layout.setContentsMargins(8, 8, 8, 8)
                        original_container_layout.setAlignment(Qt.AlignCenter)
                        
                        img_label = QLabel()
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setMinimumHeight(250)
                        img_label.setMinimumWidth(250)
                        
                        pixmap = self._cv_to_qpixmap(img, max_width=250)
                        img_label.setPixmap(pixmap)
                        
                        original_container_layout.addWidget(img_label)
                        images_row.addWidget(original_container)
                
                # Right: Grid visualization
                grid_path = nail_img_dict.get("grid")
                if grid_path:
                    img = db.get_image(grid_path)
                    if img is not None:
                        grid_container = QFrame()
                        grid_container.setStyleSheet("background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 4px;")
                        grid_container_layout = QVBoxLayout(grid_container)
                        grid_container_layout.setContentsMargins(8, 8, 8, 8)
                        grid_container_layout.setAlignment(Qt.AlignCenter)
                        
                        img_label = QLabel()
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setMinimumHeight(250)
                        img_label.setMinimumWidth(250)
                        
                        pixmap = self._cv_to_qpixmap(img, max_width=250)
                        img_label.setPixmap(pixmap)
                        
                        grid_container_layout.addWidget(img_label)
                        images_row.addWidget(grid_container)
                
                layout.addLayout(images_row)
        
        return card
    
    
    def _cv_to_qpixmap(self, img_bgr, max_width=None, max_height=None):
        """Convert OpenCV BGR image to QPixmap with scaling."""
        if img_bgr is None:
            return QPixmap()
        
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        
        # Scale to fit constraints
        if max_width and w > max_width:
            scale = max_width / w
            h = int(h * scale)
            w = max_width
            rgb = cv2.resize(rgb, (w, h))
        
        if max_height and h > max_height:
            scale = max_height / h
            w = int(w * scale)
            h = max_height
            rgb = cv2.resize(rgb, (w, h))
        
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        return QPixmap.fromImage(qimg)

