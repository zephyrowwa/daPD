# ui/scan/result_view.py
from time import time
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFrame, QSizePolicy, QGroupBox, QInputDialog, QMessageBox, QDialog, QComboBox, QLineEdit
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
import os, cv2
from styles import BRAND, ACCENT, BORD, MUTED
from widgets.touchscroll import TouchScrollArea
from database.db_manager_v2 import DatabaseManagerV2


# Recommendations based on severity
RECOMMENDATIONS = {
    "Clinically Cured / No involvement": {
        "title": "Recommendation:",
        "sections": [
            {
                "type": "list",
                "items": [
                    "No treatment needed",
                    "Do preemptive care"
                ]
            },
            {
                "type": "numbered",
                "heading": None,
                "items": [
                    "Keep nails dry",
                    "Trim straight",
                    "Antifungal powder/spray if high risk"
                ]
            }
        ]
    },
    "Mild": {
        "title": "Recommendation:",
        "sections": [
            {
                "type": "list",
                "items": [
                    "Encouraged to consult with a dermatologist/podiatrist",
                    "Mechanical debridement can improve results",
                    "Use topical antifungals on the toenails (for maximum of 48 weeks)"
                ]
            },
            {
                "type": "subsection",
                "heading": "Recommended (needs prescriptions from a doctor):",
                "items": [
                    "Efinaconazole 10% solution",
                    "Tavaborole 5% solution",
                    "Ciclopirox lacquer"
                ]
            }
        ]
    },
    "Moderate": {
        "title": "Recommendation:",
        "sections": [
            {
                "type": "list",
                "items": [
                    "Highly encouraged to consult with a dermatologist/podiatrist",
                    "Oral terbinafine (first-line) for 250 mg daily × 12 weeks",
                    "Topical antifungal (adjunct)",
                    "Nail debridement is recommended",
                    "Baseline liver function tests"
                ]
            }
        ]
    },
    "Severe": {
        "title": "Recommendation:",
        "sections": [
            {
                "type": "list",
                "items": [
                    "Immediate need for a consultation with a dermatologist/podiatrist",
                    "Oral terbinafine (or itraconazole if contraindicated)",
                    "Combination therapy (oral + topical)",
                    "Aggressive debridement",
                    "Consider nail avulsion if painful or refractory"
                ]
            }
        ]
    }
}


class CollapsibleRecommendations(QFrame):
    """Collapsible recommendations widget for toenail severity."""
    
    def __init__(self, severity, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.severity = severity
        
        self.setStyleSheet("""
            CollapsibleRecommendations {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header (clickable)
        self.header = QPushButton()
        self.header.setFlat(True)
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.clicked.connect(self.toggle)
        self.header.setMinimumHeight(32)
        self.header.setMaximumHeight(32)
        self.header.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: none;
                border-radius: 6px;
                text-align: left;
                padding: 6px 10px;
                font-weight: 600;
                font-size: 10px;
                color: #1f2937;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
            QPushButton:pressed {
                background: #d1d5db;
            }
        """)
        self.update_header()
        self.main_layout.addWidget(self.header)
        
        # Content (initially hidden)
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: none;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(10, 8, 10, 8)
        self.content_layout.setSpacing(6)
        
        self._build_content()
        self.content_frame.hide()
        self.main_layout.addWidget(self.content_frame)
    
    def _build_content(self):
        """Build the content based on severity."""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        rec = RECOMMENDATIONS.get(self.severity, {})
        sections = rec.get("sections", [])
        
        for section in sections:
            section_type = section.get("type", "list")
            
            if section_type == "list":
                for item_text in section.get("items", []):
                    item_label = QLabel(f"• {item_text}")
                    item_label.setWordWrap(True)
                    item_label.setStyleSheet("""
                        font-size: 9px;
                        color: #374151;
                        line-height: 1.3;
                        margin: 0px;
                    """)
                    self.content_layout.addWidget(item_label)
            
            elif section_type == "numbered":
                for idx, item_text in enumerate(section.get("items", []), 1):
                    item_label = QLabel(f"{idx}. {item_text}")
                    item_label.setWordWrap(True)
                    item_label.setStyleSheet("""
                        font-size: 9px;
                        color: #374151;
                        line-height: 1.3;
                        margin: 0px;
                    """)
                    self.content_layout.addWidget(item_label)
            
            elif section_type == "subsection":
                heading = section.get("heading", "")
                if heading:
                    heading_label = QLabel(heading)
                    heading_label.setStyleSheet("""
                        font-size: 9px;
                        font-weight: 600;
                        color: #1f2937;
                        padding-top: 4px;
                        padding-bottom: 2px;
                        margin: 0px;
                    """)
                    self.content_layout.addWidget(heading_label)
                
                for idx, item_text in enumerate(section.get("items", []), 1):
                    item_label = QLabel(f"{idx}. {item_text}")
                    item_label.setWordWrap(True)
                    item_label.setStyleSheet("""
                        font-size: 9px;
                        color: #374151;
                        margin-left: 6px;
                        line-height: 1.3;
                        margin-top: 0px;
                        margin-bottom: 0px;
                    """)
                    self.content_layout.addWidget(item_label)
    
    def update_header(self):
        """Update header text with expand/collapse indicator."""
        arrow = "▼" if self.is_expanded else "▶"
        rec = RECOMMENDATIONS.get(self.severity, {})
        title = rec.get("title", "Recommendation:")
        self.header.setText(f"{arrow}  {title}")
    
    def toggle(self):
        """Toggle expanded/collapsed state."""
        from PyQt5.QtWidgets import QApplication
        
        self.is_expanded = not self.is_expanded
        self.update_header()
        
        if self.is_expanded:
            self.content_frame.show()
            # Force layout to recalculate
            self.content_frame.adjustSize()
            self.adjustSize()
            # Get the parent widget (scroll area) and scroll to this recommendations widget
            parent = self.parent()
            while parent:
                parent_type = type(parent).__name__
                if "ScrollArea" in parent_type or "Scroll" in parent_type:
                    # Found a scroll area, scroll to show this widget
                    from PyQt5.QtWidgets import QAbstractScrollArea
                    scroll_area = parent
                    # Ensure this widget is visible in the scroll area
                    scroll_area.ensureWidgetVisible(self)
                    break
                parent = parent.parent()
        else:
            self.content_frame.hide()
        
        # Force parent layout update
        layout = self.parent()
        if layout and hasattr(layout, 'update'):
            layout.update()



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

    def __init__(self, on_newscan, on_apply_med=None):
        super().__init__()
        self.on_newscan = on_newscan
        self.on_apply_med = on_apply_med
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
        self.results_scroll = TouchScrollArea()
        self.results_scroll.setWidgetResizable(True)
        # Hide scroll bar for Android-like experience
        self.results_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setSpacing(16)

        self.results_scroll.setWidget(self.results_container)
        root.addWidget(self.results_scroll, 1)

        # ===== ACTION BUTTONS =====
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(10)

        self.btn_newscan = QPushButton("New Scan")
        self.btn_newscan.setFixedSize(130, 36)
        self.btn_newscan.clicked.connect(self.on_newscan)
        self._set_button_icon(self.btn_newscan, "new.svg")
        self._style_button(self.btn_newscan, BRAND)

        self.btn_save = QPushButton("Save Result")
        self.btn_save.setFixedSize(130, 36)
        self.btn_save.clicked.connect(self.show_save_dialog)
        self._set_button_icon(self.btn_save, "save.svg")
        self._style_button(self.btn_save, BRAND)

        self.btn_apply_med = QPushButton("Apply Med")
        self.btn_apply_med.setFixedSize(130, 36)
        self.btn_apply_med.clicked.connect(self._on_apply_med_clicked)
        self._set_button_icon(self.btn_apply_med, "med.svg")
        self._style_button(self.btn_apply_med, BRAND)

        btn_row.addWidget(self.btn_newscan)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_apply_med)

        root.addLayout(btn_row)


    # =======================================================
    #             UI UPDATE ENTRY POINT
    # =======================================================

    def _set_button_icon(self, button, icon_filename):
        """Load and set icon for a button."""
        icon_path = os.path.join(os.path.dirname(__file__), icon_filename)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            button.setIcon(icon)
            button.setIconSize(QSize(20, 20))

    def _style_button(self, button, color):
        """Apply consistent styling to buttons - border only, minimal padding."""
        button.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: 1.5px solid {color};
                border-radius: 6px;
                font-weight: 600;
                padding: 4px 8px;
            }}
            QPushButton:hover {{ background: rgba({color}, 0.08); }}
            QPushButton:pressed {{ background: rgba({color}, 0.12); }}
            QPushButton:disabled {{
                color: #d1d5db;
                border: 1.5px solid #d1d5db;
                background: transparent;
            }}
        """)

    def _on_apply_med_clicked(self):
        """Handle Apply Med button click."""
        if self.on_apply_med:
            self.on_apply_med()
        else:
            print("[ResultView] on_apply_med callback not set")

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
        
        # Count toenails detected on each foot
        left_nail_count = 0
        right_nail_count = 0
        
        # Process and display Right foot
        if "right" in feet_data:
            right_data = feet_data["right"]
            self._create_foot_section("Right Foot", right_data)
            # Count nails on right foot
            if "cropped_nails" in right_data:
                right_nail_count = len(right_data["cropped_nails"])
        
        # Process and display Left foot
        if "left" in feet_data:
            left_data = feet_data["left"]
            self._create_foot_section("Left Foot", left_data)
            # Count nails on left foot
            if "cropped_nails" in left_data:
                left_nail_count = len(left_data["cropped_nails"])
        
        self.results_layout.addStretch()
        
        # Enable Apply Med button only if 3+ nails detected on BOTH feet
        can_apply_med = (left_nail_count >= 3) and (right_nail_count >= 3)
        self.btn_apply_med.setEnabled(can_apply_med)
        
        print(f"[ResultView] Left foot: {left_nail_count} nails, Right foot: {right_nail_count} nails")
        print(f"[ResultView] Apply Med enabled: {can_apply_med}")
    
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
                
                # Grid layout for toenails (1 per row now)
                grid_layout = QVBoxLayout()
                grid_layout.setSpacing(16)
                grid_layout.setAlignment(Qt.AlignTop)
                grid_layout.setContentsMargins(0, 0, 0, 0)
                
                for i, nail in enumerate(nails):
                    nail_card = self.create_toenail_card(
                        nail["image"],
                        nail.get("segmentation_visualization"),
                        nail["confidence"],
                        i + 1,
                        nail.get("segmentation_classes"),
                        nail.get("osi_result")
                    )
                    grid_layout.addWidget(nail_card)
                
                section_layout.addLayout(grid_layout)
            else:
                # No toenails detected
                no_nails_label = QLabel("No toenails detected")
                no_nails_label.setAlignment(Qt.AlignCenter)
                no_nails_label.setFont(QFont("Segoe UI", 10))
                no_nails_label.setStyleSheet("color: #9ca3af; padding: 16px 8px;")
                section_layout.addWidget(no_nails_label)
        
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
        """
        Display nail image with OSI grading - redesigned two-column layout.
        Left: Bigger Image | Right: Info (Nail #, OSI, Affected Area) + Recommendations
        """
        from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout
        from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
        import cv2

        card = QFrame()
        card.setMinimumHeight(320)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        card.setStyleSheet("""
            QFrame {
                background: #ffffff;
                border: none;
                border-radius: 0px;
                padding: 8px;
            }
        """)

        # Main horizontal layout: Left (big image) | Right (info + recommendations)
        main_layout = QHBoxLayout(card)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # ===== LEFT SIDE: BIGGER IMAGE =====
        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setAlignment(Qt.AlignTop)

        # Check if nail is healthy (no affected area)
        osi_data = None
        is_healthy = True
        if osi_result is not None and isinstance(osi_result, dict):
            osi_data = osi_result.get("osi_score", {})
            if isinstance(osi_data, dict) and "error" not in osi_data:
                severity = osi_data.get("severity", "")
                is_healthy = (severity == "Clinically Cured / No involvement")
        
        # Image display section - Show grid visualization for affected, original for healthy
        image_container = QFrame()
        image_container.setStyleSheet("background: transparent; border: none;")
        image_container_layout = QVBoxLayout(image_container)
        image_container_layout.setContentsMargins(0, 0, 0, 0)
        image_container_layout.setAlignment(Qt.AlignCenter)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setMinimumHeight(300)
        image_label.setMinimumWidth(300)
        image_label.setScaledContents(False)
        
        # Determine which image to display
        if is_healthy:
            # HEALTHY: Show original image
            display_img = nail_img
        else:
            # AFFECTED: Show grid visualization (not original)
            if osi_result and "grid_visualization" in osi_result:
                display_img = osi_result["grid_visualization"]
            else:
                display_img = seg_visualization if seg_visualization is not None else nail_img
        
        if display_img is not None:
            rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            scaled_pix = pix.scaledToWidth(300, Qt.SmoothTransformation)
            image_label.setPixmap(scaled_pix)
        
        image_container_layout.addWidget(image_label)
        left_layout.addWidget(image_container)
        left_layout.addStretch()
        main_layout.addLayout(left_layout, 0)
        
        # ===== RIGHT SIDE: INFO + RECOMMENDATIONS =====
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setAlignment(Qt.AlignTop)

        # OSI Score and Severity Display
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
            
            # Nail header: "Nail #X | [Severity]"
            header_label = QLabel(f"Nail #{nail_number} | {severity_short}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet(f"""
                font-weight: 700; 
                font-size: 11px; 
                color: #333;
                padding: 2px 0px;
            """)
            right_layout.addWidget(header_label)
            
            # OSI Score with colored background
            osi_label = QLabel(f"OSI: {osi_score}/25")
            osi_label.setAlignment(Qt.AlignCenter)
            osi_label.setStyleSheet(f"""
                font-weight: 700; 
                font-size: 12px; 
                color: {severity_color};
                padding: 4px 6px;
                background: {severity_bg};
                border-radius: 3px;
            """)
            right_layout.addWidget(osi_label)
            
            # Affected area percentage
            area_label = QLabel(f"Affected Area: {area_pct:.1f}%")
            area_label.setAlignment(Qt.AlignCenter)
            area_label.setStyleSheet("font-size: 10px; color: #666; padding: 2px 0px;")
            right_layout.addWidget(area_label)
        else:
            # osi_data is invalid, None, or has error - show generic nail info
            header_label = QLabel(f"Nail #{nail_number}")
            header_label.setAlignment(Qt.AlignCenter)
            header_label.setStyleSheet("font-weight: 700; font-size: 11px; color: #333; padding: 2px 0px;")
            right_layout.addWidget(header_label)
            
            grading_label = QLabel("Unable to calculate grading")
            grading_label.setAlignment(Qt.AlignCenter)
            grading_label.setStyleSheet("font-size: 10px; color: #999; padding: 2px 0px;")
            right_layout.addWidget(grading_label)
        
        # Add spacing before recommendations
        right_layout.addSpacing(8)
        
        # Add recommendations directly (if severity is available)
        if isinstance(osi_data, dict) and osi_data and "error" not in osi_data:
            severity = osi_data.get("severity", "")
            if severity in RECOMMENDATIONS:
                # Add recommendations header
                rec_header = QLabel("Recommendation:")
                rec_header.setAlignment(Qt.AlignLeft)
                rec_header.setStyleSheet("""
                    font-weight: 700;
                    font-size: 11px;
                    color: #1f2937;
                    padding: 0px;
                    margin-bottom: 4px;
                """)
                right_layout.addWidget(rec_header)
                
                # Build recommendations content directly
                rec = RECOMMENDATIONS.get(severity, {})
                sections = rec.get("sections", [])
                
                for section in sections:
                    section_type = section.get("type", "list")
                    
                    if section_type == "list":
                        for item_text in section.get("items", []):
                            item_label = QLabel(f"• {item_text}")
                            item_label.setWordWrap(True)
                            item_label.setStyleSheet("""
                                font-size: 11px;
                                color: #374151;
                                line-height: 1.3;
                                margin: 0px;
                                padding: 2px 0px;
                            """)
                            right_layout.addWidget(item_label)
                    
                    elif section_type == "numbered":
                        for idx, item_text in enumerate(section.get("items", []), 1):
                            item_label = QLabel(f"{idx}. {item_text}")
                            item_label.setWordWrap(True)
                            item_label.setStyleSheet("""
                                font-size: 11px;
                                color: #374151;
                                line-height: 1.3;
                                margin: 0px;
                                padding: 2px 0px;
                            """)
                            right_layout.addWidget(item_label)
                    
                    elif section_type == "subsection":
                        heading = section.get("heading", "")
                        if heading:
                            heading_label = QLabel(heading)
                            heading_label.setStyleSheet("""
                                font-size: 11px;
                                font-weight: 600;
                                color: #1f2937;
                                padding-top: 4px;
                                padding-bottom: 2px;
                                margin: 0px;
                            """)
                            right_layout.addWidget(heading_label)
                        
                        for idx, item_text in enumerate(section.get("items", []), 1):
                            item_label = QLabel(f"{idx}. {item_text}")
                            item_label.setWordWrap(True)
                            item_label.setStyleSheet("""
                                font-size: 11px;
                                color: #374151;
                                margin-left: 6px;
                                line-height: 1.3;
                                margin-top: 0px;
                                margin-bottom: 2px;
                            """)
                            right_layout.addWidget(item_label)
        
        right_layout.addStretch()
        main_layout.addLayout(right_layout, 1)

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
        scan_id = self.db.add_scan(patient_id, patient_name, self.current_feet_data, overall_severity)
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
