# OSI Grid Visualization Guide

## 4×5 Grid Layout

The nail is divided into a standardized 4 columns × 5 rows grid for consistent severity assessment.

### Grid Positioning

```
                    NAIL SURFACE
            (viewed from dorsal side)

      Lateral ←       Nail       → Medial
              ←                  →

Distal
(Tip)  ┌────┬────┬────┬────┐
       │ 00 │ 01 │ 02 │ 03 │  Row 0 (Distal quarter)
       ├────┼────┼────┼────┤
       │ 10 │ 11 │ 12 │ 13 │  Row 1 (2nd quarter)
       ├────┼────┼────┼────┤
       │ 20 │ 21 │ 22 │ 23 │  Row 2 (3rd quarter)
       ├────┼────┼────┼────┤
       │ 30 │ 31 │ 32 │ 33 │  Row 3 (4th quarter)
       ├────┼────┼────┼────┤
       │ 40 │ 41 │ 42 │ 43 │  Row 4 (Matrix/Lunula)
Proximal
(Base)  └────┴────┴────┴────┘
```

### Grid Reference

- **Rows**: 0-4 (Distal to Proximal)
  - Row 0: Distal quarter
  - Row 1: 2nd quarter  
  - Row 2: 3rd quarter
  - Row 3: Proximal quarter
  - Row 4: Matrix/Lunula area

- **Columns**: 0-3 (Lateral to Medial)
  - Col 0: Lateral edge
  - Col 1: Lateral-center
  - Col 2: Medial-center
  - Col 3: Medial edge

## Visualization in MycoScan

### Result Card Display

```
┌──────────────────────────────┐
│                              │
│     GRID VISUALIZATION       │
│     (160×160 pixels)         │
│                              │
│  ┌────┬────┬────┬────┐       │
│  │   │   │████│    │   Row 0  │
│  ├────┼────┼────┼────┤       │
│  │   │████│████│████│   Row 1  │
│  ├────┼────┼────┼────┤       │
│  │████│████│████│    │   Row 2  │
│  ├────┼────┼────┼────┤       │
│  │    │    │    │    │   Row 3  │
│  ├────┼────┼────┼────┤       │
│  │    │    │    │    │   Row 4  │
│  └────┴────┴────┴────┘       │
│                              │
│  Green lines = Grid          │
│  Red (████) = Infected       │
│  White = Healthy nail        │
├──────────────────────────────┤
│ #1 | 0.95                   │
├──────────────────────────────┤
│ OSI: 10/25                  │
│ Moderate                    │
│ Area: 37.5%                 │
├──────────────────────────────┤
│ Classes: nail, fungi        │
└──────────────────────────────┘
```

## Color Scheme

### Grid Elements
- **Grid lines**: Green (0, 255, 0) in BGR
- **Infected areas**: Red overlay (0, 0, 255) in BGR
- **Healthy nail**: White background

### Severity Colors (Result Card)

```
┌────────────────┬──────────────┬──────────────────────┐
│ Score Range    │ Severity     │ Color                │
├────────────────┼──────────────┼──────────────────────┤
│ 0              │ Cured        │ Green (#22c55e)      │
│ 1-5            │ Mild         │ Blue (#3b82f6)       │
│ 6-15           │ Moderate     │ Amber (#f59e0b)      │
│ 16-25          │ Severe       │ Red (#ef4444)        │
└────────────────┴──────────────┴──────────────────────┘
```

## Infection Mapping Example

### Low Severity (Score 3)
```
      Col 0  Col 1  Col 2  Col 3
Row 0   [ ]    [ ]    [X]    [ ]   ← Minimal distal involvement
Row 1   [ ]    [ ]    [ ]    [ ]
Row 2   [ ]    [ ]    [ ]    [ ]
Row 3   [ ]    [ ]    [ ]    [ ]
Row 4   [ ]    [ ]    [ ]    [ ]

Area: 8% | Proximity: 1 (Distal)
Score = 1 × 1 = 1 (Mild)
```

### Medium Severity (Score 9)
```
      Col 0  Col 1  Col 2  Col 3
Row 0   [X]    [X]    [X]    [X]   ← 40% infected
Row 1   [X]    [X]    [X]    [X]   ← reaches 3rd quarter
Row 2   [X]    [X]    [X]    [X]
Row 3   [ ]    [ ]    [ ]    [ ]
Row 4   [ ]    [ ]    [ ]    [ ]

Area: 40% | Proximity: 3 (3rd quarter)
Score = 3 × 3 = 9 (Moderate)
```

### High Severity (Score 20)
```
      Col 0  Col 1  Col 2  Col 3
Row 0   [X]    [X]    [X]    [X]   ← 80% infected
Row 1   [X]    [X]    [X]    [X]
Row 2   [X]    [X]    [X]    [X]
Row 3   [X]    [X]    [X]    [X]   ← reaches proximal
Row 4   [ ]    [ ]    [ ]    [ ]

Area: 80% | Proximity: 4 (Proximal quarter)
Score = 5 × 4 = 20 (Severe)
```

### Matrix Involvement (Score 15)
```
      Col 0  Col 1  Col 2  Col 3
Row 0   [ ]    [ ]    [ ]    [ ]
Row 1   [ ]    [ ]    [ ]    [ ]
Row 2   [ ]    [ ]    [ ]    [ ]
Row 3   [ ]    [ ]    [ ]    [ ]
Row 4   [X]    [X]    [X]    [X]   ← Matrix/lunula infected

Area: 30% | Proximity: 5 (Matrix)
Score = 3 × 5 = 15 (Moderate)
Note: Even small matrix involvement is significant!
```

## Grid Analysis Process

### Step 1: Nail Detection
```
Original Image → YOLO Detection → Nail Boundaries
        ↓
   Detected nail region
```

### Step 2: Create Grid
```
Nail Bounding Box (x, y, w, h)
        ↓
Divide into 4×5 cells
        ↓
Calculate cell coordinates
```

### Step 3: Analyze Infection
```
For each cell:
- Count pixels in nail mask
- Count pixels in infection mask
- Calculate infection percentage
        ↓
Total infection across all cells
```

### Step 4: Determine Proximity
```
Find topmost infected cell
        ↓
Map to proximity level (1-5)
        ↓
Assign proximity score
```

### Step 5: Calculate OSI
```
Area Score × Proximity Score = OSI Score (0-25)
```

## Example: Processing Workflow

### Input Image
```
Captured nail photo with visible fungi
Dimensions: 512×512 pixels
```

### Detection → Contour
```
YOLO detection → Nail region
Nail bbox: (100, 80, 310, 350)  [x, y, width, height]
```

### Grid Creation
```
Cell width = 310 / 4 = 77.5 px
Cell height = 350 / 5 = 70 px

Grid coordinates:
[0,0] = ((100, 80), (177.5, 150))
[0,1] = ((177.5, 80), (255, 150))
... and so on for all 20 cells (4×5)
```

### Infection Analysis
```
Segmentation masks:
- Nail mask: All pixels inside nail region = 255
- Fungi mask: Only infected pixels = 255

Per cell analysis:
- Cells in rows 0-1: 50 infected pixels out of 150 total
- Cells in rows 2-4: 0 infected pixels

Total: 250 infected / 10,850 total = 2.3% area ✗
```

*Note: In real scenarios with visible infection:*
```
Total: 3500 infected / 8750 total = 40% area ✓
Topmost infection at row 1: Proximity = 2
OSI = 3 × 2 = 6 (Moderate)
```

### Visualization Output
```
4×5 grid overlay with:
- Green lines separating cells
- Red pixels showing infected cells
- White background for healthy areas
```

## Clinical Interpretation

### From Grid Visualization, You Can:

1. **Identify infection pattern**
   - Focal vs. diffuse
   - Lateral vs. medial involvement
   - Proximal spread risk

2. **Assess treatment zone**
   - Which cells need topical therapy
   - Risk of systemic involvement

3. **Track progression**
   - Compare grid positions over time
   - Assess treatment response

4. **Make clinical decisions**
   - Topical vs. systemic therapy
   - Treatment intensity
   - Follow-up frequency

## Measurement Accuracy

### Grid-Based Advantages
✅ Standardized regions for consistent measurement
✅ Reduces observer bias
✅ Enables objective tracking
✅ Facilitates inter-observer agreement
✅ Supports automated analysis

### Precision Levels
- **Area calculation**: Pixel-level accuracy
- **Proximity detection**: Cell-level accuracy  
- **Score consistency**: Standardized formula

## Integration with Reports

Grid visualization can be included in:
- Patient reports with infected cell map
- Progress tracking across visits
- Treatment efficacy documentation
- Medical record archives

---

**Key Point**: The 4×5 grid provides a standardized framework that ensures consistent, reproducible nail assessment across different patients and time points.
