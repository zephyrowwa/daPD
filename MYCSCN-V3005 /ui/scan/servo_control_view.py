# ui/scan/servo_control_view.py
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QMessageBox
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
    """Apply medication interface with pipeline: Left foot (servos 5-1) -> Next -> Right foot (servos 6-10) -> Apply -> Confirm -> Sequence -> Done."""
    
    def __init__(self, on_back, on_medication_done=None, parent=None):
        super().__init__(parent)
        self.setObjectName("Canvas")
        
        self.on_back = on_back
        self.on_medication_done = on_medication_done  # Callback when medication is done (return to results)
        self.serial_port = None
        self.sequence_running = False
        self.medication_applied = False  # Track if medication has been applied
        self.servo_vars = {}
        self.current_camera_id = 1  # 1 = left foot (default), 0 = right foot
        
        # Arduino portMap sequence: [5, 4, 3, 2, 1, 10, 9, 8, 7, 6]
        self.port_map = [5, 4, 3, 2, 1, 10, 9, 8, 7, 6]
        # Mapping servo number to its index in port_map
        self.servo_to_index = {servo: idx for idx, servo in enumerate(self.port_map)}
        
        # Track servo selections for each foot
        self.left_foot_selection = set()  # Servos 5,4,3,2,1
        self.right_foot_selection = set()  # Servos 10,9,8,7,6
        
        # Camera
        self.picam2 = None
        self.timer = None
        self.camera_running = False
        self.latest_frame = None
        
        # Try to establish serial connection
        self._init_serial()
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Top row: Back button + Foot indicators + APPLY button
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)
        
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(70, 32)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
            QPushButton:pressed {{ background: #1e40af; }}
        """)
        back_btn.clicked.connect(on_back)
        top_row.addWidget(back_btn)
        
        # Foot indicators (like camera view)
        self.status_left_label = QLabel("Left Foot: ●")
        self.status_left_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        
        self.status_right_label = QLabel("Right Foot: ◯")
        self.status_right_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        
        top_row.addWidget(self.status_left_label)
        top_row.addSpacing(8)
        top_row.addWidget(self.status_right_label)
        
        top_row.addStretch()
        
        # APPLY button (top right)
        self.apply_btn = QPushButton("APPLY")
        self.apply_btn.setFixedSize(80, 32)
        self.apply_btn.setEnabled(False)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                padding: 4px 8px;
            }}
            QPushButton:hover {{ background: #15803d; }}
            QPushButton:pressed {{ background: #166534; }}
            QPushButton:disabled {{ background: #d1d5db; color: #9ca3af; }}
        """)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        top_row.addWidget(self.apply_btn)
        
        main_layout.addLayout(top_row)
        
        # Camera feed (maximized)
        self.camera_label = QLabel("Camera Monitor")
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumSize(640, 340)
        self.camera_label.setStyleSheet(f"border: 2px solid {BORD}; border-radius: 12px; background: #f9fafb; color: {MUTED};")
        self.camera_label.setFont(QFont("Segoe UI", 12))
        main_layout.addWidget(self.camera_label, 1)
        
        # Servo selection row (below camera, horizontal, equally spaced)
        servo_row = QHBoxLayout()
        servo_row.setSpacing(4)
        servo_row.setContentsMargins(0, 6, 0, 0)
        servo_row.setAlignment(Qt.AlignCenter)
        
        # Create all servo checkboxes
        for i in range(1, 11):
            cb = QCheckBox()
            cb.setFixedSize(40, 40)
            cb.setText("")
            cb.stateChanged.connect(self._on_servo_selection_changed)
            cb.setStyleSheet("""
                QCheckBox {
                    spacing: 0px;
                    margin: 0px;
                    padding: 0px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                }
                QCheckBox::indicator:unchecked {
                    background: white;
                    border: 2px solid #d1d5db;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background: #2563eb;
                    border: 2px solid #2563eb;
                    border-radius: 3px;
                }
            """)
            self.servo_vars[i] = cb
            cb.setVisible(False)
        
        # Add checkboxes to layout in the correct order: 5,4,3,2,1,10,9,8,7,6
        for servo_num in [5, 4, 3, 2, 1, 10, 9, 8, 7, 6]:
            servo_row.addWidget(self.servo_vars[servo_num], alignment=Qt.AlignCenter)
        
        # Stretcher to separate checkboxes from buttons
        servo_row.addStretch()
        
        # All button
        self.all_btn = QPushButton("ALL")
        self.all_btn.setFixedSize(54, 32)
        self.all_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 700;
                font-size: 10px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
            QPushButton:pressed {{ background: #1e40af; }}
        """)
        self.all_btn.clicked.connect(self._on_all_clicked)
        servo_row.addWidget(self.all_btn)
        
        # Next button
        self.next_btn = QPushButton("NEXT")
        self.next_btn.setFixedSize(60, 32)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BRAND};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 10px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{ background: #1d4ed8; }}
            QPushButton:pressed {{ background: #1e40af; }}
        """)
        self.next_btn.clicked.connect(self._on_next_clicked)
        self.next_btn.setVisible(True)  # Visible only on left foot
        servo_row.addWidget(self.next_btn)
        
        main_layout.addLayout(servo_row)
        
        # Initialize to left foot view
        self._switch_to_left_foot()
    
    def showEvent(self, event):
        """Reset pipeline and start camera when page becomes visible."""
        super().showEvent(event)
        # Reset to clean state for new patient
        self._reset_pipeline_silent()
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
    
    def _switch_to_left_foot(self):
        """Switch to left foot view (servos 5,4,3,2,1)."""
        self.current_camera_id = 1
        self.status_left_label.setText("Left Foot: ●")
        self.status_left_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        self.status_right_label.setText("Right Foot: ◯")
        self.status_right_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        
        # Update servo nums and show only left foot servos (5,4,3,2,1)
        self.servo_nums = [1,2,3,4,5]
        
        # Hide all servos first, then show only the ones we need
        for i in range(1, 11):
            self.servo_vars[i].setVisible(False)
        
        for servo_num in self.servo_nums:
            self.servo_vars[servo_num].setVisible(True)
        
        self.next_btn.setVisible(True)
        self.next_btn.setEnabled(True)
        self.all_btn.setEnabled(True)
        self.apply_btn.setEnabled(False)
        
        # Switch camera
        if self.camera_running:
            if self.timer:
                self.timer.stop()
            if self.picam2 is not None:
                try:
                    if self.camera_running:
                        self.picam2.stop()
                    self.picam2.close()
                except Exception:
                    pass
                finally:
                    self.picam2 = None
            self.camera_running = False
            time.sleep(0.3)
            self._start_camera()
        
        print("[ServoControl] Switched to Left Foot")
    
    def _switch_to_right_foot(self):
        """Switch to right foot view (servos 10,9,8,7,6)."""
        self.current_camera_id = 0
        self.status_left_label.setText("Left Foot: ●")
        self.status_left_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        self.status_right_label.setText("Right Foot: ●")
        self.status_right_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        
        # Update servo nums and show only right foot servos (10,9,8,7,6)
        self.servo_nums = [6, 7, 8, 9, 10]
        
        # Hide all servos first, then show only the ones we need
        for i in range(1, 11):
            self.servo_vars[i].setVisible(False)
        
        for servo_num in self.servo_nums:
            self.servo_vars[servo_num].setVisible(True)
        
        self.next_btn.setVisible(False)
        self._update_apply_button_state()
        
        # Switch camera
        if self.camera_running:
            if self.timer:
                self.timer.stop()
            if self.picam2 is not None:
                try:
                    if self.camera_running:
                        self.picam2.stop()
                    self.picam2.close()
                except Exception:
                    pass
                finally:
                    self.picam2 = None
            self.camera_running = False
            time.sleep(0.3)
            self._start_camera()
        
        print("[ServoControl] Switched to Right Foot")
    
    def _on_servo_selection_changed(self):
        """Update apply button state when servo selection changes."""
        # Track which servos are selected
        if self.current_camera_id == 1:  # Left foot
            self.left_foot_selection = set(i for i in self.servo_nums if self.servo_vars[i].isChecked())
        else:  # Right foot
            self.right_foot_selection = set(i for i in self.servo_nums if self.servo_vars[i].isChecked())
        
        self._update_apply_button_state()
    
    def _update_apply_button_state(self):
        """Enable/disable APPLY button based on conditions."""
        if self.current_camera_id == 1:  # Left foot view
            # Not on right foot, so can't apply
            self.apply_btn.setEnabled(False)
        else:  # Right foot view
            # Can apply if at least 1 servo is selected
            total_selected = len(self.left_foot_selection) + len(self.right_foot_selection)
            self.apply_btn.setEnabled(total_selected > 0 and not self.medication_applied)
    
    def _on_all_clicked(self):
        """Select all servos on the current side."""
        for servo_num in self.servo_nums:
            self.servo_vars[servo_num].setChecked(True)
        self._on_servo_selection_changed()
    
    def _on_next_clicked(self):
        """Move from left foot to right foot."""
        if self.current_camera_id == 1:  # Currently on left foot
            # Save left foot selection
            self.left_foot_selection = set(i for i in range(1, 6) if self.servo_vars[i].isChecked())
            # Switch to right foot
            self._switch_to_right_foot()
    
    def _on_apply_clicked(self):
        """Handle APPLY button click - show confirmation dialog."""
        if self.medication_applied:
            return
        
        # Check if both feet have selections
        total_selected = len(self.left_foot_selection) + len(self.right_foot_selection)
        if total_selected == 0:
            QMessageBox.warning(self, "No Servos Selected", "Please select at least one servo before applying.")
            return
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Medication Application",
            "Are you sure you selected the right ones and want to apply?",
            QMessageBox.Ok | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Ok:
            self._execute_servo_sequence()
        else:
            # User cancelled - reset pipeline to clean state
            self._reset_pipeline()
    
    def _execute_servo_sequence(self):
        """Execute the servo sequence for both feet."""
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.critical(self, "Error", "Arduino not connected!")
            return
        
        self.sequence_running = True
        self.apply_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.all_btn.setEnabled(False)
        
        # Disable all checkboxes
        for i in range(1, 11):
            self.servo_vars[i].setEnabled(False)
        
        # Collect all selected servos
        selected_servos = sorted(list(self.left_foot_selection) + list(self.right_foot_selection))
        
        # Run sequence - send the index from port_map, not the servo number
        for servo_num in selected_servos:
            if not self.sequence_running:
                break
            
            servo_index = self.servo_to_index[servo_num]
            print(f"Activating Servo {servo_num} (index {servo_index})...")
            try:
                self.serial_port.write(f"{servo_index}\n".encode())
                time.sleep(2.2)
            except Exception as e:
                print(f"Error sending servo command: {e}")
        
        print("Servo sequence complete.")
        self.sequence_running = False
        self.medication_applied = True
        
        # Show success popup with options
        self._show_medication_applied_dialog()
    
    def _show_medication_applied_dialog(self):
        """Show the medication applied dialog with Done and Apply Again options."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Medication Applied")
        msg.setText("Medication applied.")
        msg.setInformativeText("Apply again?")
        msg.setMinimumWidth(500)
        
        btn_done = msg.addButton("Done", QMessageBox.AcceptRole)
        btn_again = msg.addButton("Apply Again", QMessageBox.RejectRole)
        
        msg.exec_()
        
        if msg.clickedButton() == btn_done:
            # Return to results screen
            if self.on_medication_done:
                self.on_medication_done()
            else:
                self.on_back()
        else:
            # Reset the pipeline
            self._reset_pipeline()
    
    def _reset_pipeline_silent(self):
        """Reset the apply medication pipeline without switching camera (for showEvent)."""
        self.medication_applied = False
        self.left_foot_selection = set()
        self.right_foot_selection = set()
        self.sequence_running = False
        
        # Clear all selections
        for i in range(1, 11):
            self.servo_vars[i].setChecked(False)
            self.servo_vars[i].setEnabled(True)
        
        # Reset to left foot state without switching camera
        self.current_camera_id = 1
        self.status_left_label.setText("Left Foot: ●")
        self.status_left_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        self.status_right_label.setText("Right Foot: ◯")
        self.status_right_label.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {BRAND};")
        
        # Update servo nums to left foot
        self.servo_nums = [5, 4, 3, 2, 1]
        
        # Hide all servos first, then show only the ones we need
        for i in range(1, 11):
            self.servo_vars[i].setVisible(False)
        
        for servo_num in self.servo_nums:
            self.servo_vars[servo_num].setVisible(True)
        
        self.next_btn.setVisible(True)
        self.next_btn.setEnabled(True)
        self.all_btn.setEnabled(True)
        self.apply_btn.setEnabled(False)
        
        print("[ServoControl] Pipeline reset (silent)")
    
    def _reset_pipeline(self):
        """Reset the apply medication pipeline."""
        self.medication_applied = False
        self.left_foot_selection = set()
        self.right_foot_selection = set()
        self.sequence_running = False
        
        # Clear all selections
        for i in range(1, 11):
            self.servo_vars[i].setChecked(False)
            self.servo_vars[i].setEnabled(True)
        
        # Return to left foot
        self._switch_to_left_foot()
    
    def closeEvent(self, event):
        """Clean up on close."""
        self._stop_camera()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

