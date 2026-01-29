# ui/scan/servo_control_view.py
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton
from PyQt5.QtGui import QFont, QImage, QPixmap
from picamera2 import Picamera2
import cv2
import serial
import time
from styles import BRAND, ACCENT, MUTED, BORD


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


class ServoControlView(QWidget):
    """Servo control interface matching camera view layout with servos on right side."""
    
    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.setObjectName("Canvas")
        
        self.on_back = on_back
        self.serial_port = None
        self.sequence_running = False
        self.servo_vars = {}
        self.current_camera_id = 0  # 0 = right, 1 = left
        
        # Camera
        self.picam2 = None
        self.timer = None
        self.camera_running = False
        self.latest_frame = None
        
        # Try to establish serial connection
        self._init_serial()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # Top row: Back button + Camera selection buttons
        top_row = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(80, 40)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                padding: 8px 12px;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
            QPushButton:pressed {{ background: #1e40af; }}
        """)
        back_btn.clicked.connect(on_back)
        top_row.addWidget(back_btn)
        
        top_row.addStretch()
        
        self.btn_left = QPushButton("Left Foot")
        self.btn_left.setFixedHeight(36)
        self.btn_left.setMinimumWidth(120)
        self.btn_left.setCheckable(True)
        self.btn_left.clicked.connect(lambda: self._switch_camera(1))
        self.btn_left.setStyleSheet(f"""
            QPushButton {{
                background: #d1d5db;
                color: #333;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:checked {{ background: #16a34a; color: white; }}
            QPushButton:pressed {{ background: #16a34a; color: white; }}
        """)
        
        self.btn_right = QPushButton("Right Foot")
        self.btn_right.setFixedHeight(36)
        self.btn_right.setMinimumWidth(120)
        self.btn_right.setCheckable(True)
        self.btn_right.setChecked(True)
        self.btn_right.clicked.connect(lambda: self._switch_camera(0))
        self.btn_right.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 6px 12px;
            }}
            QPushButton:checked {{ background: {BRAND}; }}
            QPushButton:pressed {{ background: {BRAND}; }}
        """)
        
        top_row.addWidget(self.btn_left)
        top_row.addSpacing(12)
        top_row.addWidget(self.btn_right)
        top_row.addStretch()
        main_layout.addLayout(top_row)
        
        # Content row: Camera feed on left, servos on right
        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        
        # Camera feed (left side)
        self.camera_label = QLabel("Camera Monitor\n(Right Foot)")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(500, 350)
        self.camera_label.setStyleSheet(f"border: 2px solid {BORD}; border-radius: 12px; background: #f9fafb; color: {MUTED};")
        self.camera_label.setFont(QFont("Segoe UI", 14))
        content_row.addWidget(self.camera_label)
        
        # Right side: Servos + Buttons column
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        
        # Servo checkboxes (will update based on camera selection)
        self.servo_container = QVBoxLayout()
        self.servo_container.setSpacing(6)
        
        # Create all servo checkboxes but only show relevant ones
        for i in range(1, 11):
            cb = QCheckBox(str(i))
            cb.setFont(QFont("Segoe UI", 12, QFont.Bold))
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 24px;
                    height: 24px;
                }
                QCheckBox::indicator:unchecked {
                    background: white;
                    border: 2px solid #d1d5db;
                    border-radius: 4px;
                }
                QCheckBox::indicator:checked {
                    background: #2563eb;
                    border: 2px solid #2563eb;
                    border-radius: 4px;
                }
            """)
            self.servo_vars[i] = cb
            self.servo_container.addWidget(cb)
        
        right_col.addLayout(self.servo_container)
        right_col.addStretch()
        
        # Control buttons (bottom of right column)
        button_col = QVBoxLayout()
        button_col.setSpacing(6)
        
        self.start_btn = QPushButton("START")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{ background: #15803d; }}
            QPushButton:pressed {{ background: #166534; }}
            QPushButton:disabled {{ background: #d1d5db; color: #9ca3af; }}
        """)
        self.start_btn.clicked.connect(self._start_sequence)
        
        self.clear_btn = QPushButton("CLEAR")
        self.clear_btn.setFixedHeight(40)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {MUTED};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 12px;
            }}
            QPushButton:hover {{ background: #4b5563; }}
            QPushButton:pressed {{ background: #374151; }}
            QPushButton:disabled {{ background: #d1d5db; color: #9ca3af; }}
        """)
        self.clear_btn.clicked.connect(self._clear_selection)
        
        button_col.addWidget(self.start_btn)
        button_col.addWidget(self.clear_btn)
        
        right_col.addLayout(button_col)
        
        content_row.addLayout(right_col, 0)
        main_layout.addLayout(content_row, 1)
        
        # Initialize servo view
        self._switch_camera(0)
    
    def showEvent(self, event):
        """Start camera when page becomes visible."""
        super().showEvent(event)
        if not self.camera_running:
            self._start_camera()
    
    def hideEvent(self, event):
        """Stop camera when page is hidden."""
        super().hideEvent(event)
        self._stop_camera()
    
    def _init_serial(self):
        """Initialize serial connection to Arduino."""
        try:
            self.serial_port = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            time.sleep(2)
            print("Serial connection established")
        except Exception as e:
            print(f"Serial connection error: {e}")
            self.serial_port = None
    
    def _start_camera(self):
        """Start Picamera2 with preview timer."""
        if self.camera_running:
            return
        
        try:
            if self.picam2 is None:
                self.picam2 = Picamera2(camera_num=self.current_camera_id)
            
            config = self.picam2.create_preview_configuration(
                main={"size": (1280, 720), "format": "RGB888"}
            )
            if config is None:
                print("[ServoControl] ERROR: Failed to create preview configuration")
                return
            
            self.picam2.configure(config)
            self.picam2.set_controls({
                "AwbEnable": True,
                "AeEnable": True,
                "AwbMode": 0,
                "AfMode": 2,
            })
            
            self.picam2.start()
            
            try:
                self.picam2.set_controls({"AfTrigger": 0})
            except Exception:
                pass
            
            if self.timer is None:
                self.timer = QTimer(self)
                self.timer.timeout.connect(self._update_preview)
            
            self.timer.start(33)
            self.camera_running = True
            foot_name = "Right Foot" if self.current_camera_id == 0 else "Left Foot"
            print(f"[ServoControl] Camera started - {foot_name}")
        except Exception as e:
            print(f"[ServoControl] Error starting camera: {e}")
    
    def _stop_camera(self):
        """Stop camera and preview."""
        if not self.camera_running:
            return
        
        try:
            if self.timer:
                self.timer.stop()
                self.timer = None
            if self.picam2:
                try:
                    if self.camera_running:
                        self.picam2.stop()
                except Exception:
                    pass
                try:
                    self.picam2.close()
                except Exception:
                    pass
                self.picam2 = None
        except Exception as e:
            print(f"[ServoControl] Error stopping camera: {e}")
        finally:
            self.camera_running = False
    
    def _update_preview(self):
        """Update camera preview."""
        if not self.camera_running or self.picam2 is None:
            return
        
        try:
            frame = self.picam2.capture_array()
            if frame is None:
                return
            
            self.latest_frame = frame
            self.camera_label.setPixmap(
                bgr_to_qpixmap(frame, fit=(self.camera_label.width(), self.camera_label.height()))
            )
        except Exception as e:
            print(f"[ServoControl] Error updating preview: {e}")
    
    def _switch_camera(self, camera_id):
        """Switch between left (1) and right (0) cameras."""
        if self.current_camera_id == camera_id:
            return
        
        self.current_camera_id = camera_id
        self.btn_left.setChecked(camera_id == 1)
        self.btn_right.setChecked(camera_id == 0)
        
        # Show/hide servos based on camera selection
        if camera_id == 0:  # Right foot -> servos 1-5
            visible_servos = list(range(1, 6))
        else:  # Left foot -> servos 6-10
            visible_servos = list(range(6, 11))
        
        # Show only relevant servos
        for i in range(1, 11):
            self.servo_vars[i].setVisible(i in visible_servos)
        
        # If camera is running, switch it
        if self.camera_running:
            # Stop old camera
            if self.timer:
                self.timer.stop()
            
            if self.picam2 is not None:
                try:
                    if self.camera_running:
                        self.picam2.stop()
                    self.picam2.close()
                except Exception as e:
                    print(f"[ServoControl] Error closing camera: {e}")
                finally:
                    self.picam2 = None
            
            self.camera_running = False
            time.sleep(0.3)
            
            # Start new camera
            self._start_camera()
        
        foot_name = "Right Foot" if camera_id == 0 else "Left Foot"
        self.camera_label.setText(f"Camera Monitor\n({foot_name})")
        print(f"[ServoControl] Switched to {foot_name}")
    
    def _start_sequence(self):
        """Start the servo sequence."""
        if not self.serial_port or not self.serial_port.is_open:
            print("Arduino not connected!")
            return
        
        self.sequence_running = True
        self.start_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Disable all checkboxes during sequence
        for cb in self.servo_vars.values():
            if cb.isVisible():
                cb.setEnabled(False)
        
        # Get selected servos
        selected_servos = [i for i in range(1, 11) if self.servo_vars[i].isChecked()]
        
        if not selected_servos:
            print("No servos selected!")
            self._stop_sequence()
            return
        
        # Run sequence
        self._run_servo_sequence(selected_servos)
    
    def _run_servo_sequence(self, servo_list):
        """Execute servo sequence with selected servos."""
        if not self.sequence_running:
            return
        
        for servo_id in servo_list:
            if not self.sequence_running:
                break
            
            print(f"Activating Servo {servo_id}...")
            try:
                self.serial_port.write(f"{servo_id}\n".encode())
                time.sleep(2.2)
            except Exception as e:
                print(f"Error sending servo command: {e}")
        
        if self.sequence_running:
            print("Sequence Complete.")
            self._stop_sequence()
    
    def _stop_sequence(self):
        """Stop the servo sequence."""
        self.sequence_running = False
        self.start_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # Enable all visible checkboxes
        for cb in self.servo_vars.values():
            if cb.isVisible():
                cb.setEnabled(True)
    
    def _clear_selection(self):
        """Clear all servo selections."""
        for cb in self.servo_vars.values():
            cb.setChecked(False)
    
    def closeEvent(self, event):
        """Clean up on close."""
        self._stop_camera()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()
