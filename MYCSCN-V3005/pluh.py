import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                             QLabel, QFileDialog, QHBoxLayout, 
                             QVBoxLayout, QWidget)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from ultralytics import YOLO

class YOLOv11UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv11 Instance Segmentation Viewer")
        self.setGeometry(100, 100, 1200, 600)

        # Load Model (Ensure you have 'yolo11n-seg.pt' or your custom weight file)
        self.model = YOLO("best.pt") 

        self.initUI()

    def initUI(self):
        # Main Layout
        main_layout = QVBoxLayout()
        image_layout = QHBoxLayout()

        # Labels for images
        self.lbl_original = QLabel("Original Image")
        self.lbl_original.setAlignment(Qt.AlignCenter)
        self.lbl_original.setStyleSheet("border: 1px solid black; background: #f0f0f0;")

        self.lbl_result = QLabel("Segmentation Result")
        self.lbl_result.setAlignment(Qt.AlignCenter)
        self.lbl_result.setStyleSheet("border: 1px solid black; background: #f0f0f0;")

        image_layout.addWidget(self.lbl_original)
        image_layout.addWidget(self.lbl_result)

        # Buttons
        self.btn_load = QPushButton("Select Image & Run Inference")
        self.btn_load.setFixedHeight(50)
        self.btn_load.clicked.connect(self.run_inference)

        main_layout.addLayout(image_layout)
        main_layout.addWidget(self.btn_load)

        # Central Widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def cv2_to_qpixmap(self, img):
        """Converts an OpenCV BGR image to a QPixmap for display."""
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QImage(img.data, width, height, bytes_per_line, QImage.Format_BGR888)
        return QPixmap.fromImage(q_img)

    def run_inference(self):
        # 1. Choose Image
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        
        if file_path:
            # 2. Run Model Inference
            results = self.model(file_path)
            result = results[0] # Get first result

            # 3. Process Original Image
            orig_img = result.orig_img
            # Resize for UI consistency (keeping aspect ratio)
            orig_img_resized = cv2.resize(orig_img, (580, 400))
            self.lbl_original.setPixmap(self.cv2_to_qpixmap(orig_img_resized))

            # 4. Process Annotated Image
            # plot() returns an image with both boxes and segmentation masks
            annotated_img = result.plot() 
            annotated_resized = cv2.resize(annotated_img, (580, 400))
            self.lbl_result.setPixmap(self.cv2_to_qpixmap(annotated_resized))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YOLOv11UI()
    window.show()
    sys.exit(app.exec_())