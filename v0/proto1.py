import cv2
import numpy as np
from ultralytics import YOLO
from tkinter import Tk, Label, Button, filedialog, Frame
from PIL import Image, ImageTk

# --------------------------------------------------
# Load your trained YOLOv11 model
# --------------------------------------------------
model = YOLO("best.pt")  # change path to your model


# --------------------------------------------------
# Function: Compute OSI
# --------------------------------------------------
def compute_osi(nail_mask, fungi_mask):
    nail_mask = (nail_mask > 128).astype(np.uint8)
    fungi_mask = (fungi_mask > 128).astype(np.uint8)

    ys, xs = np.where(nail_mask > 0)
    if len(ys) == 0 or len(xs) == 0:
        return 0, "No nail detected"

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    nail_roi = nail_mask[y_min:y_max, x_min:x_max]
    fungi_roi = fungi_mask[y_min:y_max, x_min:x_max]
    h, w = nail_roi.shape

    rows, cols = 4, 5
    step_y, step_x = h // rows, w // cols
    affected_cells = 0
    total_cells = rows * cols

    for i in range(rows):
        for j in range(cols):
            y1, y2 = i * step_y, (i + 1) * step_y
            x1, x2 = j * step_x, (j + 1) * step_x
            sub_nail = nail_roi[y1:y2, x1:x2]
            sub_fungi = fungi_roi[y1:y2, x1:x2]
            if sub_nail.sum() == 0:
                continue
            if sub_fungi.sum() > 0:
                affected_cells += 1

    area_percent = (affected_cells / total_cells) * 100
    if area_percent == 0:
        area_score = 0
    elif area_percent <= 10:
        area_score = 1
    elif area_percent <= 25:
        area_score = 2
    elif area_percent <= 50:
        area_score = 3
    elif area_percent <= 75:
        area_score = 4
    else:
        area_score = 5

    infected_y = np.where(fungi_roi > 0)[0]
    if len(infected_y) > 0:
        top_infected = infected_y.min()
        fraction_to_top = 1 - (top_infected / h)
        if fraction_to_top <= 0.25:
            prox_score = 1
        elif fraction_to_top <= 0.50:
            prox_score = 2
        elif fraction_to_top <= 0.75:
            prox_score = 3
        elif fraction_to_top < 1.0:
            prox_score = 4
        else:
            prox_score = 5
    else:
        prox_score = 1

    osi = area_score * prox_score
    if osi <= 5:
        severity = "Mild"
    elif osi <= 15:
        severity = "Moderate"
    else:
        severity = "Severe"

    return osi, severity, (x_min, y_min, x_max, y_max)


# --------------------------------------------------
# Function: Analyze image using YOLO
# --------------------------------------------------
def analyze_image(path):
    img = cv2.imread(path)
    orig_display = img.copy()
    results = model.predict(img, verbose=False)[0]

    nail_mask = np.zeros(img.shape[:2], np.uint8)
    fungi_mask = np.zeros(img.shape[:2], np.uint8)

    # Merge all masks properly
    for cls, mask in zip(results.boxes.cls, results.masks.data):
        label = results.names[int(cls)].lower()
        mask_img = (mask.cpu().numpy() * 255).astype(np.uint8)
        mask_resized = cv2.resize(mask_img, (img.shape[1], img.shape[0]))
        if label == "nail":
            nail_mask = cv2.bitwise_or(nail_mask, mask_resized)
        elif label == "fungi":
            fungi_mask = cv2.bitwise_or(fungi_mask, mask_resized)

    # --------------------------------------------------
    # Fix bounding box to cover the entire nail region
    # --------------------------------------------------
    ys, xs = np.where(nail_mask > 0)
    if len(ys) == 0 or len(xs) == 0:
        return img, orig_display, 0, "No nail detected"

    y_min, y_max = ys.min(), ys.max()
    x_min, x_max = xs.min(), xs.max()

    # Compute OSI
    osi, severity, _ = compute_osi(nail_mask, fungi_mask)

    # --------------------------------------------------
    # Draw full bounding box and 4x5 grid
    # --------------------------------------------------
    segmented_img = img.copy()
    cv2.rectangle(segmented_img, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)

    rows, cols = 4, 5
    step_y = (y_max - y_min) // rows
    step_x = (x_max - x_min) // cols

    for i in range(1, rows):
        y = y_min + i * step_y
        cv2.line(segmented_img, (x_min, y), (x_max, y), (0, 255, 0), 2)
    for j in range(1, cols):
        x = x_min + j * step_x
        cv2.line(segmented_img, (x, y_min), (x, y_max), (0, 255, 0), 2)

    cv2.putText(segmented_img, f"OSI Score: {osi} ({severity})", (x_min, y_min - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return segmented_img, orig_display, osi, severity


# --------------------------------------------------
# UI logic (Tkinter)
# --------------------------------------------------
def upload_image():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not path:
        return

    segmented_img, orig_img, osi, severity = analyze_image(path)

    # Convert for display
    def to_tkimage(img, maxsize=(500, 500)):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(img_rgb)
        im.thumbnail(maxsize)
        return ImageTk.PhotoImage(im)

    orig_tk = to_tkimage(orig_img)
    seg_tk = to_tkimage(segmented_img)

    panel_orig.configure(image=orig_tk)
    panel_orig.image = orig_tk
    panel_seg.configure(image=seg_tk)
    panel_seg.image = seg_tk

    result_label.config(text=f"Severity: {severity} (OSI={osi})")


# --------------------------------------------------
# Tkinter Layout
# --------------------------------------------------
root = Tk()
root.title("Onychomycosis Severity Classifier")

Label(root, text="Upload an image for OSI-based severity analysis").pack(pady=10)
Button(root, text="Select Image", command=upload_image).pack(pady=5)

frame = Frame(root)
frame.pack(pady=10)

panel_orig = Label(frame)
panel_orig.pack(side="left", padx=10)

panel_seg = Label(frame)
panel_seg.pack(side="left", padx=10)

result_label = Label(root, text="", font=("Arial", 14))
result_label.pack(pady=10)

root.mainloop()
