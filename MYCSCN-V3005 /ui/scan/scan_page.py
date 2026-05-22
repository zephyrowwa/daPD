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
from analysis.segmentation import (
    ToenailDetector, NailSegmentation, crop_detections, 
    visualize_affected_area_only, get_affected_mask_and_bbox
)
from analysis.osi_grading import process_nail_for_grading, get_osi_score


class ScanPage(QWidget):
    """Controller that switches between SourceSelection, CameraView, UploadView, and ResultView."""

    def __init__(self, on_back, on_apply_med=None, parent=None):
        super().__init__(parent)
        self.on_back = on_back
        self.on_apply_med = on_apply_med
        self.returning_from_medication = False  # Flag to prevent showEvent override

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
            on_both_captured=self.on_both_feet_captured,
            on_upload=self.show_upload_page
        )
        
        # Page 2: Upload View
        self.upload_view = UploadView(
            on_images_ready=self.on_images_ready,
            on_back=self.show_camera_page
        )
        
        # Page 3: Result View
        self.result_view = ResultView(
            on_newscan=self.show_camera_page,
            on_apply_med=on_apply_med
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
        # If returning from medication, don't reset - keep showing the result view
        if self.returning_from_medication:
            self.returning_from_medication = False
            self.btn_back.raise_()
            super().showEvent(e)
            return
        
        try:
            self.camera_view.stop_camera()
        except Exception:
            pass
        # Reset camera state for new scan
        self.camera_view.reset_capture_state()
        # Show camera view directly (skip source selection)
        self.stack.setCurrentWidget(self.camera_view)
        self.camera_view.start_camera()
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
        self.camera_view.reset_capture_state()
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
        """
        Process a single foot image through the complete pipeline:
        1. Detection: Find toenails in full image
        2. Cropping: Crop each nail from detection bbox
        3. Segmentation: Run segmentation on each cropped nail
        4. Visualization: Show ONLY affected areas
        5. Grid & OSI: Calculate severity with grid overlay
        """
        from PyQt5.QtWidgets import QApplication
        
        print(f"\n{'='*60}")
        print(f"[ScanPage] Processing {foot_name} foot")
        print(f"{'='*60}")
        
        # STEP 1: DETECTION
        print(f"\n[Step 1] Running Detection Model...")
        detections = self.detector.detect(img_bgr)
        print(f"✓ Detected {len(detections)} toenails on {foot_name} foot")
        
        if len(detections) == 0:
            print(f"⚠ No toenails detected on {foot_name} foot")
            return {
                "image": img_bgr,
                "cropped_nails": [],
                "detections": []
            }
        
        for i, det in enumerate(detections, 1):
            bbox = det["bbox"]
            conf = det["confidence"]
            print(f"  [{i}] Bbox: {bbox}, Confidence: {conf:.3f}")
        
        # STEP 2: CROPPING
        print(f"\n[Step 2] Cropping individual toenails...")
        cropped_nails = crop_detections(img_bgr, detections, padding=10)
        print(f"✓ Cropped {len(cropped_nails)} toenail images (512x512)")
        
        # STEP 3: SEGMENTATION & VISUALIZATION
        print(f"\n[Step 3] Running Segmentation Model on each nail...")
        self.result_view.loading_overlay.update_status(
            "Analyzing toenails...", 
            f"Segmenting {foot_name} foot nails"
        )
        
        for i, nail in enumerate(cropped_nails, 1):
            print(f"\n  Nail #{i}:")
            nail_img = nail["image"]
            
            # Run segmentation on cropped nail
            seg_results = self.segmentation.segment(nail_img)
            print(f"    Segmentation detections: {len(seg_results)}")
            
            # Extract affected area and nail masks/bboxes
            affected_mask, affected_bbox = get_affected_mask_and_bbox(seg_results)
            nail_mask = None
            nail_bbox = None
            
            for seg_det in seg_results:
                class_name = seg_det["class"].lower()
                conf = seg_det["confidence"]
                print(f"      - {class_name}: confidence={conf:.3f}")
                
                if class_name == "nail":
                    nail_mask = seg_det["mask"]
                    nail_bbox = seg_det["bbox"]  # Get nail bbox for grid overlay
            
            # If no nail class found by segmentation, use affected area bbox for grading
            # This ensures accurate severity grading based on actual affected region
            if nail_bbox is None and affected_bbox is not None:
                print(f"    ⚠ No nail mask from segmentation, using affected area bbox for grading")
                nail_bbox = affected_bbox
            
            # Store segmentation results in nail data
            nail["seg_results"] = seg_results
            nail["nail_mask"] = nail_mask
            nail["nail_bbox"] = nail_bbox
            nail["affected_mask"] = affected_mask
            nail["affected_bbox"] = affected_bbox
            
            # STEP 4: VISUALIZATION - Show ONLY affected area
            print(f"    Creating affected area visualization...")
            seg_visualization = visualize_affected_area_only(nail_img, seg_results)
            nail["segmentation_visualization"] = seg_visualization
            
            # STEP 5: OSI GRADING with grid overlay
            print(f"    Calculating OSI severity...")
            nail["osi_result"] = self._calculate_osi_for_nail(
                nail_img, nail_mask, affected_mask, nail_bbox, foot_name, i
            )
        
        # Create detection visualization with bounding boxes and nail numbers
        print(f"\n[Step 6] Creating detection visualization with bounding boxes...")
        detection_viz = img_bgr.copy()
        for i, det in enumerate(detections, 1):
            bbox = det["bbox"]
            x1, y1, x2, y2 = bbox
            # Draw bounding box (cyan)
            cv2.rectangle(detection_viz, (x1, y1), (x2, y2), (0, 255, 255), 2)
            # Draw label with nail number
            label = f"Nail {i}"
            cv2.putText(
                detection_viz, label,
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )
        print(f"✓ Detection visualization created")
        
        print(f"\n✓ Completed processing of {foot_name} foot")
        print(f"{'='*60}\n")
        
        return {
            "image": img_bgr,
            "detection_visualization": detection_viz,
            "cropped_nails": cropped_nails,
            "detections": detections
        }
    
    def _calculate_osi_for_nail(self, nail_img, nail_mask, affected_mask, nail_bbox, foot_name, nail_idx):
        """
        Calculate OSI score and grid visualization for a single nail.
        Uses the nail segmentation bbox for grid overlay.
        """
        try:
            # If no affected area detected, nail is healthy
            if affected_mask is None:
                print(f"    ✓ No affected area detected - Healthy nail")
                return {
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
                    "grid_visualization": nail_img.copy()
                }
            
            # If we have affected area but no nail mask, use full image as nail
            if nail_mask is None:
                print(f"    ⚠ No nail mask, using full image")
                h, w = nail_img.shape[:2]
                nail_mask = np.ones((h, w), dtype=np.uint8) * 255
            
            # Call OSI grading with nail segmentation bbox
            osi_result = process_nail_for_grading(
                nail_img,
                nail_mask,
                affected_mask,
                nail_bbox_from_detection=nail_bbox
            )
            
            if "error" not in osi_result:
                osi_data = osi_result.get("osi_score", {})
                if "error" not in osi_data:
                    severity = osi_data.get("total_osi_score", 0)
                    print(f"    ✓ OSI Score: {severity}/25")
            else:
                print(f"    ✗ OSI grading error: {osi_result.get('error')}")
            
            return osi_result
            
        except Exception as e:
            print(f"    ✗ Error calculating OSI: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

