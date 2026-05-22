#!/usr/bin/env python3
"""Test script to debug grading issues"""

import cv2
import numpy as np
from analysis.segmentation import ToenailDetector, NailSegmentation, crop_detections, get_affected_mask_and_bbox
from analysis.osi_grading import process_nail_for_grading
import os

# Find a test image
data_dir = "/home/team24/Desktop/MycoScan/data/scans"
test_subjects = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]

if not test_subjects:
    print("No test data found")
    exit(1)

test_subject = test_subjects[0]
subject_path = os.path.join(data_dir, test_subject)
print(f"Testing with subject: {test_subject}")

# Look for image files
image_files = [f for f in os.listdir(subject_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
if not image_files:
    print(f"No images found in {subject_path}")
    exit(1)

image_path = os.path.join(subject_path, image_files[0])
print(f"Loading image: {image_path}")

# Load image
img = cv2.imread(image_path)
if img is None:
    print(f"Could not load image: {image_path}")
    exit(1)

print(f"Image shape: {img.shape}")

# Initialize models
detector = ToenailDetector("best_tn.pt")
segmentation = NailSegmentation("best.pt")

# Step 1: Detection
print("\n[Step 1] Running detection...")
detections = detector.detect(img)
print(f"Detected {len(detections)} nails")

if len(detections) == 0:
    print("No nails detected")
    exit(1)

# Step 2: Cropping
print("\n[Step 2] Cropping nails...")
cropped_nails = crop_detections(img, detections)
print(f"Cropped {len(cropped_nails)} nails")

# Step 3: Segmentation & OSI calculation
print("\n[Step 3] Running segmentation and OSI grading...")
for i, nail in enumerate(cropped_nails, 1):  # Test all nails
    print(f"\n  Nail #{i}:")
    nail_img = nail["image"]
    
    # Run segmentation
    seg_results = segmentation.segment(nail_img)
    print(f"  Segmentation detections: {len(seg_results)}")
    
    for seg_det in seg_results:
        print(f"    - {seg_det['class']}: confidence={seg_det['confidence']:.3f}")
    
    # Extract masks
    affected_mask, affected_bbox = get_affected_mask_and_bbox(seg_results)
    nail_mask = None
    nail_bbox = None
    
    for seg_det in seg_results:
        if seg_det["class"].lower() == "nail":
            nail_mask = seg_det["mask"]
            nail_bbox = seg_det["bbox"]
    
    # Fallback: use affected bbox if no nail mask
    if nail_bbox is None and affected_bbox is not None:
        print(f"  Using affected area bbox as fallback")
        nail_bbox = affected_bbox
    
    # Fallback: create full mask if none exists
    if nail_mask is None:
        print(f"  No nail mask, creating full image mask")
        h, w = nail_img.shape[:2]
        nail_mask = np.ones((h, w), dtype=np.uint8) * 255
    
    print(f"  nail_bbox: {nail_bbox}")
    print(f"  nail_mask shape: {nail_mask.shape}, min: {nail_mask.min()}, max: {nail_mask.max()}")
    if affected_mask is not None:
        print(f"  affected_mask shape: {affected_mask.shape}, min: {affected_mask.min()}, max: {affected_mask.max()}")
    
    # Run OSI grading
    print(f"\n  Running OSI grading...")
    osi_result = process_nail_for_grading(
        nail_img,
        nail_mask,
        affected_mask,
        nail_bbox_from_detection=nail_bbox
    )
    
    if "osi_score" in osi_result:
        score = osi_result["osi_score"]
        print(f"\n  ✓ Results:")
        print(f"    Area: {score['area_percent']:.1f}% (Score: {score['area_score']}/5)")
        print(f"    Proximity: {score['proximity_level']}/5 (Score: {score['proximity_score']}/5)")
        print(f"    Total OSI Score: {score['total_osi_score']}/25")
        print(f"    Severity: {score['severity']}")
    else:
        print(f"  ✗ Error: {osi_result}")

print("\n[DONE]")
