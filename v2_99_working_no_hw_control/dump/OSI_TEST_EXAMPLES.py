# OSI Grading Test Examples

Quick test cases to validate OSI scoring and grid visualization.

## Test 1: No Infection (Cured)

```python
from analysis.osi_grading import get_osi_score

result = get_osi_score(area_percent=0, proximity_level=1)
print(result)

# Expected Output:
# {
#     'area_score': 0,
#     'proximity_score': 1,
#     'total_osi_score': 0,
#     'severity': 'Clinically Cured / No involvement',
#     'area_percent': 0,
#     'proximity_level': 1
# }
```

## Test 2: Small Distal Infection (Mild)

```python
result = get_osi_score(area_percent=5, proximity_level=1)
print(result)

# Expected Output:
# {
#     'area_score': 1,
#     'proximity_score': 1,
#     'total_osi_score': 1,
#     'severity': 'Mild',
#     'area_percent': 5,
#     'proximity_level': 1
# }
```

## Test 3: Medium Infection (Moderate)

```python
result = get_osi_score(area_percent=40, proximity_level=3)
print(result)

# Expected Output:
# {
#     'area_score': 3,
#     'proximity_score': 3,
#     'total_osi_score': 9,
#     'severity': 'Moderate',
#     'area_percent': 40,
#     'proximity_level': 3
# }
```

## Test 4: Large Proximal Infection (Severe)

```python
result = get_osi_score(area_percent=85, proximity_level=4)
print(result)

# Expected Output:
# {
#     'area_score': 5,
#     'proximity_score': 4,
#     'total_osi_score': 20,
#     'severity': 'Severe',
#     'area_percent': 85,
#     'proximity_level': 4
# }
```

## Test 5: Matrix Involvement (Severe)

```python
result = get_osi_score(area_percent=30, proximity_level=5)
print(result)

# Expected Output:
# {
#     'area_score': 3,
#     'proximity_score': 5,
#     'total_osi_score': 15,
#     'severity': 'Moderate',  # Note: 15 is moderate, not severe
#     'area_percent': 30,
#     'proximity_level': 5
# }

# Even small infections at matrix level are problematic
result2 = get_osi_score(area_percent=5, proximity_level=5)
print(result2)

# {
#     'area_score': 1,
#     'proximity_score': 5,
#     'total_osi_score': 5,  # Still in mild range
#     'severity': 'Mild',
#     'area_percent': 5,
#     'proximity_level': 5
# }
```

## Test 6: Error Handling - Invalid Area

```python
result = get_osi_score(area_percent=150, proximity_level=1)
print(result)

# Expected Output:
# {'error': 'Invalid area percentage. Must be between 0 and 100.'}
```

## Test 7: Error Handling - Invalid Proximity

```python
result = get_osi_score(area_percent=50, proximity_level=10)
print(result)

# Expected Output:
# {'error': 'Invalid proximity level. Must be between 1 and 5.'}
```

## Test 8: Full Pipeline with Mock Data

```python
import numpy as np
from analysis.osi_grading import process_nail_for_grading

# Create mock nail image
nail_image = np.ones((512, 512, 3), dtype=np.uint8) * 200

# Create mock nail mask (white area representing nail)
nail_mask = np.zeros((512, 512), dtype=np.uint8)
nail_mask[50:450, 50:450] = 255  # Square nail region

# Create mock affected mask (infection area)
affected_mask = np.zeros((512, 512), dtype=np.uint8)
affected_mask[50:200, 50:450] = 255  # Top portion infected

result = process_nail_for_grading(nail_image, nail_mask, affected_mask)

print("OSI Result:")
print(f"  Score: {result['osi_score']['total_osi_score']}")
print(f"  Severity: {result['osi_score']['severity']}")
print(f"  Area: {result['osi_score']['area_percent']:.1f}%")
print(f"  Proximity: {result['osi_score']['proximity_level']}")

# Verify grid was created
print(f"\nGrid cells created: {len(result['grid_coordinates'])} rows")
print(f"Nail bounding box: {result['nail_bbox']}")

# The grid_visualization now has the 4x5 grid overlay
# You can display or save it:
import cv2
cv2.imshow("Grid Visualization", result["grid_visualization"])
cv2.waitKey(0)
cv2.destroyAllWindows()
```

## Test 9: Boundary Cases

```python
# Minimum severity (just barely infected)
result = get_osi_score(area_percent=1, proximity_level=1)
assert result['total_osi_score'] == 1
assert result['severity'] == 'Mild'

# Maximum severity
result = get_osi_score(area_percent=100, proximity_level=5)
assert result['total_osi_score'] == 25
assert result['severity'] == 'Severe'

# Edge between categories
result = get_osi_score(area_percent=50, proximity_level=1)
assert result['total_osi_score'] == 3  # 3 × 1
assert result['severity'] == 'Mild'  # 1-5 range

result = get_osi_score(area_percent=50, proximity_level=2)
assert result['total_osi_score'] == 6  # 3 × 2
assert result['severity'] == 'Moderate'  # 6-15 range

result = get_osi_score(area_percent=50, proximity_level=5)
assert result['total_osi_score'] == 15  # 3 × 5
assert result['severity'] == 'Moderate'  # Still 6-15 range

print("All boundary tests passed!")
```

## Test 10: Visual Verification

Create a simple test to see the grid overlay:

```python
import cv2
import numpy as np
from analysis.osi_grading import process_nail_for_grading

# Create a simple test image with nail and infection
image = np.ones((500, 500, 3), dtype=np.uint8) * 240

# Draw nail area in center
nail_mask = np.zeros((500, 500), dtype=np.uint8)
cv2.ellipse(nail_mask, (250, 250), (150, 180), 0, 0, 360, 255, -1)

# Create infection mask (top half of nail)
affected_mask = np.zeros((500, 500), dtype=np.uint8)
cv2.ellipse(affected_mask, (250, 200), (150, 100), 0, 0, 360, 255, -1)

# Process
result = process_nail_for_grading(image, nail_mask, affected_mask)

# Display
print(f"OSI Score: {result['osi_score']['total_osi_score']}")
print(f"Severity: {result['osi_score']['severity']}")

grid_viz = result['grid_visualization']
cv2.imshow('OSI Grid Visualization', grid_viz)
cv2.imwrite('osi_grid_test.png', grid_viz)  # Save for inspection
cv2.waitKey(1000)
cv2.destroyAllWindows()

print("Test image saved as 'osi_grid_test.png'")
```

## Running Tests

```bash
# In Python terminal or script:
python -c "
from analysis.osi_grading import get_osi_score

# Test mild
result = get_osi_score(5, 1)
print(f'Mild test: {result[\"total_osi_score\"]}/25 - {result[\"severity\"]}')

# Test moderate
result = get_osi_score(40, 3)
print(f'Moderate test: {result[\"total_osi_score\"]}/25 - {result[\"severity\"]}')

# Test severe
result = get_osi_score(85, 4)
print(f'Severe test: {result[\"total_osi_score\"]}/25 - {result[\"severity\"]}')
"
```

## Expected Behavior

After implementing OSI grading:

1. ✅ Each detected nail shows OSI score in UI (0-25)
2. ✅ Severity is color-coded (green/blue/amber/red)
3. ✅ Grid overlay appears with green lines
4. ✅ Infected areas highlighted in red
5. ✅ Console logs show OSI calculations
6. ✅ Database can store OSI scores with scan results

## Debug Checklist

- [ ] OSI module imports without errors
- [ ] Test cases 1-7 pass with expected output
- [ ] Mock data test (Test 8) creates grid visualization
- [ ] Boundary cases handled correctly
- [ ] Color coding matches severity levels
- [ ] Grid appears on result cards
- [ ] Console shows OSI calculations
