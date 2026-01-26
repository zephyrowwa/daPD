# analysis/segmentation.py
import cv2
import numpy as np
from ultralytics import YOLO

# ------------------ YOLO wrapper ------------------
# analysis/segmentation.py
import cv2
import numpy as np
from ultralytics import YOLO

class NailSegmentation:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def segment(self, img):
        """
        Returns a list of detected nails.
        Each nail contains bbox, nail_mask, affected_mask
        """
        results = self.model.predict(img, verbose=False)[0]

        nails = []

        if results.masks is None:
            return nails

        for box, cls, mask in zip(
            results.boxes.xyxy,
            results.boxes.cls,
            results.masks.data
        ):
            label = results.names[int(cls)].lower()
            if label != "nail":
                continue

            x1, y1, x2, y2 = map(int, box[:4])

            mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
            mask_resized = cv2.resize(
                mask_img,
                (img.shape[1], img.shape[0])
            )

            nails.append({
                "bbox": (x1, y1, x2, y2),
                "nail_mask": mask_resized,
            })

        return nails


# ------------------ drawing helpers ------------------
def draw_segmentation(img_bgr, nail_mask, affected_mask):
    """Yellow = nail, Red = affected."""
    overlay = img_bgr.copy()
    color = np.zeros_like(img_bgr, np.uint8)
    color[nail_mask > 0] = (0, 255, 255)
    color[affected_mask > 0] = (0, 0, 255)
    return cv2.addWeighted(overlay, 1.0, color, 0.45, 0)

def draw_grid(img_bgr, bbox, rows=4, cols=5):
    if bbox is None:
        return img_bgr
    x1, y1, x2, y2 = bbox
    h, w = (y2 - y1), (x2 - x1)
    if h <= 0 or w <= 0:
        return img_bgr
    step_y, step_x = h // rows, w // cols
    out = img_bgr.copy()
    # outer box (cyan-ish like YOLO)
    cv2.rectangle(out, (x1, y1), (x2, y2), (255, 180, 0), 2)
    # grid
    for r in range(1, rows):
        y = y1 + r * step_y
        cv2.line(out, (x1, y), (x2, y), (0, 220, 0), 2)
    for c in range(1, cols):
        x = x1 + c * step_x
        cv2.line(out, (x, y1), (x, y2), (0, 220, 0), 2)
    return out

# ------------------ OSI computation ------------------
def compute_osi(nail_mask, affected_mask):
    nail = (nail_mask > 0).astype(np.uint8)
    affected = (affected_mask > 0).astype(np.uint8)

    ys, xs = np.where(nail > 0)
    if len(xs) == 0:
        return 0, "Healthy"

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    nail_roi = nail[y_min:y_max, x_min:x_max]
    affected_roi = affected[y_min:y_max, x_min:x_max]

    h, w = nail_roi.shape
    rows, cols = 4, 5
    step_y, step_x = h // rows, w // cols

    affected_cells = 0
    for i in range(rows):
        for j in range(cols):
            cell = affected_roi[
                i*step_y:(i+1)*step_y,
                j*step_x:(j+1)*step_x
            ]
            if cell.sum() > 0:
                affected_cells += 1

    percent = affected_cells / (rows * cols) * 100

    if percent == 0:
        return 0, "Healthy"
    elif percent <= 10:
        return 1, "Mild"
    elif percent <= 25:
        return 2, "Moderate"
    else:
        return 3, "Severe"

# ------------------ Full pipeline ------------------
def run_full_analysis(model_path, full_img):
    segmenter = NailSegmentation(model_path)
    nails = segmenter.segment(full_img)

    results = []

    for nail in nails:
        bbox = nail["bbox"]
        nail_mask = nail["nail_mask"]

        crop = crop_square_from_bbox(full_img, bbox)

        # affected mask = intersection
        affected_mask = cv2.bitwise_and(nail_mask, nail_mask)

        osi, severity = compute_osi(nail_mask, affected_mask)

        results.append({
            "image": crop,
            "severity": severity,
            "osi": osi
        })

    return results

def crop_square_from_bbox(img, bbox, padding=10):
    x1, y1, x2, y2 = bbox
    h, w = img.shape[:2]

    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    side = max(x2 - x1, y2 - y1) + padding

    half = side // 2
    x1 = max(cx - half, 0)
    y1 = max(cy - half, 0)
    x2 = min(cx + half, w)
    y2 = min(cy + half, h)

    return img[y1:y2, x1:x2].copy()

