import sys
import time
import cv2
import os
import re
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from picamera2 import Picamera2

class CameraThread(QThread):
    change_pixmap_signal = pyqtSignal(object)
    focus_status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.camera_id = 0
        self.picam2 = None
        self._needs_switch = False
        self._capture_pending = False
        self._capture_path = None

    def run(self):
        while self.running:
            try:
                self.picam2 = Picamera2(camera_num=self.camera_id)
                config = self.picam2.create_preview_configuration(
                    main={"size": (1280, 720), "format": "BGR888"} 
                )
                self.picam2.configure(config)
                self.picam2.start()
                
                # Initial autofocus - AfMode 2 is 'Auto' (focuses once)
                self.picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
                time.sleep(1.5)  # Wait for initial focus
                self.focus_status_signal.emit(f"Camera {self.camera_id} focused")
                print(f"--- Camera {self.camera_id} Started with Autofocus ---")
                
                while self.running and not self._needs_switch:
                    frame = self.picam2.capture_array()
                    if frame is not None:
                        self.change_pixmap_signal.emit(frame.copy())
                        
                        # Handle capture if pending
                        if self._capture_pending and self._capture_path:
                            # Convert RGB to BGR for cv2.imwrite
                            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            cv2.imwrite(self._capture_path, bgr_frame)
                            print(f"Saved: {self._capture_path}")
                            self._capture_pending = False
                            self._capture_path = None
                    
                    self.msleep(16)

                self.cleanup_camera()
                if self._needs_switch:
                    self._needs_switch = False
                    time.sleep(0.5)
                
            except Exception as e:
                print(f"Camera Error: {e}")
                self.cleanup_camera()
                self.msleep(1000)

    def refocus(self):
        """Manually trigger an autofocus sweep"""
        if self.picam2:
            try:
                self.picam2.set_controls({"AfMode": 2, "AfTrigger": 0})
                print("Autofocus triggered")
                time.sleep(1.5)
                self.focus_status_signal.emit("Refocused")
            except Exception as e:
                print(f"Refocus error: {e}")
    
    def capture_image(self, filepath):
        """Queue an image capture"""
        self._capture_path = filepath
        self._capture_pending = True

    def cleanup_camera(self):
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
            except: pass
            self.picam2 = None

    def switch(self, new_id):
        self.camera_id = new_id
        self._needs_switch = True

    def stop(self):
        self.running = False
        self.wait()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.current_id = 0
        self.capture_count = 0
        self.output_dir = "forda"
        
        # Create output directory if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Auto-detect the highest number in the folder
        self._auto_detect_counter()
        
        self.setWindowTitle("MycoScan - Dual Camera AF")
        self.display_label = QLabel("Initializing...")
        self.display_label.setFixedSize(480, 300)
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet("background: #000; border: 1px solid #333;")
        
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: white; background: #222; padding: 5px;")
        
        # Switch Button
        self.btn_switch = QPushButton(f"Switch to Camera {1 - self.current_id}")
        self.btn_switch.setFixedSize(480, 45)
        self.btn_switch.clicked.connect(self.toggle_camera)

        # Refocus Button
        self.btn_refocus = QPushButton("Manual Refocus")
        self.btn_refocus.setFixedSize(480, 45)
        self.btn_refocus.clicked.connect(self.trigger_refocus)
        
        # Capture Button
        self.btn_capture = QPushButton("Capture Image")
        self.btn_capture.setFixedSize(480, 45)
        self.btn_capture.setStyleSheet("background: #2ecc71; color: white; font-weight: bold;")
        self.btn_capture.clicked.connect(self.capture_image)
        
        # Reset Counter Button
        self.btn_reset = QPushButton("Reset Counter")
        self.btn_reset.setFixedSize(480, 45)
        self.btn_reset.clicked.connect(self.reset_counter)

        layout = QVBoxLayout()
        layout.addWidget(self.display_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.status_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_switch, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_refocus, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_capture, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_reset, alignment=Qt.AlignCenter)
        self.setLayout(layout)

        self.thread = CameraThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.focus_status_signal.connect(self.update_status)
        self.thread.start()

    def bgr_to_qpixmap(self, frame_rgb, fit=(480, 300)):
        if frame_rgb is None: return QPixmap()
        h, w, ch = frame_rgb.shape
        qimg = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        if fit:
            return pix.scaled(fit[0], fit[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pix
    
    def _auto_detect_counter(self):
        """Scan folder for existing images and set counter to max number + 1"""
        max_num = 0
        if os.path.exists(self.output_dir):
            for filename in os.listdir(self.output_dir):
                # Extract number from filename (e.g., "l119.jpg" -> 119)
                match = re.search(r'[lr](\d+)', filename)
                if match:
                    num = int(match.group(1))
                    max_num = max(max_num, num)
        self.capture_count = max_num

    def toggle_camera(self):
        self.current_id = 1 - self.current_id
        self.btn_switch.setText(f"Switch to Camera {1 - self.current_id}")
        self.update_status(f"Switching to Camera {self.current_id}")
        self.thread.switch(self.current_id)

    def trigger_refocus(self):
        self.update_status("Refocusing...")
        self.thread.refocus()
    
    def capture_image(self):
        """Capture image and alternate cameras"""
        self.capture_count += 1
        camera_prefix = "l" if self.current_id == 0 else "r"
        filename = f"{camera_prefix}{self.capture_count}.jpg"
        filepath = os.path.join(self.output_dir, filename)
        
        self.thread.capture_image(filepath)
        self.update_status(f"Captured {filename}")
        
        # Auto-switch camera for next capture
        time.sleep(0.5)
        self.toggle_camera()
    
    def reset_counter(self):
        """Reset the capture counter"""
        self.capture_count = 0
        self.update_status("Counter reset to 0")

    @pyqtSlot(object)
    def update_image(self, bgr_frame):
        pixmap = self.bgr_to_qpixmap(bgr_frame)
        self.display_label.setPixmap(pixmap)
    
    @pyqtSlot(str)
    def update_status(self, message):
        self.status_label.setText(message)

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())