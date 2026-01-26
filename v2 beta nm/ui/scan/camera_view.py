# ui/scan/camera_view.py
from PyQt5.QtCore import Qt, QTimer, QEvent, QElapsedTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtGui import QImage, QPixmap
from picamera2 import Picamera2
import cv2, time
from styles import ACCENT, BORD, MUTED


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
    """Full-screen camera preview. Tap to refocus, hold to capture."""

    def __init__(self, on_capture):
        super().__init__()
        
        self.picam2 = None
        self.timer = None
        self.running = False
        self.latest_frame = None
        
        self.on_capture = on_capture
        self.long_press = False
        self.press_timer = QElapsedTimer()

        # preview label (main focus)
        self.preview_label = QLabel("Camera Preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumSize(720, 400)
        self.preview_label.setStyleSheet(f"border:1px solid {BORD}; border-radius:12px; color:{MUTED};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.preview_label, 1)

        # enable tap / hold detection
        self.preview_label.installEventFilter(self)
        
        self.start_camera()

    # ---------- Preview ----------
    def update_preview(self):
        if not self.running or self.picam2 is None:
            return
        frame = self.picam2.capture_array()
        if frame is None:
            return
        frame_bgr = frame
        h, w = frame_bgr.shape[:2]
        side = min(h, w)
        y1, x1 = (h - side) // 2, (w - side) // 2
        cv2.rectangle(frame_bgr, (x1, y1), (x1 + side, y1 + side), (0, 255, 0), 2)
        self.latest_frame = frame_bgr
        self.preview_label.setPixmap(
            bgr_to_qpixmap(frame_bgr, fit=(self.preview_label.width(), self.preview_label.height()))
        )

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

    def refocus(self):
        """Trigger autofocus again."""
        try:
            self.picam2.set_controls({"AfTrigger": 0})
            print("[CameraView] Autofocus triggered.")
        except Exception as e:
            print("[CameraView] Refocus error:", e)

    def capture_frame(self):
        """Crop 1:1 and send to parent."""
        if self.latest_frame is None:
            return
        h, w = self.latest_frame.shape[:2]
        side = min(h, w)
        y1, x1 = (h - side) // 2, (w - side) // 2
        cropped = self.latest_frame[y1:y1 + side, x1:x1 + side].copy()
        self.on_capture(cropped)
        print("[CameraView] Captured via long press.")

    def start_camera(self):
        """(Re)start Picamera2 + preview timer if not running."""
        if self.running:
            return
        if self.picam2 is None:
            from picamera2 import Picamera2
            self.picam2 = Picamera2()
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
        print("[CameraView] started")

    def stop_camera(self):
        """Stop preview and camera but keep object reusable."""
        if not self.running:
            return
        try:
            if self.timer:
                self.timer.stop()
            if self.picam2:
                self.picam2.stop()
        except Exception:
            pass
        self.running = False
        print("[CameraView] stopped")
