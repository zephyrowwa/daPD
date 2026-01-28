# analysis/segmentation.py
import cv2
import numpy as np
from ultralytics import YOLO


class ToenailDetector:
    """Detect toenails using YOLO object detection model."""
    
    def __init__(self, model_path):
        self.model = YOLO(model_path)
    
    def detect(self, img):
        """
        Run object detection on image.
        Returns list of detected toenails with bounding boxes.
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
    """Segment toenails and affected areas using YOLO."""
    
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def segment(self, img):
        """
        Run segmentation model on image.
        Returns list of detected objects with their masks and class.
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
            
            # Resize mask to original image size
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


def crop_detections(img, detections, padding=6, resize_to=512):
    """
    Crop individual toenail images from detections as square crops.
    Centers on detection and adds padding to make a square.
    Resizes to specified size for model input.
    Returns list of cropped toenail images.
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
            "bbox": bbox,
            "confidence": detection["confidence"]
        })
    
    return cropped_nails


def visualize_segmentation_masks(img, seg_results):
    """
    Visualize segmentation masks with class-specific colors.
    No bounding boxes or labels - just the colored masks.
    Only shows nail and fungi classes (filters out toe).
    
    Color mapping:
    - nail: White (255, 255, 255)
    - fungi: Yellow (0, 255, 255) in BGR
    """
    out = img.copy()
    
    # Define colors for each class (BGR format)
    class_colors = {
        "nail": (255, 255, 255),      # White
        "fungi": (0, 255, 255),       # Yellow (BGR)
    }
    
    # Draw each segmentation mask
    for detection in seg_results:
        class_name = detection["class"].lower()
        
        # Skip toe class
        if class_name == "toe":
            continue
        
        mask = detection["mask"]
        
        # Get color for this class
        color = class_colors.get(class_name, (128, 128, 128))  # Gray default
        
        # Create colored overlay
        colored_mask = np.zeros_like(out, np.uint8)
        colored_mask[mask > 127] = color
        
        # Blend mask with original image (40% transparency)
        out = cv2.addWeighted(out, 1.0, colored_mask, 0.35, 0)
    
    return out


def visualize_detections(img, detections):
    """
    Draw detected toenails on the image.
    Shows bounding boxes and confidence scores.
    """
    out = img.copy()
    
    for detection in detections:
        bbox = detection["bbox"]
        confidence = detection["confidence"]
        
        # Draw bounding box in cyan
        x1, y1, x2, y2 = bbox
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 255), 2)
        
        # Draw label with confidence
        label = f"Toenail {confidence:.2f}"
        cv2.putText(
            out, label,
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )
    
    return out
    """
    Draw nail segmentations on the image.
    - Nail mask: White overlay
    - Bounding box: White outline
    """
    out = img.copy()
    
    # Draw each detection
    for detection in detections:
        class_name = detection["class"]
        
        # Only show nails
        if class_name != "nail":
            continue
        
        mask = detection["mask"]
        bbox = detection["bbox"]
        
        # Draw mask overlay in white
        mask_overlay = np.zeros_like(out, np.uint8)
        mask_overlay[mask > 0] = (255, 255, 255)  # White
        out = cv2.addWeighted(out, 1.0, mask_overlay, 0.35, 0)
        
        # Draw bounding box in white
        x1, y1, x2, y2 = bbox
        cv2.rectangle(out, (x1, y1), (x2, y2), (255, 255, 255), 2)
    
    return out

