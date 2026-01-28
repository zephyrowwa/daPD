#!/usr/bin/env python3
"""Quick test of OSI grid visualization with various scenarios"""

import cv2
import numpy as np
from analysis.osi_grading import process_nail_for_grading

def test_scenario(name, nail_image, nail_mask, affected_mask):
    print(f"\n{'='*50}")
    print(f"Testing: {name}")
    print(f"{'='*50}")
    print(f"  Nail image: {nail_image.shape}")
    print(f"  Nail mask: {nail_mask.shape}, areas={np.sum(nail_mask > 0)}")
    print(f"  Affected mask: {affected_mask.shape}, areas={np.sum(affected_mask > 0)}")
    
    result = process_nail_for_grading(nail_image, nail_mask, affected_mask)
    
    if "error" in result:
        print(f"  ✗ Error: {result['error']}")
        return False
    
    osi_score = result.get("osi_score", {})
    print(f"  ✓ OSI Score: {osi_score.get('total_osi_score', 0)}/25")
    print(f"  ✓ Severity: {osi_score.get('severity', 'Unknown')}")
    print(f"  ✓ Area: {osi_score.get('area_percent', 0):.1f}%")
    
    grid_viz = result.get("grid_visualization")
    if grid_viz is not None:
        print(f"  ✓ Grid visualization created: {grid_viz.shape}")
        return True
    else:
        print(f"  ✗ No grid visualization")
        return False

# Test 1: Healthy nail (no infection)
print("\n" + "="*50)
print("TEST 1: HEALTHY NAIL (No Infection)")
print("="*50)

nail_image_1 = np.ones((256, 256, 3), dtype=np.uint8) * 220
nail_mask_1 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(nail_mask_1, (128, 128), 100, 255, -1)
affected_mask_1 = np.zeros((256, 256), dtype=np.uint8)

test_scenario("Healthy Nail", nail_image_1, nail_mask_1, affected_mask_1)

# Test 2: Mild infection (small, distal)
print("\n" + "="*50)
print("TEST 2: MILD INFECTION (Small, Distal)")
print("="*50)

nail_image_2 = np.ones((256, 256, 3), dtype=np.uint8) * 220
nail_mask_2 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(nail_mask_2, (128, 128), 100, 255, -1)
affected_mask_2 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(affected_mask_2, (128, 180), 30, 255, -1)  # Small spot at distal end

test_scenario("Mild Infection", nail_image_2, nail_mask_2, affected_mask_2)

# Test 3: Moderate infection
print("\n" + "="*50)
print("TEST 3: MODERATE INFECTION")
print("="*50)

nail_image_3 = np.ones((256, 256, 3), dtype=np.uint8) * 220
nail_mask_3 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(nail_mask_3, (128, 128), 100, 255, -1)
affected_mask_3 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(affected_mask_3, (128, 90), 60, 255, -1)  # Medium spot in middle

test_scenario("Moderate Infection", nail_image_3, nail_mask_3, affected_mask_3)

# Test 4: Severe infection (large, proximal)
print("\n" + "="*50)
print("TEST 4: SEVERE INFECTION (Large, Proximal)")
print("="*50)

nail_image_4 = np.ones((256, 256, 3), dtype=np.uint8) * 220
nail_mask_4 = np.zeros((256, 256), dtype=np.uint8)
cv2.circle(nail_mask_4, (128, 128), 100, 255, -1)
affected_mask_4 = np.zeros((256, 256), dtype=np.uint8)
cv2.ellipse(affected_mask_4, (128, 60), (80, 100), 0, 0, 360, 255, -1)  # Large area at proximal

test_scenario("Severe Infection", nail_image_4, nail_mask_4, affected_mask_4)

print("\n" + "="*50)
print("✓ All tests completed!")
print("="*50)

