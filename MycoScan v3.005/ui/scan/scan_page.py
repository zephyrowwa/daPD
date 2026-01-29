# ui/scan/scan_page.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QPushButton
import numpy as np
import cv2
from styles import BRAND
from ui.scan.camera_view import CameraView
from ui.scan.result_view import ResultView
from ui.scan.source_selection import SourceSelection
from ui.scan.upload_view import UploadView
from analysis.segmentation import ToenailDetector, NailSegmentation, crop_detections, visualize_segmentation_masks
from analysis.osi_grading import process_nail_for_grading, get_osi_score


class ScanPage(QWidget):
    """Controller that switches between SourceSelection, CameraView, UploadView, and ResultView."""

    def __init__(self, on_back, parent=None):
        super().__init__(parent)
        self.on_back = on_back

        # Main stacked pages
        self.stack = QStackedWidget(self)
        
        # Page 0: Source Selection
        self.source_selection = SourceSelection(
            on_capture=self.show_camera_page,
            on_upload=self.show_upload_page,
            on_back=on_back
        )
        
        # Page 1: Camera View (for dual-foot capture)
        self.camera_view = CameraView(
            on_capture=None,  # Legacy callback, not used in new workflow
            on_both_captured=self.on_both_feet_captured
        )
        
        # Page 2: Upload View
        self.upload_view = UploadView(
            on_images_ready=self.on_images_ready,
            on_back=self.show_source_selection
        )
        
        # Page 3: Result View
        self.result_view = ResultView(
            on_newscan=self.show_source_selection
        )
        
        self.stack.addWidget(self.source_selection)  # 0
        self.stack.addWidget(self.camera_view)       # 1
        self.stack.addWidget(self.upload_view)       # 2
        self.stack.addWidget(self.result_view)       # 3

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
        """Whenever the Scan page becomes visible again, reset and show source selection."""
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        # Reset camera state for new scan
        self.camera_view.reset_capture_state()
        # Show source selection page
        self.stack.setCurrentWidget(self.source_selection)
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
    def show_source_selection(self):
        """Show the source selection page."""
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        self.camera_view.reset_capture_state()
        self.stack.setCurrentWidget(self.source_selection)
        self.btn_back.raise_()
        print("[ScanPage] Showing source selection page")
    
    def show_camera_page(self):
        """Show the camera capture page for dual-foot capture."""
        self.stack.setCurrentWidget(self.camera_view)
        self.btn_back.raise_()
        self.camera_view.start_camera()
        print("[ScanPage] Showing camera view for capture")
    
    def show_upload_page(self):
        """Show the upload page."""
        self.stack.setCurrentWidget(self.upload_view)
        self.btn_back.raise_()
        print("[ScanPage] Showing upload view")
    
    def on_both_feet_captured(self, left_image, right_image, source):
        """Process both captured foot images."""
        self.on_images_ready(left_image, right_image, source)
    
    def on_images_ready(self, left_image, right_image, source):
        """Process images from either capture or upload."""
        from PyQt5.QtWidgets import QApplication
        
        # Show loading overlay and navigate to result view
        self.stack.setCurrentWidget(self.result_view)
        self.btn_back.raise_()
        
        # Clear previous results before showing loading overlay
        self.result_view.clear_results()
        
        self.result_view.loading_overlay.start("Analyzing toenails...", "Detecting nails")
        QApplication.processEvents()
        
        print("[ScanPage] Processing both feet images...")
        
        # Process both left and right feet
        feet_data = {
            "left": self._process_foot_image(left_image, "Left"),
            "right": self._process_foot_image(right_image, "Right")
        }
        
        # Hide loading overlay and show results
        self.result_view.loading_overlay.stop()
        self.result_view.show_results(feet_data)
        
        self.btn_back.raise_()
    
    def _process_foot_image(self, img_bgr, foot_name):
        """Process a single foot image."""
        from PyQt5.QtWidgets import QApplication
        
        print(f"[ScanPage] Processing {foot_name} foot...")
        
        detections = self.detector.detect(img_bgr)
        print(f"[ScanPage] Detected {len(detections)} toenails on {foot_name} foot")
        
        # Log all detections
        for i, det in enumerate(detections):
            bbox = det["bbox"]
            conf = det["confidence"]
            print(f"  [{i+1}] Bbox: {bbox}, Confidence: {conf:.3f}")
        
        # Crop individual toenails with padding
        cropped_nails = crop_detections(img_bgr, detections, padding=6)
        
        print(f"[ScanPage] Cropped {len(cropped_nails)} toenail images on {foot_name} foot")
        
        # Run segmentation on each cropped nail
        self.result_view.loading_overlay.update_status(
            "Analyzing toenails...", 
            f"Segmenting {foot_name} foot nails"
        )
        
        for i, nail in enumerate(cropped_nails):
            seg_results = self.segmentation.segment(nail["image"])
            
            # Extract detected classes from segmentation
            detected_classes = []
            nail_mask = None
            nail_bbox = None
            affected_mask = None
            
            for seg_det in seg_results:
                class_name = seg_det["class"].lower()
                if class_name in ["nail", "fungi"]:
                    seg_conf = seg_det["confidence"]
                    detected_classes.append({
                        "class": class_name,
                        "confidence": seg_conf
                    })
                    
                    # Store masks for OSI grading
                    mask_data = seg_det.get("mask")
                    if mask_data is not None:
                        if hasattr(mask_data, 'cpu'):
                            mask_data = mask_data.cpu().numpy()
                        if hasattr(mask_data, 'numpy'):
                            mask_data = mask_data.numpy()
                        
                        if class_name == "nail":
                            nail_mask = mask_data
                            nail_bbox = seg_det.get("bbox")
                        elif class_name == "fungi":
                            affected_mask = mask_data
            
            nail["segmentation_classes"] = detected_classes
            
            # Create visualization of segmentation masks
            seg_visualization = visualize_segmentation_masks(nail["image"], seg_results)
            nail["segmentation_visualization"] = seg_visualization
            
            # Initialize osi_result with a default value
            nail["osi_result"] = None
            
            # Simple fallback: if no fungi detected, mark as healthy
            # This avoids misclassification when segmentation is uncertain
            if affected_mask is None:
                # No fungi detected during segmentation - nail is healthy
                print(f"  ✓ Toenail {i+1} ({foot_name}): OSI 0/25 (No fungi detected - Healthy)")
                nail["osi_result"] = {
                    "osi_score": {
                        "area_score": 0,
                        "proximity_score": 1,
                        "total_osi_score": 0,
                        "severity": "Clinically Cured / No involvement",
                        "area_percent": 0,
                        "proximity_level": 1
                    },
                    "grid_analysis": {
                        "area_percent": 0,
                        "proximity_level": 1,
                        "total_nail_area_px": 0,
                        "affected_area_px": 0
                    },
                    "grid_visualization": nail["image"].copy(),
                    "nail_segmentation_visualization": nail["image"].copy(),
                    "grid_coordinates": [],
                    "nail_bbox": None
                }
            # Calculate OSI score if we have nail mask and fungi detected
            elif nail_mask is not None:
                try:
                    osi_result = process_nail_for_grading(
                        nail["image"],
                        nail_mask,
                        affected_mask,
                        nail_bbox_from_detection=nail_bbox
                    )
                    
                    nail["osi_result"] = osi_result
                    
                    if "error" not in osi_result:
                        osi_data = osi_result.get("osi_score", {})
                        if "error" not in osi_data:
                            print(f"  ✓ Toenail {i+1} ({foot_name}): OSI {osi_data.get('total_osi_score', 0)}/25")
                except Exception as e:
                    print(f"  ✗ OSI Grading failed for {foot_name} nail {i+1}: {str(e)}")
                    nail["osi_result"] = {"osi_score": {"error": str(e)}}
            else:
                # No nail mask detected - assume healthy nail with 0% affected area
                print(f"  ⚠ No nail mask detected for {foot_name} nail {i+1}, assuming healthy")
                
                # Create a healthy OSI result (0% affected = Healthy)
                try:
                    # Get image dimensions to create masks
                    h, w = nail["image"].shape[:2] if len(nail["image"].shape) >= 2 else (512, 512)
                    
                    # Create a simple bounding box from image dimensions
                    default_bbox = (0, 0, w, h)
                    
                    # Create masks: full nail mask, no affected areas
                    nail_mask_default = np.ones((h, w), dtype=np.uint8) * 255
                    affected_mask_default = np.zeros((h, w), dtype=np.uint8)
                    
                    osi_result = process_nail_for_grading(
                        nail["image"],
                        nail_mask_default,
                        affected_mask_default,
                        nail_bbox_from_detection=default_bbox
                    )
                    
                    nail["osi_result"] = osi_result
                    print(f"  ✓ Toenail {i+1} ({foot_name}): Assumed healthy (no segmentation data)")
                    
                except Exception as e:
                    print(f"  ✗ Failed to create default healthy score for {foot_name} nail {i+1}: {str(e)}")
                    nail["osi_result"] = {"osi_score": {"error": "Could not analyze nail"}}
            
            print(f"  {foot_name} Toenail {i+1}: {len(detected_classes)} classes detected")
        
        # Create detection visualization with bounding boxes and labels
        detection_viz = img_bgr.copy()
        for i, det in enumerate(detections, 1):
            bbox = det["bbox"]
            x1, y1, x2, y2 = bbox
            # Draw bounding box (cyan)
            cv2.rectangle(detection_viz, (x1, y1), (x2, y2), (0, 255, 255), 2)
            # Draw label
            label = f"Nail {i}"
            cv2.putText(
                detection_viz, label,
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )
        
        return {
            "image": img_bgr,
            "detection_visualization": detection_viz,
            "cropped_nails": cropped_nails,
            "detections": detections
        }

