# ui/scan/upload_view.py
"""
Image upload page: Select left and right foot images.
"""
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QFrame, QSizePolicy, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage, QFont
import cv2
import os
from styles import BRAND, ACCENT, MUTED


class UploadView(QWidget):
    """Upload left and right foot images."""
    
    def __init__(self, on_images_ready, on_back):
        super().__init__()
        self.on_images_ready = on_images_ready
        self.on_back = on_back
        
        self.left_image = None
        self.right_image = None
        self.left_path = None
        self.right_path = None
        
        # Main layout
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)
        
        # Title
        title = QLabel("Select Images")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2937; padding: 8px;")
        root.addWidget(title)
        
        # Content row: Left and Right columns
        content = QHBoxLayout()
        content.setSpacing(16)
        
        # Left foot section
        left_section = self._create_foot_section("Left Foot", self.on_select_left)
        self.left_label = left_section[0]
        self.btn_left = left_section[1]
        content.addLayout(left_section[2])
        
        # Right foot section
        right_section = self._create_foot_section("Right Foot", self.on_select_right)
        self.right_label = right_section[0]
        self.btn_right = right_section[1]
        content.addLayout(right_section[2])
        
        root.addLayout(content, 1)
        
        # Bottom buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.setAlignment(Qt.AlignCenter)
        
        self.btn_proceed = QPushButton("Analyze Images")
        self.btn_proceed.setFixedSize(140, 44)
        self.btn_proceed.setEnabled(False)
        self.btn_proceed.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:enabled:hover {{ background: {ACCENT}; }}
            QPushButton:disabled {{ background: #d1d5db; color: #999; }}
        """)
        self.btn_proceed.clicked.connect(self.on_proceed)
        
        self.btn_back_btn = QPushButton("Back to Camera")
        self.btn_back_btn.setFixedSize(130, 44)
        self.btn_back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {MUTED};
                color: #333;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #f3f4f6; }}
        """)
        self.btn_back_btn.clicked.connect(self.on_back)
        
        button_row.addWidget(self.btn_back_btn)
        button_row.addSpacing(12)
        button_row.addWidget(self.btn_proceed)
        
        root.addLayout(button_row)
    
    def _create_foot_section(self, title, on_select):
        """Create a section for selecting foot image."""
        section = QVBoxLayout()
        section.setSpacing(12)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        section.addWidget(title_label)
        
        # Image preview
        image_label = QLabel("No image selected")
        image_label.setAlignment(Qt.AlignCenter)
        image_label.setStyleSheet("""
            QLabel {
                background: #f3f4f6;
                border: 2px dashed #d1d5db;
                border-radius: 8px;
                padding: 20px;
                color: #6b7280;
                font-size: 12px;
            }
        """)
        image_label.setMinimumHeight(200)
        section.addWidget(image_label)
        
        # Select button
        btn_select = QPushButton(f"Select {title}")
        btn_select.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 8px;
            }}
            QPushButton:hover {{ background: {ACCENT}; }}
        """)
        btn_select.clicked.connect(on_select)
        section.addWidget(btn_select)
        
        return (image_label, btn_select, section)
    
    def on_select_left(self):
        """Select left foot image."""
        path = QFileDialog.getOpenFileName(
            self,
            "Select Left Foot Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )[0]
        
        if path:
            self._load_image(path, "left")
    
    def on_select_right(self):
        """Select right foot image."""
        path = QFileDialog.getOpenFileName(
            self,
            "Select Right Foot Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )[0]
        
        if path:
            self._load_image(path, "right")
    
    def _load_image(self, path, foot):
        """Load image and display preview."""
        try:
            # Read image using cv2
            img = cv2.imread(path)
            if img is None:
                QMessageBox.warning(self, "Error", "Could not load image")
                return
            
            # Store image and path
            if foot == "left":
                self.left_image = img
                self.left_path = path
                label = self.left_label
            else:
                self.right_image = img
                self.right_path = path
                label = self.right_label
            
            # Convert to RGB and display
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Scale to fit label
            scaled_pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
            
            # Update button state
            self.btn_proceed.setEnabled(self.left_image is not None and self.right_image is not None)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {str(e)}")
    
    def on_proceed(self):
        """Process the selected images."""
        if self.left_image is None or self.right_image is None:
            QMessageBox.warning(self, "Error", "Please select both left and right foot images")
            return
        
        # Call the callback with both images
        self.on_images_ready(
            left_image=self.left_image,
            right_image=self.right_image,
            source="upload"
        )
