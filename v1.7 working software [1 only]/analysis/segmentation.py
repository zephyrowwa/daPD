# analysis/segmentation.py
import cv2
import numpy as np
from ultralytics import YOLO

# ------------------ YOLO wrapper ------------------
class NailSegmentation:
    def __init__(self, model_path="best.pt"):
        print(f"[Segmentation] Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)

    def segment(self, img_bgr):
        """
        Returns:
          nail_mask (H,W) uint8
          affected_mask (H,W) uint8
          nail_bbox_yolo (x1,y1,x2,y2) from YOLO *boxes* (union of all 'nail' boxes)
        """
        res = self.model.predict(img_bgr, verbose=False)[0]

        H, W = img_bgr.shape[:2]
        nail_mask = np.zeros((H, W), np.uint8)
        affected_mask = np.zeros((H, W), np.uint8)

        # collect all nail boxes to compute a single union bbox
        nail_boxes = []

        if res.masks is not None and len(res.masks) > 0:
            for box, cls, mask in zip(res.boxes.xyxy, res.boxes.cls, res.masks.data):
                label = res.names[int(cls)].lower()
                x1, y1, x2, y2 = map(int, box[:4])
                mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
                mask_resized = cv2.resize(mask_img, (W, H))

                if label in ("nail",):
                    nail_mask = cv2.bitwise_or(nail_mask, mask_resized)
                    nail_boxes.append((x1, y1, x2, y2))
                elif label in ("fungi", "affected"):
                    affected_mask = cv2.bitwise_or(affected_mask, mask_resized)

        # union bbox from YOLO 'nail' boxes (what you see in the viewer)
        nail_bbox_yolo = None
        if nail_boxes:
            xs1, ys1, xs2, ys2 = zip(*nail_boxes)
            x1 = max(0, min(xs1)); y1 = max(0, min(ys1))
            x2 = min(W - 1, max(xs2)); y2 = min(H - 1, max(ys2))
            nail_bbox_yolo = (int(x1), int(y1), int(x2), int(y2))

        return nail_mask, affected_mask, nail_bbox_yolo

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
def compute_osi(nail_mask, affected_mask, bbox=None, rows=4, cols=5):
    """
    Compute OSI using a 4×5 grid inside the given bbox (YOLO nail box).
    If bbox is None, falls back to mask extents.
    """
    nail = (nail_mask > 128).astype(np.uint8)
    fungi = (affected_mask > 128).astype(np.uint8)

    H, W = nail.shape
    if bbox is None:
        ys, xs = np.where(nail > 0)
        if len(xs) == 0:
            return 0, "No nail detected", (0, 0, 0, 0)
        y1, y2 = int(ys.min()), int(ys.max())
        x1, x2 = int(xs.min()), int(xs.max())
    else:
        x1, y1, x2, y2 = bbox

    # clamp
    x1 = max(0, min(W - 1, x1)); x2 = max(0, min(W - 1, x2))
    y1 = max(0, min(H - 1, y1)); y2 = max(0, min(H - 1, y2))
    if x2 <= x1 or y2 <= y1:
        return 0, "Invalid bbox", (0, 0, 0, 0)

    roi_nail = nail[y1:y2, x1:x2]
    roi_fun  = fungi[y1:y2, x1:x2]
    h, w = roi_nail.shape
    step_y, step_x = h // rows, w // cols

    affected_cells = 0
    for r in range(rows):
        for c in range(cols):
            ys = r * step_y; ye = (r + 1) * step_y if r < rows - 1 else h
            xs = c * step_x; xe = (c + 1) * step_x if c < cols - 1 else w
            if roi_fun[ys:ye, xs:xe].any():
                affected_cells += 1

    area_percent = affected_cells / (rows * cols) * 100.0
    area_score = 0 if area_percent == 0 else 1 if area_percent <= 10 else \
                 2 if area_percent <= 25 else 3 if area_percent <= 50 else \
                 4 if area_percent <= 75 else 5

    infected_y = np.where(roi_fun > 0)[0]
    if infected_y.size > 0:
        top = infected_y.min()
        frac = 1 - top / max(1, h)
        prox = 1 if frac <= 0.25 else 2 if frac <= 0.5 else \
               3 if frac <= 0.75 else 4 if frac < 1 else 5
    else:
        prox = 1

    osi = int(area_score * prox)
    severity = "Mild" if osi <= 5 else "Moderate" if osi <= 15 else "Severe"
    return osi, severity, (x1, y1, x2, y2)

# ------------------ Full pipeline ------------------
def run_full_analysis(model_path, img_bgr):
    seg = NailSegmentation(model_path)
    nail_mask, fungi_mask, yolo_bbox = seg.segment(img_bgr)

    # overlay masks
    overlay = draw_segmentation(img_bgr, nail_mask, fungi_mask)

    # OSI on YOLO nail bbox
    osi, severity, bbox = compute_osi(nail_mask, fungi_mask, bbox=yolo_bbox)

    # draw grid with that exact bbox
    out = draw_grid(overlay, bbox)

    # basic recs
    recommendation = (
        "Maintain regular nail hygiene." if severity == "Mild"
        else "Apply topical antifungal daily." if severity == "Moderate"
        else "Seek medical consultation for systemic therapy."
    )
    print(f"[Segmentation] OSI={osi} | Severity={severity}")
    return out, severity, recommendation
