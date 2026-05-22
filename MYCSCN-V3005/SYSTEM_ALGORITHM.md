# MycoScan System Algorithm Flow

## High-Level Overview

MycoScan is a complete automated toenail fungus detection and treatment system. It captures toenail images, analyzes them using deep learning models, grades the severity of infection, and applies topical medication via robotic servo control.

### Main Processing Pipeline
```
User Launches App → Select Input Source → Capture/Upload Images → 
Detection & Segmentation → OSI Grading → Display Results → 
Apply Medication (Optional) → Save to Database → History View
```

---

## 1. Application Launch & UI Navigation

### Entry Point: `main.py`

```
main()
  ├─ Create QApplication (PyQt5)
  ├─ Load Base Stylesheet (BASE_QSS)
  ├─ Show Splash Screen (900ms delay)
  ├─ Create AppWindow with 5 Stack Pages:
  │  ├─ Page 0: LandingPage (Start Scan / View History buttons)
  │  ├─ Page 1: ScanPage (Camera capture & analysis)
  │  ├─ Page 2: HistoryPage (View past scans)
  │  ├─ Page 3: ScanDetailView (Detailed view of single scan)
  │  └─ Page 4: ServoControlView (Apply medication via servos)
  ├─ Initialize Keyboard Manager (onscreen keyboard)
  └─ Show Main Window
```

### Page Navigation via `router.py`
- Route enum controls which page is displayed
- `goto(stack, Route)` switches pages instantly
- Back button always available (floating, top-left)

---

## 2. Scan Initialization: `ui/scan/scan_page.py`

### Flow When User Taps "Start Scan"

```
ScanPage.showEvent()
  ├─ Stop previous camera if running
  ├─ Reset capture state
  ├─ Load Detection Model (best_tn.pt - YOLO)
  ├─ Load Segmentation Model (best.pt - YOLO)
  ├─ Show CameraView (fullscreen camera preview)
  └─ Start live camera feed
```

### Internal Stack Pages
```
ScanPage contains 4 sub-pages:
├─ Page 0: SourceSelection (Choose: Capture or Upload)
├─ Page 1: CameraView (Live preview + capture buttons)
├─ Page 2: UploadView (File selector for pre-recorded images)
└─ Page 3: ResultView (Severity grades + recommendations)
```

---

## 3. Image Acquisition

### Option A: Camera Capture (Default) - `ui/scan/camera_view.py`

```
CameraView.start_camera()
  ├─ Initialize Picamera2 (Raspberry Pi camera)
  ├─ Set resolution to high quality
  ├─ Start QTimer (60 FPS update loop)
  └─ Display live preview in QLabel

User Interaction:
├─ TAP on preview → Autofocus on that point
├─ HOLD (>500ms) on preview → Capture current frame
└─ Display "Capturing: [Left/Right] Foot" status

Dual-Foot Workflow:
├─ First capture → Saves to captured_images[foot_id]
├─ Status changes to next foot (Right ↔ Left)
├─ Second capture → Both feet captured
└─ on_both_captured() callback triggers → Process images
```

### Option B: File Upload - `ui/scan/upload_view.py`

```
UploadView.on_select_left() / on_select_right()
  ├─ Open QFileDialog (file browser)
  ├─ User selects image (.jpg, .png, etc.)
  ├─ Read image via cv2.imread()
  ├─ Display thumbnail preview
  ├─ Enable "PROCESS" button when both feet selected
  └─ on_images_ready() → Process images

Note: Both paths merge at on_images_ready(images_dict)
```

---

## 4. Image Processing Pipeline: Detection & Segmentation

### Called After Images Ready: `ui/scan/scan_page.py`

```
ScanPage.on_images_ready(images_dict)
  └─ For each foot image [RIGHT=0, LEFT=1]:
       ├─ Step 1: DETECTION (best_tn.pt)
       ├─ Step 2: SEGMENTATION (best.pt)
       ├─ Step 3: OSI GRADING
       └─ Step 4: SAVE RESULTS
```

---

### Step 1: Detection - `analysis/segmentation.py`

**Purpose:** Find and crop toenails from full foot image

```
ToenailDetector.detect(full_image)
  ├─ Run YOLO object detection model (best_tn.pt)
  ├─ Input: Full foot photo (any resolution)
  ├─ Model Output: Bounding boxes for each detected toenail
  │  └─ Returns: [(class, confidence, bbox), ...]
  └─ Return: List of detections

Detection Result Structure:
{
  "class": "toenail",           # Class name
  "confidence": 0.92,           # Detection confidence
  "bbox": (x1, y1, x2, y2)     # Pixel coordinates
}
```

**Processing:**
```
crop_detections(full_image, detections, padding=50)
  ├─ For each detection bbox
  ├─ Add padding (50px) around bbox
  ├─ Extract cropped region (~512x512)
  └─ Return: [cropped_nail_1, cropped_nail_2, ...]
```

---

### Step 2: Segmentation - `analysis/segmentation.py`

**Purpose:** Identify healthy nail vs. infected (fungal) areas

```
NailSegmentation.segment(cropped_nail_image)
  ├─ Run YOLO segmentation model (best.pt) on cropped nail
  ├─ Input: Single toenail image (~512x512)
  ├─ Model Output: Pixel-level masks for each class
  │  ├─ Class 0: "nail" (healthy toenail)
  │  ├─ Class 1: "fungi" (infected area - IMPORTANT)
  │  └─ Class 2: "toe" (surrounding skin)
  │
  └─ Return: [{
       "class": "fungi",
       "confidence": 0.85,
       "bbox": (x, y, w, h),
       "mask": binary_mask_array  # Pixel-level segmentation
     }, ...]
```

**Key Output:** Binary mask where 1 = infected, 0 = healthy/background

---

### Extract Affected Area

```
get_affected_mask_and_bbox(segmentation_results)
  ├─ Filter masks where class == "fungi"
  ├─ Combine all fungal masks (OR operation)
  ├─ Calculate bounding box of affected region
  └─ Return: (affected_mask, bbox)

Affected Area Calculation:
├─ Total affected pixels = sum(affected_mask)
├─ Nail area = sum(nail_mask)
├─ Infection percentage = (affected_pixels / nail_pixels) × 100%
└─ Used for severity grading
```

---

## 5. OSI Grading: Severity Assessment

### Called After Segmentation: `analysis/osi_grading.py`

```
process_nail_for_grading(cropped_nail, segmentation_results)
  ├─ Extract affected mask
  ├─ Get nail contour (largest contour in nail mask)
  ├─ Create 4×5 grid overlay on nail area
  ├─ Analyze each grid cell for infection
  └─ Calculate OSI score

OSI = Onychomycosis Severity Index
```

---

### Grid Analysis

```
OSIGridAnalyzer.create_grid_overlay(nail_bbox)
  ├─ Divide nail into 4 columns × 5 rows = 20 cells
  ├─ Grid Layout:
  │  ┌──┬──┬──┬──┐
  │  │  │  │  │  │  ← Nail top (lunula area)
  │  ├──┼──┼──┼──┤
  │  │  │  │  │  │
  │  ├──┼──┼──┼──┤
  │  │  │  │  │  │
  │  ├──┼──┼──┼──┤
  │  │  │  │  │  │
  │  ├──┼──┼──┼──┤
  │  │  │  │  │  │  ← Nail bottom (free edge)
  │  └──┴──┴──┴──┘
  │
  └─ Cell coordinates: [(x1, y1), (x2, y2)]
```

---

### Cell Infection Analysis

```
OSIGridAnalyzer.analyze_grid_cells(nail_mask, affected_mask, grid)
  ├─ For each of 20 grid cells:
  │  ├─ Count pixels in nail
  │  ├─ Count infected pixels
  │  ├─ Calculate % infection in cell
  │  ├─ Determine if "involved" (threshold = 10%)
  │  └─ Calculate proximity score (favor distal = free edge)
  │
  └─ Aggregate statistics:
     ├─ Total involved cells
     ├─ Total nail area involvement (%)
     └─ Proximity weighting (distal more severe)
```

---

### OSI Score Calculation

```
get_osi_score(nail_image, segmentation_results) → severity_text

Formula combines:
├─ Nail area involvement (%)
│  ├─ 0%: "Clinically Cured / No involvement"
│  ├─ 1-10%: "Mild"
│  ├─ 11-50%: "Moderate"
│  └─ >50%: "Severe"
│
├─ Distal involvement (free edge = more severe)
├─ Proximal involvement (nail bed = less severe)
└─ Grid cell analysis (20-point system)

Final Output: One of 4 severity grades
```

---

## 6. Result Display: `ui/scan/result_view.py`

### ResultView Population

```
ResultView.display_results(nail_images, segmentation_results, scores)
  │
  └─ For each foot (Left + Right):
       ├─ Section 1: Original Image
       │  └─ Show captured/uploaded photo
       │
       ├─ Section 2: Segmentation Visualization
       │  ├─ Show detected toenails
       │  ├─ Overlay affected areas (green/yellow/red)
       │  ├─ Draw 4×5 grid on nail
       │  └─ Highlight infected cells
       │
       ├─ Section 3: OSI Score
       │  ├─ Display severity badge:
       │  │  ├─ "Clinically Cured / No involvement" (Green)
       │  │  ├─ "Mild" (Yellow)
       │  │  ├─ "Moderate" (Orange)
       │  │  └─ "Severe" (Red)
       │  │
       │  └─ Show percentage: X% of nail involved
       │
       ├─ Section 4: Treatment Recommendations
       │  ├─ Based on severity grade
       │  ├─ Collapsible details
       │  └─ Links to medications/specialists
       │
       └─ Buttons:
          ├─ "NEW SCAN" (reset & start over)
          ├─ "APPLY MEDICATION" (if eligible)
          └─ "SAVE" (optional, save to database)
```

### Recommendation Mapping

```
Severity → Recommendation
├─ "Clinically Cured": No treatment needed
├─ "Mild": Topical antifungals (48 weeks max)
│  └─ Efinaconazole 10%, Tavaborole 5%, Ciclopirox lacquer
├─ "Moderate": Oral + topical (requires dermatologist)
│  └─ Oral terbinafine (250mg × 12 weeks)
└─ "Severe": Aggressive treatment required
   └─ Combination oral/topical + possible nail removal
```

---

## 7. Medication Application: `ui/scan/servo_control_view.py`

### ServoControlView Pipeline

```
User Taps "APPLY MEDICATION" → ServoControlView

ServoControlView.showEvent()
  ├─ Initialize Picamera2 (camera for application verification)
  ├─ Initialize Serial Connection (to Arduino)
  ├─ Display servo selection interface
  └─ Start camera preview (document medication application)

Servo Port Mapping:
└─ Arduino sequencing order: [5, 4, 3, 2, 1, 10, 9, 8, 7, 6]
   ├─ Servos 5, 4, 3, 2, 1 → LEFT FOOT
   └─ Servos 10, 9, 8, 7, 6 → RIGHT FOOT
```

---

### User Interaction Flow

```
Step 1: Select Target Servos
  ├─ Display 10 servo checkboxes
  │  ├─ Top row: Servos for LEFT FOOT (5, 4, 3, 2, 1)
  │  ├─ Middle: "NEXT" button to switch feet
  │  └─ Bottom row: Servos for RIGHT FOOT (10, 9, 8, 7, 6)
  │
  ├─ User checks affected toenail(s)
  └─ User taps "NEXT" → Shows right foot servos

Step 2: Apply Medication
  ├─ User applies topical medication to selected servos/nails
  ├─ Camera preview shows documentation
  ├─ Taps "APPLY" button → Confirmation dialog
  │
  └─ Step 3: Send Commands to Arduino
     ├─ For each selected servo:
     │  ├─ Send: "ServoN" command via Serial
     │  ├─ Arduino activates servo N (applies applicator)
     │  ├─ Wait for confirmation
     │  └─ Move to next servo
     │
     ├─ After all servos: "CONFIRM" button
     └─ Step 4: Sequence Done
        ├─ Display completion message
        ├─ Save medication record to database
        └─ Return to scan results OR start new scan
```

---

### Serial Communication Protocol

```
Host (MycoScan) → Arduino Serial Port

Command Format:
├─ "Servo5" → Activate servo 5 (LEFT foot, pinky toe)
├─ "Servo4" → Activate servo 4 (LEFT foot)
├─ ...
├─ "Servo10" → Activate servo 10 (RIGHT foot, pinky toe)
└─ "Servo6" → Activate servo 6 (RIGHT foot, big toe)

Arduino Response:
├─ "OK" → Command received, servo activated
└─ "ERROR" → Communication failure

Sequence Execution:
└─ Run in port_map order for consistency:
   [5, 4, 3, 2, 1] skip unselected, then [10, 9, 8, 7, 6] skip unselected
```

---

## 8. Database Storage: `database/db.py`

### Data Persistence

```
Database.add_scan(patient_name, severity, captured_path, segmented_path)
  ├─ Create SQLite database if doesn't exist
  ├─ INSERT INTO scans table:
  │  ├─ patient_name TEXT
  │  ├─ severity TEXT ("Mild", "Moderate", "Severe", etc.)
  │  ├─ recommended_action TEXT (treatment recommendations)
  │  ├─ captured_path TEXT (path to original image)
  │  ├─ segmented_path TEXT (path to visualization with grid/overlay)
  │  ├─ created_at TIMESTAMP (automatic)
  │  └─ id INTEGER PRIMARY KEY (auto-increment)
  │
  └─ Return: scan_id (for future reference)

File Storage:
└─ data/scans/
   ├─ [PatientName]/
   │  ├─ [scan_id]_original.jpg (captured photo)
   │  ├─ [scan_id]_segmented.png (with overlay)
   │  └─ ...
   └─ mycoscan.db (SQLite database)
```

---

## 9. History & Playback: `ui/history/`

### HistoryPageV2 Display

```
HistoryPageV2.load_from_database()
  ├─ Query Database.list_scans() → get all records
  ├─ Sort by created_at DESC (newest first)
  │
  └─ Display as scrollable list:
     ├─ For each scan:
     │  ├─ Thumbnail of segmented image
     │  ├─ Patient name
     │  ├─ Severity badge
     │  ├─ Date/time
     │  └─ Tap to view details

User Taps on Scan
  └─ ScanDetailView loads:
     ├─ Full resolution images
     ├─ OSI scores + grid visualization
     ├─ Treatment recommendations
     └─ Medication history (if applied)
```

---

## 10. Complete User Journey: End-to-End

```
┌─────────────────────────────────────────────────────────────┐
│ USER OPENS APP                                              │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
        ┌─────────────────────────────────┐
        │ Landing Page (2 Buttons)        │
        │ [START SCAN] [VIEW HISTORY]     │
        └────┬──────────────────┬─────────┘
             │                  │
    ┌────────▼─┐      ┌────────▼─┐
    │ SCAN PATH │      │ HISTORY  │
    └────────┬─┘      │ PLAYBACK │
             │         └──────────┘
             ▼
    ┌──────────────────┐
    │ Select Source    │
    │ [Capture|Upload] │
    └────────┬─────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
    CAMERA       FILE SELECTOR
    (Live)       (Pre-recorded)
      │             │
      ├─ Capture Left Foot ──────┐
      ├─ Capture Right Foot ─────┤
      │                           │
      └───────────────┬───────────┘
                      ▼
         ┌─────────────────────────┐
         │ YOLO Detection Model    │ (best_tn.pt)
         │ (Find toenails)         │
         └────────┬────────────────┘
                  ▼
         ┌─────────────────────────┐
         │ YOLO Segmentation Model │ (best.pt)
         │ (Healthy vs Infected)   │
         └────────┬────────────────┘
                  ▼
         ┌─────────────────────────┐
         │ OSI Grid Analysis       │
         │ (4×5 grid scoring)      │
         └────────┬────────────────┘
                  ▼
    ┌────────────────────────────────┐
    │ Result View                     │
    │ - Original images              │
    │ - Segmentation overlays        │
    │ - OSI severity grades          │
    │ - Treatment recommendations    │
    │ Buttons: [NEW] [APPLY] [SAVE]  │
    └────────┬──────────┬────────────┘
             │          │
    ┌────────▼──┐   ┌───▼──────────┐
    │ NEW SCAN  │   │ APPLY        │
    │ (Loop)    │   │ MEDICATION   │
    │           │   │              │
    └───────────┘   └───┬──────────┘
                        ▼
            ┌───────────────────────┐
            │ Servo Control View     │
            │ - Select nails        │
            │ - Live camera (doc)   │
            │ - Send to Arduino     │
            └───┬─────────────┬─────┘
                │             │
        ┌───────▼─────────────▼──┐
        │ [APPLY] [CONFIRM]      │
        └───────┬──────┬─────────┘
                │      │
        ┌───────▼──┐  ┌▼────────────────┐
        │ Save to  │  │ Return to       │
        │ Database │  │ Landing         │
        └──────────┘  └─────────────────┘
```

---

## 11. Key Parameters & Constants

### Detection & Segmentation
```
Detection Model:    best_tn.pt (YOLO v8 format)
  ├─ Input: Full foot image
  ├─ Output: Toenail detections
  └─ Confidence threshold: >0.5 typically

Segmentation Model: best.pt (YOLO v8 format)
  ├─ Input: Cropped nail (~512x512)
  ├─ Classes: nail, fungi, toe
  └─ Output: Pixel-level masks

Crop Padding:       50 pixels (around detection bbox)
```

### OSI Grading
```
Grid Dimensions:    4 columns × 5 rows = 20 cells
Cell Infection:     10% threshold to mark "involved"
Severity Thresholds:
  ├─ 0%: Clinically Cured
  ├─ 1-10%: Mild
  ├─ 11-50%: Moderate
  └─ >50%: Severe
```

### Servo Control
```
Port Map Order:     [5, 4, 3, 2, 1, 10, 9, 8, 7, 6]
Left Foot Servos:   [5, 4, 3, 2, 1] (pinky to big toe)
Right Foot Servos:  [10, 9, 8, 7, 6] (pinky to big toe)
Serial Baud:        9600 (typical Arduino)
```

---

## 12. Error Handling & Recovery

```
Common Failure Points:

1. Camera Initialization Fails
   ├─ Fallback to upload mode
   └─ Show error message + allow file selection

2. Model Loading Fails
   ├─ Check model files exist (best.pt, best_tn.pt)
   ├─ Verify YOLO package installed
   └─ Graceful error UI

3. Serial Connection Fails
   ├─ Skip servo control
   ├─ Allow scan completion
   └─ Disable "APPLY MEDICATION" button

4. Database Corruption
   ├─ Auto-backup database
   ├─ Recreate schema if needed
   └─ Preserve scan history

5. Image Processing Errors
   ├─ Retry with lower resolution
   ├─ Use default severity "Unknown"
   └─ Save original image anyway
```

---

## 13. Performance Considerations

### Processing Time Breakdown
```
Detection:      ~500ms (YOLO inference)
Segmentation:   ~800ms (YOLO inference per nail, ×2 feet)
OSI Grading:    ~100ms (grid analysis)
Grid Rendering: ~50ms (visualization overlay)
─────────────────────────────────────
Total:          ~1.5-2 seconds per scan
```

### Memory Usage
```
Live Camera Stream:  ~50-100MB (buffered frames)
YOLO Models Loaded:  ~400-600MB (both models in RAM)
Database:            ~10-50MB (depends on scan count)
GUI/UI Elements:     ~100-200MB (PyQt5 overhead)
─────────────────────────────────────
Typical Total:       ~600-1000MB

Raspberry Pi 4 (4GB)  ✓ Sufficient
Raspberry Pi Zero     ✗ Insufficient
```

---

## Summary

MycoScan is a **fully-integrated clinical toenail analysis system** that:

1. **Acquires images** via camera or file upload (dual-foot workflow)
2. **Detects toenails** using YOLO object detection
3. **Segments** infected vs. healthy areas using YOLO instance segmentation
4. **Grades severity** using Onychomycosis Severity Index (OSI) with 4×5 grid analysis
5. **Displays results** with visualizations and treatment recommendations
6. **Applies medication** via robotic servo control (optional)
7. **Stores records** in SQLite database for historical tracking
8. **Retrieves history** with full playback and patient tracking

The entire pipeline is designed to be **rapid** (<2s analysis), **accurate** (deep learning-based), and **clinically actionable** (severity grades + treatment options).

