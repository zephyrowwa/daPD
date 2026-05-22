import sys
import serial
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QLabel

class ServoControlGUI(QWidget):
    def __init__(self):
        super().__init__()
        try:
            # Change 'COM3' to your specific Arduino port
            self.arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            time.sleep(2) 
        except Exception as e:
            print(f"Connection Error: {e}")

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.checkboxes = []
        
        # Updated Labels to match the new 5,4,3,2,1,10,9,8,7,6 sequence
        labels = [
            "Servo (Port 5)", "Servo (Port 4)", "Servo (Port 3)", 
            "Servo (Port 2)", "Servo (Port 1)", "Servo (Port 10)", 
            "Servo (Port 9)", "Servo (Port 8)", "Servo (Port 7)", "Servo (Port 6)"
        ]

        layout.addWidget(QLabel("Select Servos to Run in Sequence:"))

        for label in labels:
            cb = QCheckBox(label)
            layout.addWidget(cb)
            self.checkboxes.append(cb)

        self.btn = QPushButton('Run Selected Sequence', self)
        self.btn.clicked.connect(self.send_commands)
        layout.addWidget(self.btn)

        self.setLayout(layout)
        self.setWindowTitle('Servo Controller - New Sequence')
        self.show()

    def send_commands(self):
        for i, cb in enumerate(self.checkboxes):
            if cb.isChecked():
                print(f"Sending trigger for: {cb.text()}")
                self.arduino.write(str(i).encode())
                # Wait for the physical movement to finish (1.2s + 1.0s + buffer)
                time.sleep(2.3) 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ServoControlGUI()
    sys.exit(app.exec_())