# ui/scan/camera_view.py
from PyQt5.QtCore import Qt, QTimer, QEvent, QElapsedTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton, QSlider
from PyQt5.QtGui import QImage, QPixmap
from picamera2 import Picamera2
import cv2, time
from styles import ACCENT, BORD, MUTED, BRAND


def bgr_to_qpixmap(frame_bgr, fit=(640, 400)):
    """Convert BGR numpy frame to QPixmap."""
    if frame_bgr is None:
        return QPixmap()
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb.shape
    qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    pix = QPixmap.fromImage(qimg)
    if fit:
        return pix.scaled(fit[0], fit[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
    return pix


class CameraView(QWidget):
    """Full-screen camera preview. Tap to refocus, hold to capture. Button with slider to zoom."""

    def __init__(self, on_capture):
        super().__init__()
        
        self.picam2 = None
        self.timer = None
        self.running = False
        self.latest_frame = None
        self.current_camera_id = 0  # 0 = right foot, 1 = left foot
        
        self.on_capture = on_capture
        self.long_press = False
        self.press_timer = QElapsedTimer()
        
        # Zoom
        self.zoom_level = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 3.0

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        # Top row: Camera selection buttons (centered)
        camera_row = QHBoxLayout()
        camera_row.addStretch()
        
        self.btn_left_foot = QPushButton("Left Foot")
        self.btn_left_foot.setFixedHeight(32)
        self.btn_left_foot.setMinimumWidth(120)
        self.btn_left_foot.setCheckable(True)
        self.btn_left_foot.clicked.connect(lambda: self.switch_camera(1))
        self.btn_left_foot.setStyleSheet(f"""
            QPushButton {{
                background: {MUTED};
                color: #333;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:checked {{ background: {BRAND}; color: white; }}
            QPushButton:pressed {{ background: {BRAND}; color: white; }}
        """)
        
        self.btn_right_foot = QPushButton("Right Foot")
        self.btn_right_foot.setFixedHeight(32)
        self.btn_right_foot.setMinimumWidth(120)
        self.btn_right_foot.setCheckable(True)
        self.btn_right_foot.setChecked(True)
        self.btn_right_foot.clicked.connect(lambda: self.switch_camera(0))
        self.btn_right_foot.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:checked {{ background: {BRAND}; }}
            QPushButton:pressed {{ background: {BRAND}; }}
        """)
        
        camera_row.addWidget(self.btn_left_foot)
        camera_row.addSpacing(12)
        camera_row.addWidget(self.btn_right_foot)
        camera_row.addStretch()
        
        # Preview row with zoom controls on the right
        preview_row = QHBoxLayout()
        
        self.preview_label = QLabel("Camera Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumSize(720, 400)
        self.preview_label.setStyleSheet(f"border:1px solid {BORD}; border-radius:12px; color:{MUTED};")
        
        # Zoom control column (right side)
        zoom_col = QVBoxLayout()
        
        self.btn_zoom = QPushButton("🔍")
        self.btn_zoom.setFixedSize(48, 48)
        self.btn_zoom.setCheckable(True)
        self.btn_zoom.clicked.connect(self.toggle_zoom_slider)
        self.btn_zoom.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 18px;
            }}
            QPushButton:pressed {{ background: {BRAND}; }}
        """)
        
        self.zoom_slider = QSlider(Qt.Vertical)
        self.zoom_slider.setMinimum(10)  # 1.0x
        self.zoom_slider.setMaximum(30)  # 3.0x
        self.zoom_slider.setValue(10)
        self.zoom_slider.setFixedWidth(24)
        self.zoom_slider.setMinimumHeight(150)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        self.zoom_slider.setVisible(False)
        self.zoom_slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                border: 1px solid {BORD};
                width: 8px;
                background: {MUTED};
                border-radius: 4px;
            }}
            QSlider::handle:vertical {{
                background: {ACCENT};
                border: 1px solid {ACCENT};
                height: 18px;
                margin: 0 -5px;
                border-radius: 9px;
            }}
        """)
        
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setFixedWidth(35)
        self.zoom_label.setStyleSheet("font-weight: 600; text-align: center;")
        self.zoom_label.setVisible(False)
        
        zoom_col.addWidget(self.btn_zoom, alignment=Qt.AlignHCenter)
        zoom_col.addWidget(self.zoom_slider, alignment=Qt.AlignHCenter)
        zoom_col.addWidget(self.zoom_label, alignment=Qt.AlignHCenter)
        zoom_col.addStretch()
        
        preview_row.addWidget(self.preview_label, 1)
        preview_row.addSpacing(8)
        preview_row.addLayout(zoom_col)

        main_layout.addLayout(camera_row)
        main_layout.addLayout(preview_row, 1)

        # enable tap / hold detection
        self.preview_label.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self.start_camera()

    # ---------- Preview ----------
    def update_preview(self):
        if not self.running or self.picam2 is None:
            return
        frame = self.picam2.capture_array()
        if frame is None:
            return
        frame_bgr = frame
        
        # Apply zoom
        if self.zoom_level > 1.0:
            frame_bgr = self.apply_zoom(frame_bgr)
        
        self.latest_frame = frame_bgr
        self.preview_label.setPixmap(
            bgr_to_qpixmap(frame_bgr, fit=(self.preview_label.width(), self.preview_label.height()))
        )
    
    def apply_zoom(self, frame):
        """Crop frame to apply zoom effect."""
        h, w = frame.shape[:2]
        
        # Calculate crop region
        crop_h = int(h / self.zoom_level)
        crop_w = int(w / self.zoom_level)
        
        # Center the crop
        y1 = (h - crop_h) // 2
        x1 = (w - crop_w) // 2
        y2 = y1 + crop_h
        x2 = x1 + crop_w
        
        # Crop and resize back to original size
        cropped = frame[y1:y2, x1:x2]
        zoomed = cv2.resize(cropped, (w, h))
        
        return zoomed

    # ---------- Tap / Hold ----------
    def eventFilter(self, source, event):
        if source == self.preview_label:
            if event.type() == QEvent.MouseButtonPress:
                self.press_timer.start()
                self.long_press = False
            elif event.type() == QEvent.MouseButtonRelease:
                elapsed = self.press_timer.elapsed()
                if elapsed > 600:  # >0.6s = long press
                    self.capture_frame()
                else:
                    self.refocus()
        return super().eventFilter(source, event)
    
    def toggle_zoom_slider(self):
        """Show/hide zoom slider."""
        is_visible = self.zoom_slider.isVisible()
        self.zoom_slider.setVisible(not is_visible)
        self.zoom_label.setVisible(not is_visible)
        self.btn_zoom.setChecked(not is_visible)
    
    def on_zoom_slider_changed(self, value):
        """Update zoom level from slider."""
        self.zoom_level = value / 10.0
        self.zoom_label.setText(f"{self.zoom_level:.1f}x")
        print(f"[CameraView] Zoom: {self.zoom_level:.1f}x")
    
    def switch_camera(self, camera_id):
        """Switch between cameras."""
        if self.current_camera_id == camera_id:
            return
        
        self.current_camera_id = camera_id
        
        # Update button states
        self.btn_right_foot.setChecked(camera_id == 0)
        self.btn_left_foot.setChecked(camera_id == 1)
        
        # Stop and fully release current camera
        self.stop_camera()
        
        # Properly close the camera
        if self.picam2 is not None:
            try:
                self.picam2.close()
            except Exception as e:
                print(f"[CameraView] Error closing camera: {e}")
            self.picam2 = None
        
        # Small delay to ensure resource is released
        import time
        time.sleep(0.5)
        
        # Start new camera
        self.start_camera()
        
        foot_name = "Right Foot (ID 0)" if camera_id == 0 else "Left Foot (ID 1)"
        print(f"[CameraView] Switched to {foot_name}")

    def refocus(self):
        """Trigger autofocus again."""
        try:
            self.picam2.set_controls({"AfTrigger": 0})
            print("[CameraView] Autofocus triggered.")
        except Exception as e:
            print("[CameraView] Refocus error:", e)

    def capture_frame(self):
        """Send frame to parent."""
        if self.latest_frame is None:
            return
        self.on_capture(self.latest_frame.copy())
        print("[CameraView] Captured via long press.")

    def start_camera(self):
        """(Re)start Picamera2 + preview timer if not running."""
        if self.running:
            return
        if self.picam2 is None:
            from picamera2 import Picamera2
            self.picam2 = Picamera2(camera_num=self.current_camera_id)
            self.picam2.configure(
                self.picam2.create_preview_configuration(
                    main={"size": (1280, 720), "format": "RGB888"}
                )
            )
            self.picam2.set_controls({
                "AwbEnable": True,
                "AeEnable": True,
                "AwbMode": 0,
                "AfMode": 2,  # single-shot AF
            })
        self.picam2.start()
        # initial focus sweep
        try:
            self.picam2.set_controls({"AfTrigger": 0})
        except Exception:
            pass

        if self.timer is None:
            from PyQt5.QtCore import QTimer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_preview)
        self.timer.start(33)
        self.running = True
        foot_name = "Right Foot (ID 0)" if self.current_camera_id == 0 else "Left Foot (ID 1)"
        print(f"[CameraView] started - {foot_name}")

    def stop_camera(self):
        """Stop preview and camera but keep object reusable."""
        if not self.running:
            return
        try:
            if self.timer:
                self.timer.stop()
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
        except Exception as e:
            print(f"[CameraView] Error stopping camera: {e}")
        self.running = False
        print("[CameraView] stopped")
