import cv2
import numpy as np

# --- Step 1: Load segmentation masks (binary 0–255) ---
nail_mask = cv2.imread("nail_mask.png", cv2.IMREAD_GRAYSCALE)
fungi_mask = cv2.imread("fungi_mask.png", cv2.IMREAD_GRAYSCALE)

# Threshold in case masks are soft
nail_mask = (nail_mask > 128).astype(np.uint8)
fungi_mask = (fungi_mask > 128).astype(np.uint8)

# --- Step 2: Isolate the nail region ---
ys, xs = np.where(nail_mask > 0)
y_min, y_max = ys.min(), ys.max()
x_min, x_max = xs.min(), xs.max()

nail_roi = nail_mask[y_min:y_max, x_min:x_max]
fungi_roi = fungi_mask[y_min:y_max, x_min:x_max]

h, w = nail_roi.shape

# --- Step 3: Divide ROI into 20×20 grid (5 % each side) ---
step_y, step_x = h // 20, w // 20
affected_boxes = 0
total_boxes = 20 * 20

for i in range(20):
    for j in range(20):
        y1, y2 = i * step_y, (i + 1) * step_y
        x1, x2 = j * step_x, (j + 1) * step_x
        sub_nail = nail_roi[y1:y2, x1:x2]
        sub_fungi = fungi_roi[y1:y2, x1:x2]

        if sub_nail.sum() == 0:  # skip outside of nail
            continue

        ratio = sub_fungi.sum() / (sub_nail.sum() + 1e-5)
        if ratio > 0:  # any affected pixels → affected region
            affected_boxes += 1

area_percent = (affected_boxes / total_boxes) * 100

# --- Step 4: Assign Area Score (0–5) ---
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

# --- Step 5: Compute Proximity Score (1–5) ---
# Find topmost infected pixel (smaller y → closer to matrix)
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
    prox_score = 1  # no infection

# --- Step 6: Optional +10 points (if hyperkeratosis/streaks) ---
extra_points = 0  # change to 10 if a classifier detects such signs

# --- Step 7: Calculate OSI score ---
osi_score = (area_score * prox_score) + extra_points

if osi_score <= 5:
    severity = "Mild"
elif osi_score <= 15:
    severity = "Moderate"
else:
    severity = "Severe"

print(f"Area involvement: {area_percent:.2f}%  (score={area_score})")
print(f"Proximity to matrix: {prox_score}")
print(f"OSI Score: {osi_score} → {severity}")
