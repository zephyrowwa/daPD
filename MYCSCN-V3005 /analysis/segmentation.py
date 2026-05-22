# analysis/segmentation.py
"""
Pipeline:
1. Detection Model: Detect toenails in full image → crop with padding
2. Segmentation Model: Run on each cropped nail → get affected area mask
3. Visualization: Show ONLY affected area (fungi/disease) overlay
4. Grid: Overlay grid on affected area (based on segmentation bbox)
5. OSI Grading: Calculate severity
"""

import cv2
import numpy as np
from ultralytics import YOLO


class ToenailDetector:
    """Detect toenails using YOLO object detection model (best_tn.pt)."""
    
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def detect(self, img):
        """
        Run object detection on full image.
        Returns list of detected toenails with bounding boxes.
        
        Args:
            img: Input image (BGR)
            
        Returns:
            List of detections with 'class', 'confidence', 'bbox' keys
        """
        results = self.model.predict(img, verbose=False)[0]
        
        detections = []
        
        if results.boxes is None:
            return detections
        
        # Process each detection
        for box, cls, conf in zip(
            results.boxes.xyxy,
            results.boxes.cls,
            results.boxes.conf
        ):
            x1, y1, x2, y2 = map(int, box[:4])
            class_name = results.names[int(cls)].lower()
            confidence = float(conf)
            
            detections.append({
                "class": class_name,
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2)
            })
        
        return detections


class NailSegmentation:
    """Segment nails and affected areas using YOLO segmentation model (best.pt)."""
    
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def segment(self, img):
        """
        Run segmentation model on cropped nail image.
        
        Args:
            img: Cropped nail image (BGR), typically 512x512
            
        Returns:
            List of segmentation detections with:
            - 'class': class name (nail, fungi/affected, toe)
            - 'confidence': confidence score
            - 'bbox': bounding box in original image coords
            - 'mask': binary mask (same size as input img)
        """
        results = self.model.predict(img, verbose=False)[0]
        
        detections = []
        
        if results.masks is None:
            return detections
        
        # Process each detection
        for box, cls, conf, mask in zip(
            results.boxes.xyxy,
            results.boxes.cls,
            results.boxes.conf,
            results.masks.data
        ):
            x1, y1, x2, y2 = map(int, box[:4])
            class_name = results.names[int(cls)].lower()
            confidence = float(conf)
            
            # Convert mask to numpy and resize to input image size
            mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
            mask_resized = cv2.resize(
                mask_img,
                (img.shape[1], img.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )
            
            detections.append({
                "class": class_name,
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2),
                "mask": mask_resized
            })
        
        return detections


def crop_detections(img, detections, padding=10, resize_to=512):
    """
    Crop individual toenails from full image based on detection bboxes.
    Creates square crops centered on detection with padding.
    
    Args:
        img: Full image (BGR)
        detections: List of detections from ToenailDetector
        padding: Padding in pixels to add around bbox
        resize_to: Target size for cropped image (None to keep original size)
        
    Returns:
        List of cropped nail data dicts with 'image' and metadata
    """
    cropped_nails = []
    h, w = img.shape[:2]
    
    for detection in detections:
        bbox = detection["bbox"]
        x1, y1, x2, y2 = bbox
        
        # Calculate bbox dimensions
        bbox_w = x2 - x1
        bbox_h = y2 - y1
        
        # Use the larger dimension + padding for square size
        size = max(bbox_w, bbox_h) + (padding * 2)
        
        # Center point of bbox
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        
        # Calculate square crop around center
        half_size = size // 2
        crop_x1 = max(cx - half_size, 0)
        crop_y1 = max(cy - half_size, 0)
        crop_x2 = min(cx + half_size, w)
        crop_y2 = min(cy + half_size, h)
        
        # Crop the image
        cropped = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        
        # If crop is at boundary, pad to make it square
        crop_h, crop_w = cropped.shape[:2]
        if crop_h != crop_w:
            max_dim = max(crop_h, crop_w)
            # Create square image with black padding
            square = np.zeros((max_dim, max_dim, cropped.shape[2]), dtype=cropped.dtype)
            # Center the cropped image in the square
            y_offset = (max_dim - crop_h) // 2
            x_offset = (max_dim - crop_w) // 2
            square[y_offset:y_offset + crop_h, x_offset:x_offset + crop_w] = cropped
            cropped = square
        
        # Resize to target size for segmentation model
        if resize_to:
            cropped_resized = cv2.resize(cropped, (resize_to, resize_to), interpolation=cv2.INTER_LINEAR)
        else:
            cropped_resized = cropped
        
        cropped_nails.append({
            "image": cropped_resized,
            "bbox": bbox,  # Original bbox in full image
            "crop_bbox": (crop_x1, crop_y1, crop_x2, crop_y2),  # Crop region in full image
            "confidence": detection["confidence"]
        })
    
    return cropped_nails


def visualize_affected_area_only(img, seg_results):
    """
    Visualize ONLY the affected area (fungi/disease) on the nail image.
    DOES NOT show nail boundaries - only the diseased/affected area.
    
    Args:
        img: Input image (BGR)
        seg_results: List of segmentation detections from NailSegmentation.segment()
        
    Returns:
        Image with only affected area overlaid in yellow
    """
    out = img.copy()
    
    # Process only fungi/affected class
    for detection in seg_results:
        class_name = detection["class"].lower()
        
        # ONLY visualize affected/fungi areas
        if class_name not in ["fungi", "affected", "disease"]:
            continue
        
        mask = detection["mask"]
        
        # Create yellow overlay for affected areas (BGR: 0, 255, 255)
        affected_overlay = np.zeros_like(out, np.uint8)
        affected_overlay[mask > 127] = (0, 255, 255)  # Yellow in BGR
        
        # Blend affected areas with strong visibility (60% transparency)
        out = cv2.addWeighted(out, 1.0, affected_overlay, 0.60, 0)
    
    return out


def get_affected_mask_and_bbox(seg_results):
    """
    Extract the affected area mask and bounding box from segmentation results.
    
    Args:
        seg_results: List of segmentation detections
        
    Returns:
        Tuple of (affected_mask, affected_bbox) or (None, None) if not found
    """
    for detection in seg_results:
        class_name = detection["class"].lower()
        if class_name in ["fungi", "affected", "disease"]:
            return detection["mask"], detection["bbox"]
    
    return None, None

