
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QInputDialog
import cv2
from analysis.segmentation import run_full_analysis

class ScanPage(QWidget):
    def __init__(self, on_back, db):
        super().__init__()
        self.db = db
        self.on_back = on_back
        self.img = None

        layout = QVBoxLayout(self)
        self.label = QLabel("Scan Result Appears Here")
        layout.addWidget(self.label)

        btn_scan = QPushButton("Simulate Scan")
        btn_scan.clicked.connect(self.fake_scan)
        layout.addWidget(btn_scan)

        self.btn_save = QPushButton("Save Result")
        self.btn_save.clicked.connect(self.save)
        layout.addWidget(self.btn_save)

        btn_hist = QPushButton("View History")
        btn_hist.clicked.connect(on_back)
        layout.addWidget(btn_hist)

    def fake_scan(self):
        self.img = cv2.imread("sample.jpg") if cv2.imread("sample.jpg") is not None else None
        if self.img is None:
            self.label.setText("No sample image")
            return
        out, sev, rec = run_full_analysis("best.pt", self.img)
        self.result = (out, sev, rec)
        self.label.setText(f"Severity: {sev}")

    def save(self):
        if not hasattr(self, "result"):
            return
        name, ok = QInputDialog.getText(self, "Patient", "Patient name")
        if ok:
            self.db.add_scan(name, self.result[1], self.result[2], "segmented.png")
