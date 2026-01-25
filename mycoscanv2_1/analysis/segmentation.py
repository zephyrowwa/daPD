
import cv2, numpy as np
from ultralytics import YOLO

class NailSegmentation:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def segment(self, img):
        res = self.model(img, verbose=False)[0]
        nail = np.zeros(img.shape[:2], np.uint8)
        fungi = np.zeros_like(nail)
        bbox = None

        for b, c, m in zip(res.boxes.xyxy, res.boxes.cls, res.masks.data):
            label = res.names[int(c)]
            mask = (m.cpu().numpy()*255).astype("uint8")
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]))
            x1,y1,x2,y2 = map(int,b)

            if label == "nail":
                nail |= mask
                bbox = (x1,y1,x2,y2)
            if label == "affected":
                fungi |= mask

        return nail, fungi, bbox

def compute_osi(nail, fungi):
    if fungi.sum() == 0:
        return 0, "Healthy"

    h,w = nail.shape
    bottom = fungi[int(h*0.75):h,:]
    ratio = bottom.sum() / nail.sum()

    if ratio < 0.25:
        return 1, "Mild"
    elif ratio < 0.5:
        return 4, "Moderate"
    return 12, "Severe"

def run_full_analysis(model, img):
    seg = NailSegmentation(model)
    nail, fungi, bbox = seg.segment(img)
    score, severity = compute_osi(nail, fungi)

    overlay = img.copy()
    overlay[fungi>0] = (0,0,255)

    rec = {
        "Healthy": "No action needed",
        "Mild": "Maintain nail hygiene",
        "Moderate": "Apply antifungal medication",
        "Severe": "Consult dermatologist"
    }[severity]

    return overlay, severity, rec
