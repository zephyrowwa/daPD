# ui/scan/scan_page.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QPushButton
from styles import BRAND
from ui.scan.camera_view import CameraView
from ui.scan.result_view import ResultView
from analysis.segmentation import ToenailDetector, NailSegmentation, crop_detections, visualize_segmentation_masks


class ScanPage(QWidget):



    """Controller that switches between CameraView and ResultView."""

    def __init__(self, on_back, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.on_back = on_back


        # Main stacked pages (camera + result)
        self.stack = QStackedWidget(self)
        self.camera_view = CameraView(on_capture=self.show_result_page)
        self.result_view = ResultView(on_newscan=self.show_camera_page, db=self.db)
        self.stack.addWidget(self.camera_view)
        self.stack.addWidget(self.result_view)

        MODEL_PATH = "best_tn.pt"
        self.detector = ToenailDetector(MODEL_PATH)

        SEG_MODEL_PATH = "best.pt"
        self.segmentation = NailSegmentation(SEG_MODEL_PATH)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        # Floating Back button — always visible and above everything
        self.btn_back = QPushButton("←")
        self.btn_back.setParent(self)
        self.btn_back.setFixedSize(48, 32)
        self.btn_back.clicked.connect(self.handle_back)
        self.btn_back.raise_()  # ensure on top of all
        self.btn_back.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,0.85);
                color: {BRAND};
                border: 1.5px solid {BRAND};
                border-radius: 6px;
                font-family: 'DejaVu Sans','Segoe UI';
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.95); }}
            """
        )

        # Ensure the button is initially visible
        self.btn_back.show()

    # ---------- Event Handlers ----------
    def showEvent(self, e):
        """Whenever the Scan page becomes visible again, make sure the camera runs."""
        try:
            self.camera_view.start_camera()
        except Exception:
            pass
        # keep the floating back button on top
        self.btn_back.raise_()
        super().showEvent(e)

    def resizeEvent(self, event):
        """Keep the back button in the top-left corner."""
        self.btn_back.move(10, 10)
        super().resizeEvent(event)

    def handle_back(self):
        """Back to landing: stop camera cleanly, then navigate out."""
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        self.on_back()

    # ---------- Page Navigation ----------
    def show_result_page(self, captured_img):
        from PyQt5.QtWidgets import QApplication
        
        # Show loading overlay and navigate to result view
        self.stack.setCurrentWidget(self.result_view)
        self.btn_back.raise_()
        
        # Clear previous results before showing loading overlay
        self.result_view.clear_results()
        
        self.result_view.loading_overlay.start("Analyzing toenails...", "Detecting nails")
        QApplication.processEvents()
        
        print("[ScanPage] Running toenail detection...")
        
        detections = self.detector.detect(captured_img)
        print(f"[ScanPage] Detected {len(detections)} toenails")
        
        # Log all detections
        for i, det in enumerate(detections):
            bbox = det["bbox"]
            conf = det["confidence"]
            print(f"  [{i+1}] Bbox: {bbox}, Confidence: {conf:.3f}")
        
        # Crop individual toenails with padding (5-7 pixels on each side)
        cropped_nails = crop_detections(captured_img, detections, padding=6)
        
        print(f"[ScanPage] Cropped {len(cropped_nails)} toenail images")
        
        # Run segmentation on each cropped nail to detect classes
        self.result_view.loading_overlay.update_status("Analyzing toenails...", "Segmenting nails")
        print("[ScanPage] Running segmentation on cropped toenails...")
        for i, nail in enumerate(cropped_nails):
            seg_results = self.segmentation.segment(nail["image"])
            
            # Extract detected classes from segmentation (only nail and fungi, not toe)
            detected_classes = []
            for seg_det in seg_results:
                class_name = seg_det["class"].lower()
                # Only include nail and fungi classes
                if class_name in ["nail", "fungi"]:
                    seg_conf = seg_det["confidence"]
                    detected_classes.append({
                        "class": class_name,
                        "confidence": seg_conf
                    })
            
            nail["segmentation_classes"] = detected_classes
            
            # Create visualization of segmentation masks
            seg_visualization = visualize_segmentation_masks(nail["image"], seg_results)
            nail["segmentation_visualization"] = seg_visualization
            
            # Update UI progress
            self.result_view.loading_overlay.update_status(
                "Analyzing toenails...", 
                f"Segmenting nail {i+1}/{len(cropped_nails)}"
            )
            
            print(f"  Toenail {i+1}: {len(detected_classes)} classes detected - {[c['class'] for c in detected_classes]}")
        
        # Hide loading overlay and show results
        self.result_view.loading_overlay.stop()
        self.result_view.show_results(cropped_nails)

        self.btn_back.raise_()

    def show_camera_page(self):
        """Return from result → camera preview, (re)start camera."""
        try:
            self.camera_view.start_camera()
        except Exception:
            pass
        self.stack.setCurrentWidget(self.camera_view)
        self.btn_back.raise_()
        print("[ScanPage] Returning to camera preview.")

    def closeEvent(self, e):
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        super().closeEvent(e)
