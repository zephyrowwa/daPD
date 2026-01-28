# OSI Grading Integration Guide

## Overview

The Onychomycosis Severity Index (OSI) grading system has been integrated into your MycoScan application. After nail detection and segmentation, the system automatically calculates OSI scores and displays them with a 4x5 grid overlay visualization.

## Components

### 1. **OSI Grading Module** (`analysis/osi_grading.py`)

Core functions for OSI scoring and grid analysis:

#### `OSIGridAnalyzer` Class
- **Purpose**: Analyzes nail affected areas using a 4x5 grid overlay
- **Key Methods**:
  - `detect_nail_contour()`: Detects nail boundaries from segmentation mask
  - `create_grid_overlay()`: Generates 4x5 grid coordinates
  - `analyze_grid_cells()`: Calculates infection percentage and proximity level

#### `get_osi_score(area_percent, proximity_level)`
Calculates OSI score based on:
- **Area Score** (A): 0-5 based on infection percentage
  - 0%: Score 0
  - 1-10%: Score 1
  - 11-25%: Score 2
  - 26-50%: Score 3
  - 51-75%: Score 4
  - 76-100%: Score 5

- **Proximity Score** (P): 1-5 based on nail location
  - 1: Distal quarter (tip)
  - 2: Second quarter
  - 3: Third quarter
  - 4: Proximal quarter (base)
  - 5: Matrix involvement (lunula/proximal fold)

- **Final Score**: Area Score × Proximity Score (0-25)

- **Severity Classification**:
  - 0: Clinically Cured / No involvement
  - 1-5: Mild
  - 6-15: Moderate
  - 16-25: Severe

#### `process_nail_for_grading()`
Complete pipeline that:
1. Detects nail contour
2. Creates 4x5 grid overlay
3. Analyzes affected areas
4. Calculates OSI score
5. Returns grid visualization with overlay

#### `draw_grid_on_image()`
Renders the 4x5 grid and infection highlights on the nail image

### 2. **Pipeline Integration** (`ui/scan/scan_page.py`)

The scan page now performs these steps:
1. **Detection**: YOLO object detection for nail localization
2. **Segmentation**: Semantic segmentation for nail and fungi classes
3. **Cropping**: Extract individual nail images
4. **OSI Grading**: For each nail:
   - Extract nail mask and affected area mask
   - Run `process_nail_for_grading()`
   - Store results in nail data

```python
# Example from scan_page.py
if nail_mask is not None and affected_mask is not None:
    osi_result = process_nail_for_grading(
        nail["image"],
        nail_mask,
        affected_mask
    )
    nail["osi_result"] = osi_result
```

### 3. **UI Display** (`ui/scan/result_view.py`)

Updated result card now displays:
- **OSI Score**: 0-25 (prominent display)
- **Severity**: Color-coded severity classification
  - Green: Clinically Cured
  - Blue: Mild
  - Amber: Moderate
  - Red: Severe
- **Affected Area %**: Calculated infection percentage
- **Grid Visualization**: 4x5 grid overlay on nail image highlighting affected areas

## Data Flow

```
Captured Image
    ↓
[YOLO Detection]
    ↓
Detected Toenails + Bounding Boxes
    ↓
[Crop Detections]
    ↓
Cropped Nail Images
    ↓
[YOLO Segmentation] → Nail Mask + Fungi Mask
    ↓
[OSI Grid Analysis]
    ├─ Detect nail contour
    ├─ Create 4x5 grid
    ├─ Analyze infection percentage
    └─ Determine proximity level
    ↓
[Calculate OSI Score]
    ├─ Area Score
    ├─ Proximity Score
    ├─ Total Score (A × P)
    └─ Severity Class
    ↓
[Draw Grid Visualization]
    ├─ Green grid lines
    ├─ Red overlay for affected areas
    └─ Store grid coordinates
    ↓
Result Display with OSI Score & Severity
```

## Output Structure

When `process_nail_for_grading()` completes, it returns:

```python
{
    "osi_score": {
        "area_score": 3,                    # 0-5
        "proximity_score": 3,               # 1-5
        "total_osi_score": 9,               # 0-25
        "severity": "Moderate",             # Classification
        "area_percent": 35.5,               # Infection %
        "proximity_level": 3                # 1-5
    },
    "grid_analysis": {
        "area_percent": 35.5,
        "proximity_level": 3,
        "total_nail_area_px": 15000,
        "affected_area_px": 5325
    },
    "grid_visualization": <numpy_array>,    # Image with grid overlay
    "grid_coordinates": [
        [((x1,y1), (x2,y2)), ...],          # 4x5 grid cells
        ...
    ],
    "nail_bbox": (x, y, w, h)               # Nail bounding box
}
```

## Usage Examples

### Example 1: Get OSI Score Only
```python
from analysis.osi_grading import get_osi_score

result = get_osi_score(area_percent=40, proximity_level=3)
print(f"Score: {result['total_osi_score']}/25")
print(f"Severity: {result['severity']}")
# Output: Score: 9/25
#         Severity: Moderate
```

### Example 2: Process Nail with Grid Visualization
```python
from analysis.osi_grading import process_nail_for_grading
import cv2

# Assuming you have:
# - cropped_nail: preprocessed nail image
# - nail_mask: binary segmentation mask for nail
# - affected_mask: binary segmentation mask for infection

result = process_nail_for_grading(cropped_nail, nail_mask, affected_mask)

# Display result
cv2.imshow("Grid Visualization", result["grid_visualization"])

# Access scores
print(f"OSI: {result['osi_score']['total_osi_score']}")
print(f"Severity: {result['osi_score']['severity']}")
```

### Example 3: Access Grid Coordinates
```python
result = process_nail_for_grading(cropped_nail, nail_mask, affected_mask)

grid = result["grid_coordinates"]
# grid[row][col] = ((x1, y1), (x2, y2))  # Rectangle coordinates

# Access top-left cell
top_left_cell = grid[0][0]
print(f"Top-left cell: {top_left_cell}")
```

## Grid Layout

The 4x5 grid divides the nail into regions:
- **4 Columns**: Horizontal nail sections (lateral-to-lateral)
- **5 Rows**: Vertical nail sections (distal-to-proximal)

```
Distal (Tip)
┌─────┬─────┬─────┬─────┐
│     │     │     │     │ Row 0
├─────┼─────┼─────┼─────┤
│     │     │     │     │ Row 1
├─────┼─────┼─────┼─────┤
│     │     │     │     │ Row 2
├─────┼─────┼─────┼─────┤
│     │     │     │     │ Row 3
├─────┼─────┼─────┼─────┤
│     │     │     │     │ Row 4
└─────┴─────┴─────┴─────┘
Proximal (Base/Matrix)
```

## UI Visual Feedback

### Result Card Elements
```
┌─────────────────────────┐
│   [Grid Image Display]  │  ← Shows nail with 4x5 grid overlay
│      (160×160)          │     Red areas = infection, Green = grid lines
├─────────────────────────┤
│ #1 | 0.95 (Confidence) │
├─────────────────────────┤
│  OSI: 9/25              │  ← Color coded by severity
│  Moderate               │
│ Area: 35.5%             │
├─────────────────────────┤
│ Classes: nail, fungi    │
└─────────────────────────┘
```

## Integration Checklist

- ✅ OSI grading module created (`analysis/osi_grading.py`)
- ✅ Scan pipeline updated to calculate OSI scores
- ✅ Result UI enhanced with OSI display
- ✅ Grid visualization rendered with infection highlights
- ✅ Severity color-coding implemented
- ✅ Console logging for debugging

## Next Steps

To further enhance the system:

1. **Database Integration**: Store OSI scores in database with scan results
2. **Report Generation**: Include OSI scores in patient reports
3. **Trend Analysis**: Track OSI changes over time for same patient
4. **Customization**: Adjust grid cell analysis weights
5. **Export**: Export images with grid overlay for medical records

## Troubleshooting

### No Grid Appears
- Check that segmentation masks are properly generated
- Verify nail contour detection returns valid coordinates
- Ensure masks have sufficient non-zero values (>127)

### OSI Score Is 0
- Verify affected_mask contains infection data
- Check mask binary thresholding (should be 0-255)
- Ensure proximity level is being calculated correctly

### Grid Display Issues
- Verify nail_bbox coordinates are within image bounds
- Check grid cell coordinate calculations
- Ensure display image is in BGR format for OpenCV

## References

- **OSI Index Paper**: Commonly used in dermatology for onychomycosis severity assessment
- **Grid-based Analysis**: Standardized for consistent severity grading across patients
- **Color Coding**: Medical standard (Red = affected, Green = healthy)
