# MycoScan v3.005 - Deep Learning Toenail Analysis System

## Overview

MycoScan is a PyQt5-based GUI application for detecting and grading onychomycosis (fungal toenail infections) using deep learning models. It combines YOLO-based detection/segmentation with OSI (Onychomycosis Severity Index) grading and robotic medication application via servo control.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Application Pipeline](#application-pipeline)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Installation & Setup](#installation--setup)
7. [Usage Guide](#usage-guide)
8. [Database Schema](#database-schema)
9. [Troubleshooting](#troubleshooting)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        MycoScan Application                      │
│                    (PyQt5 GUI - main.py)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌──────────────┐  ┌──────────┐  ┌───────────┐
        │  Landing     │  │  Scan    │  │  History  │
        │  Page        │  │  Page    │  │  Page     │
        └──────────────┘  └──────────┘  └───────────┘
                │              │
                │         ┌────┴────┐
                │         ▼         ▼
                │    ┌─────────┐  ┌──────────┐
                │    │ Camera  │  │ Upload   │
                │    │ Capture │  │ Images   │
                │    └─────────┘  └──────────┘
                │         │         │
                │         └────┬────┘
                │              ▼
                │         ┌──────────────┐
                │         │ Result View  │
                │         │ (OSI Grades) │
                │         └──────────────┘
                │              │
                │              ▼
                │         ┌────────────┐
                │         │ Servo      │
                │         │ Control    │
                │         │ (Medicate) │
                │         └────────────┘
                │
        ┌───────┴─────────┐
        ▼                 ▼
    ┌────────────┐   ┌──────────────┐
    │ ML Models  │   │  Database    │
    │ (YOLO)     │   │ (SQLite)     │
    └────────────┘   └──────────────┘
```

### Component Stack

```
UI Layer (PyQt5)
├── Landing Page (ui/landing.py)
├── Scan Page (ui/scan/scan_page.py)
│   ├── Camera View (ui/scan/camera_view.py)
│   ├── Upload View (ui/scan/upload_view.py)
│   ├── Result View (ui/scan/result_view.py)
│   └── Servo Control (ui/scan/servo_control_view.py)
├── History Page (ui/history/history_page_v2.py)
├── Scan Detail View (ui/history/scan_detail_view.py)
└── Widgets (widgets/)
    ├── Virtual Keyboard (widgets/virtual_keyboard.py)
    └── Touch Scroll (widgets/touchscroll.py)
        │
Analysis Layer (ML Pipeline)
├── Detection (analysis/segmentation.py)
│   └── ToenailDetector (YOLO - best_tn.pt)
├── Segmentation (analysis/segmentation.py)
│   └── NailSegmentation (YOLO - best.pt)
└── Grading (analysis/osi_grading.py)
    └── OSIGridAnalyzer & process_nail_for_grading()
        │
Data Layer (Persistence)
└── Database (database/)
    ├── db_manager_v2.py (Current - V2)
    ├── db_manager.py (Legacy - V1)
    └── db.py (Legacy - Old)
```

---

## Application Pipeline

### Complete End-to-End Workflow

```
START
  │
  ├─► LANDING PAGE (ui/landing.py)
  │   • "Start a Scan" → Go to SCAN PAGE
  │   • "View Previous Scans" → Go to HISTORY PAGE
  │
  ├─► SCAN PAGE (ui/scan/scan_page.py) [Main Scanner]
  │   │
  │   ├─► SOURCE SELECTION (ui/scan/source_selection.py)
  │   │   • Choose: "Capture Images" OR "Upload Images"
  │   │
  │   ├─► CAMERA CAPTURE (ui/scan/camera_view.py) [If Capture]
  │   │   • Tap to focus, Hold 1.5s to upload
  │   │   • Capture left foot → Capture right foot
  │   │   • Images stored in memory
  │   │
  │   ├─► IMAGE UPLOAD (ui/scan/upload_view.py) [If Upload]
  │   │   • Select left foot image (512x512 or larger)
  │   │   • Select right foot image
  │   │
  │   ├─► RESULT VIEW (ui/scan/result_view.py) [Processing]
  │   │   │
  │   │   ├─► [Step 1] DETECTION (ToenailDetector)
  │   │   │   • Input: Full foot image
  │   │   │   • Model: YOLO (best_tn.pt)
  │   │   │   • Output: ~10 toenail bounding boxes
  │   │   │   • Processing time: ~2-3 seconds
  │   │   │
  │   │   ├─► [Step 2] CROPPING (crop_detections)
  │   │   │   • Input: Full image + detection bboxes
  │   │   │   • Operation: Crop each nail with 10px padding
  │   │   │   • Output: ~10 cropped 512x512 images
  │   │   │
  │   │   ├─► [Step 3] SEGMENTATION (NailSegmentation)
  │   │   │   • Input: Each 512x512 cropped nail
  │   │   │   • Model: YOLO Segmentation (best.pt)
  │   │   │   • Output: Nail mask + Affected area mask
  │   │   │   • Processing time: ~30-50ms per nail
  │   │   │
  │   │   ├─► [Step 4] AFFECTED AREA EXTRACTION
  │   │   │   • Input: Segmentation masks
  │   │   │   • Operation: Extract fungal area bbox
  │   │   │   • Output: Affected region for analysis
  │   │   │
  │   │   ├─► [Step 5] OSI GRADING (OSIGridAnalyzer)
  │   │   │   • Input: Affected area + nail segmentation
  │   │   │   • Operation: Overlay 4×5 grid on nail
  │   │   │   • Calculations:
  │   │   │     - Area score: % of nail affected
  │   │   │     - Proximity score: Distance from cuticle
  │   │   │     - Total OSI: (Area + Proximity) * 5
  │   │   │   • Output: OSI Score (0-25)
  │   │   │   • Severity Level:
  │   │   │     - 0: Clinically Cured / No involvement
  │   │   │     - 1-6: Mild
  │   │   │     - 7-15: Moderate
  │   │   │     - 16-25: Severe
  │   │   │
  │   │   ├─► [Step 6] VISUALIZATION & RECOMMENDATIONS
  │   │   │   • Display toenail cards with:
  │   │   │     - Nail image + segmentation overlay
  │   │   │     - OSI score & severity badge
  │   │   │     - Collapsible recommendations
  │   │   │   • Enable "Apply Med" button if:
  │   │   │     - Left foot: ≥3 nails detected
  │   │   │     - Right foot: ≥3 nails detected
  │   │   │
  │   │   └─► SAVE SCAN TO DATABASE (database/db_manager_v2.py)
  │   │       • Patient name (user input)
  │   │       • Overall severity (max of all nails)
  │   │       • All images: detection viz, nail cards, etc.
  │   │       • Nail data: per-nail OSI scores & masks
  │   │
  │   └─► BUTTONS:
  │       • "New Scan" → Back to SOURCE SELECTION
  │       • "Apply Med" → Go to SERVO CONTROL
  │       • "← Back" → Return to LANDING
  │
  ├─► SERVO CONTROL (ui/scan/servo_control_view.py) [Medication]
  │   │
  │   ├─► DUAL-FOOT PIPELINE:
  │   │   • Left Foot (Servos 5,4,3,2,1)
  │   │   • Select nails to apply medication to
  │   │   • Click "NEXT"
  │   │   • Switch camera feed to right foot
  │   │   • Right Foot (Servos 10,9,8,7,6)
  │   │   • Select nails
  │   │
  │   ├─► SERVO EXECUTION:
  │   │   • Click "APPLY"
  │   │   • Confirmation dialog
  │   │   • For each selected servo:
  │   │     - Send command via serial (/dev/ttyUSB0)
  │   │     - Wait 2.2 seconds for application
  │   │   • Show "Medication Applied" dialog
  │   │
  │   └─► OPTIONS:
  │       • "Done" → Return to RESULT VIEW
  │       • "Apply Again" → Reset pipeline, repeat
  │
  ├─► HISTORY PAGE (ui/history/history_page_v2.py)
  │   • Display table of all previous scans
  │   • Click row → View SCAN DETAIL
  │   • Filter/search by patient name
  │
  ├─► SCAN DETAIL VIEW (ui/history/scan_detail_view.py)
  │   • Full details of previous scan
  │   • All nail images with OSI scores
  │   • Medical recommendations
  │
  └─► EXIT
      • Close application
```

---

## Project Structure

```
MycoScan/
├── README.md (this file)
├── main.py (🔴 Entry point - Application window)
├── router.py (Navigation between pages)
├── styles.py (Global CSS styles & colors)
├── keyboard_manager.py (On-screen keyboard integration)
│
├── best_tn.pt (YOLO Detection model - toenail detector)
├── best.pt (YOLO Segmentation model - nail/affected area)
│
├── ui/ (User Interface - PyQt5)
│   ├── landing.py (🔴 Landing page with Start/History buttons)
│   ├── history/
│   │   ├── history_page_v2.py (🔴 Table of previous scans)
│   │   ├── history_page.py (Legacy version)
│   │   ├── detail_page.py (Modal popup for scan details)
│   │   └── scan_detail_view.py (Full-page scan view)
│   └── scan/
│       ├── scan_page.py (🔴 Main controller for scan workflow)
│       ├── camera_view.py (Dual camera capture - left/right feet)
│       ├── upload_view.py (Upload images from file system)
│       ├── result_view.py (Display OSI results & recommendations)
│       ├── servo_control_view.py (🔴 Robotic medication applicator)
│       └── source_selection.py (Choose capture vs upload)
│
├── widgets/
│   ├── splash.py (Startup splash screen)
│   ├── touchscroll.py (Touch-friendly scrolling)
│   ├── virtual_keyboard.py (On-screen keyboard)
│   └── __pycache__/
│
├── analysis/ (Machine Learning Pipeline)
│   ├── segmentation.py (🔴 Detection, Cropping, Segmentation)
│   │   ├── ToenailDetector (best_tn.pt)
│   │   ├── NailSegmentation (best.pt)
│   │   └── Helper functions
│   └── osi_grading.py (🔴 OSI Calculation & Grid Analysis)
│       ├── OSIGridAnalyzer
│       └── process_nail_for_grading()
│
├── database/ (Data Persistence)
│   ├── db_manager_v2.py (🔴 Current database - RECOMMENDED)
│   ├── db_manager.py (Legacy - V1)
│   ├── db.py (Legacy - Old)
│   └── mycoscan.db (SQLite database file)
│
├── data/ (Sample data & scans)
│   └── scans/
│       └── [Patient folders with images]
│
└── [Support files]
    ├── test_grading.py (Debug/test OSI grading)
    ├── omsim.py (Camera simulator/tester)
    ├── servocheck.py (Servo tester)
    ├── pluh.py (YOLO model viewer)
    ├── launch_app.sh (Startup script)
    └── __pycache__/

🔴 = Critical files for understanding the app
```

---

## Core Components

### 1. **Main Application (main.py)**

Entry point that sets up the QMainWindow with stacked pages.

```python
AppWindow
├── page_landing (LandingPage)
├── page_scan (ScanPage)
├── page_history (HistoryPageV2)
├── page_scan_detail (ScanDetailView)
└── page_servo_control (ServoControlView)
```

**Key Methods:**
- `_show_scan_details(patient_id)` - Load and display scan from history
- `_return_to_scan_results()` - Return from medication application

---

### 2. **Scan Page Controller (ui/scan/scan_page.py)**

Central orchestrator for the entire scanning workflow. Manages:
- Image capture/upload
- Detection & segmentation
- OSI grading
- Database saving

**Key Methods:**

```python
def on_images_ready(left_image, right_image, source):
    """Main processing pipeline"""
    → _process_foot_image() [2 calls - left & right]
    → _calculate_osi_for_nail() [~10 calls per foot]
    → result_view.show_results()

def _process_foot_image(img_bgr, foot_name):
    """Single foot processing pipeline:
    1. Detection (ToenailDetector.detect)
    2. Cropping (crop_detections)
    3. Segmentation (NailSegmentation.segment)
    4. OSI Grading (process_nail_for_grading)
    5. Visualization
    """

def _calculate_osi_for_nail(nail_img, nail_mask, affected_mask, nail_bbox, foot_name, nail_idx):
    """Calculate OSI score for single nail"""
```

---

### 3. **Detection & Segmentation (analysis/segmentation.py)**

**ToenailDetector** (YOLO Detection - best_tn.pt)
- Input: Full foot image (variable size)
- Output: ~10 detection bboxes with confidence scores
- Speed: ~2-3 seconds per image

**NailSegmentation** (YOLO Segmentation - best.pt)
- Input: 512x512 cropped nail image
- Output: Nail mask + Affected area mask
- Speed: ~30-50ms per image

**Helper Functions:**
```python
crop_detections(img, detections, padding=10, resize_to=512)
  → Crops each detection bbox → resizes to 512x512

get_affected_mask_and_bbox(seg_results)
  → Extracts fungal area mask & bounding box

visualize_affected_area_only(img, seg_results)
  → Creates visualization overlay of affected areas
```

---

### 4. **OSI Grading (analysis/osi_grading.py)**

**OSI Score Calculation Algorithm:**

```
Step 1: Create 4×5 Grid overlay on nail (20 cells)

Step 2: Count affected cells:
   area_score = (affected_pixels / total_nail_pixels) * 100
   If area_score < 25%: area_score_val = 1
   Else if < 50%: area_score_val = 2
   Else if < 75%: area_score_val = 3
   Else: area_score_val = 4

Step 3: Determine proximity (distance from cuticle):
   Cells in top 1/3 of nail (closest to cuticle): proximity_score = 4
   Cells in mid 1/3: proximity_score = 3
   Cells in bottom 1/3: proximity_score = 1

Step 4: Calculate total OSI:
   total_osi_score = (area_score_val + proximity_score) * 5
   Range: 0-25

Step 5: Map to severity:
   0: Clinically Cured / No involvement
   1-6: Mild
   7-15: Moderate
   16-25: Severe
```

**Key Functions:**
```python
def process_nail_for_grading(nail_img, nail_mask, affected_mask, nail_bbox):
    """Complete grading pipeline for single nail"""
    → Returns: {"osi_score": {...}, "grid_visualization": img}

def get_osi_score(area_percent, proximity_level):
    """Calculate OSI from area % and proximity"""
```

---

### 5. **Camera Capture (ui/scan/camera_view.py)**

Dual-camera interface for capturing left and right feet.

**Hardware:** Picamera2 (Raspberry Pi camera)

**Interaction:**
- Tap to refocus
- Hold 1.5+ seconds to upload images
- Zoom slider with ± button
- Switches between cameras (camera_id 0 & 1)

**State Machine:**
```
IDLE
  ├─ Tap → FOCUS & PREVIEW
  ├─ Hold 1.5s → CAPTURE first foot
  └─ Release → Show preview + "Proceed" button
  
FIRST_FOOT_CAPTURED
  ├─ Click "Proceed" → Switch to second camera
  └─ CAPTURE second foot
  
BOTH_CAPTURED
  └─ Call on_both_captured_callback() → Process images
```

---

### 6. **Result View (ui/scan/result_view.py)**

Displays OSI grading results with medical recommendations.

**Features:**
- Loading overlay with animated spinner
- Separate sections for left/right feet
- Toenail cards with:
  - Nail image (left side)
  - OSI score & severity badge (right side)
  - Collapsible medical recommendations
- "Save Scan" dialog with patient name input
- "Apply Med" button (enabled only if ≥3 nails per foot)

**Recommendations Database:** Hardcoded dict for each severity level

---

### 7. **Servo Control (ui/scan/servo_control_view.py)**

Robotic medication applicator interface.

**Pipeline:**
```
LEFT FOOT (Servos 5,4,3,2,1)
  ├─ Check off nails to apply medication
  ├─ Camera shows left foot feed
  └─ Click "NEXT"
      ↓
RIGHT FOOT (Servos 10,9,8,7,6)
  ├─ Check off nails
  ├─ Camera switches to right foot feed
  └─ Click "APPLY"
      ↓
CONFIRMATION
  ├─ Dialog: "Apply medication?"
  └─ On accept: Execute servo sequence
      ↓
EXECUTION
  ├─ For each selected servo:
  │   ├─ Send command: servo_index via serial
  │   └─ Wait 2.2 seconds for application
  └─ Show "Medication Applied" dialog
      ↓
DONE or REPEAT
  ├─ "Done" → Return to results
  └─ "Apply Again" → Reset pipeline
```

**Hardware:**
- Arduino connected via `/dev/ttyUSB0` (9600 baud)
- Servo mapping: `[5,4,3,2,1,10,9,8,7,6]` → indices 0-9

---

### 8. **Database (database/db_manager_v2.py)**

SQLite database with 3 tables:

```sql
TABLE patients:
  id INTEGER PRIMARY KEY
  name TEXT
  status TEXT
  created_at TEXT
  updated_at TEXT

TABLE scans:
  id INTEGER PRIMARY KEY
  patient_id INTEGER FOREIGN KEY
  date TEXT
  time TEXT
  overall_severity TEXT
  images_json TEXT (JSON dict of all images)
  nails_json TEXT (JSON list of nail data)

TABLE nail_details:
  id INTEGER PRIMARY KEY
  scan_id INTEGER FOREIGN KEY
  foot TEXT (left/right)
  nail_index INTEGER
  osi_score INTEGER
  severity TEXT
  image_path TEXT
  mask_path TEXT
```

**Key Methods:**
```python
add_patient(name) → patient_id
add_scan(patient_id, images_dict, nails_list) → scan_id
get_patient_scans(patient_id) → scan list
get_image(image_path) → OpenCV image
delete_scan(scan_id)
```

---

## Data Flow

### Image Dimensions & Transformations

```
Camera Capture
  ↓ (1280×720 RGB)
  
Resize to standard
  ↓ (512×512 if larger)
  
Detection Model (best_tn.pt)
  ├─ Input: 512×512
  └─ Output: [10 bboxes] → confidence, x,y,w,h
  
Cropping + Padding
  ├─ Input: detection bbox + 10px padding
  └─ Output: 512×512 cropped nail
  
Segmentation Model (best.pt)
  ├─ Input: 512×512 cropped nail
  └─ Output: 
      ├─ nail_mask: 512×512 binary (nail=255, bg=0)
      ├─ affected_mask: 512×512 binary (fungal=255, healthy=0)
      └─ segmentation_viz: 512×512 colored overlay
      
OSI Grid Analysis
  ├─ Input: nail_mask + affected_mask
  ├─ Overlay: 4×5 grid on nail
  └─ Output: OSI score (0-25) + grid visualization
  
Database Storage
  ├─ Original images: Base64 encoded in SQLite
  ├─ Detection visualization: Full image with bboxes
  ├─ Nail cards: Cropped 512×512 images
  └─ Masks: Segmentation masks (for debugging/review)
```

### Processing Time Breakdown (per scan)

```
[Left Foot Image]
  ├─ Detection: ~2 seconds
  ├─ Cropping: ~0.5 seconds
  ├─ Segmentation (×10 nails): ~0.5 seconds
  ├─ OSI Grading (×10 nails): ~0.3 seconds
  ├─ Visualization: ~0.5 seconds
  └─ Subtotal: ~3.8 seconds

[Right Foot Image]
  └─ Same as left: ~3.8 seconds

[Save to Database]
  └─ ~0.5 seconds

TOTAL: ~8 seconds per complete scan
```

---

## Installation & Setup

### 1. **Hardware Requirements**
- Raspberry Pi 4B+ with 4GB+ RAM
- Picamera2 (2× cameras for dual-foot capture)
- Arduino Uno/Nano with servo control
- 7" touchscreen
- Optional: On-screen keyboard (onboard package)

### 2. **Python Dependencies**

```bash
pip install PyQt5
pip install ultralytics  # YOLO
pip install opencv-python
pip install numpy
pip install picamera2  # Raspberry Pi
pip install pyserial  # Arduino communication
```

### 3. **Model Files**

Place in root directory:
- `best_tn.pt` - YOLO detection model (toenail detection)
- `best.pt` - YOLO segmentation model (nail + affected area)

Download from: [Ultralytics YOLOv8](https://docs.ultralytics.com/tasks/detect/)

### 4. **Arduino Setup**

```
Load firmware with servo control:
→ Send servo_index (0-9) via serial
→ Arduino activates corresponding servo
→ Wait for application (~2.2 seconds)
→ Send next command
```

Port: `/dev/ttyUSB0` (9600 baud)

### 5. **Database Setup**

Automatically created on first run:
```bash
database/mycoscan.db
```

### 6. **Launch Application**

```bash
cd /home/team24/Desktop/MycoScan
python main.py
```

Or use provided script:
```bash
./launch_app.sh
```

---

## Usage Guide

### For End Users

#### **Scan New Patient**

1. Click **"Start a Scan"** from landing page
2. Choose **"Capture Images"** or **"Upload Images"**
3. If capturing:
   - Hold device steady
   - Tap screen to focus
   - Hold 1.5+ seconds to capture first foot
   - Click "Proceed"
   - Switch to second foot
   - Capture second foot
4. Wait for processing (~8 seconds)
5. Review results:
   - See toenail cards with OSI scores
   - Read medical recommendations
   - Adjust patient name if needed
6. Click **"Save Scan"** to store in database
7. If **≥3 nails per foot**: Click **"Apply Med"** to apply medication

#### **Review Previous Scans**

1. Click **"View Previous Scans"** from landing
2. Browse table of patients
3. Click row to view full scan details
4. See all nail images with original analysis

#### **Apply Medication**

1. From results, click **"Apply Med"**
2. Select nails on left foot to medicate
3. Click **"NEXT"**
4. Select nails on right foot
5. Click **"APPLY"**
6. Confirm in dialog
7. Watch servo sequence execute
8. Choose "Done" or "Apply Again"

---

### For Developers

#### **Adding a New Feature**

1. **New UI Page:**
   - Create file in `ui/` folder
   - Inherit from `QWidget`
   - Add to `AppWindow` in `main.py`

2. **New Analysis Function:**
   - Add to `analysis/` module
   - Call from `ScanPage._process_foot_image()`
   - Return results dict

3. **Database Changes:**
   - Modify schema in `database/db_manager_v2.py._init_db()`
   - Add getter/setter methods
   - Test with existing data

#### **Debugging**

Logs are printed to stdout. Check with:
```bash
tail -f /home/team24/Desktop/debug.log
```

Key debug points:
- `[ScanPage]` - Image processing
- `[Detection]` - YOLO detection
- `[Segmentation]` - YOLO segmentation
- `[OSI]` - Grading calculations
- `[ServoControl]` - Medication application
- `[Database]` - Data storage

---

## Database Schema

### Complete ER Diagram

```
┌────────────┐
│  patients  │
├────────────┤
│ id (PK)    │
│ name       │
│ status     │
│ created_at │
│ updated_at │
└────────────┘
     │ 1:N
     ├─────────────────────┐
     ▼                     ▼
┌────────────┐      ┌──────────────┐
│   scans    │      │nail_details  │
├────────────┤      ├──────────────┤
│ id (PK)    │      │ id (PK)      │
│ patient_id │      │ scan_id (FK) │
│ date       │      │ foot         │
│ time       │      │ nail_index   │
│ overall_   │      │ osi_score    │
│ severity   │      │ severity     │
│ images_    │      │ image_path   │
│ json       │      │ mask_path    │
│ nails_     │      └──────────────┘
│ json       │
└────────────┘
```

### Sample JSON Fields

**images_json:**
```json
{
  "left_foot_full": "path/to/image.jpg",
  "left_foot_detection": "path/to/detection_viz.jpg",
  "left_foot_nails": ["path/nail1.jpg", "path/nail2.jpg", ...],
  "right_foot_full": "...",
  "right_foot_detection": "...",
  "right_foot_nails": [...]
}
```

**nails_json:**
```json
[
  {
    "side": "left",
    "index": 1,
    "osi_score": 12,
    "severity": "Moderate",
    "area_percent": 45,
    "proximity_level": 2,
    "image_path": "..."
  },
  ...
]
```

---

## Troubleshooting

### **Common Issues**

#### 1. Models Not Found
```
Error: FileNotFoundError: best_tn.pt
→ Solution: Copy model files to root directory
→ Verify file exists: ls -la best_tn.pt best.pt
```

#### 2. Camera Not Detected
```
Error: RuntimeError: Could not create preview config
→ Solution: Check Picamera2 is enabled
→ Run: sudo raspi-config → Interfacing → Camera → Enable
→ Reboot: sudo reboot
```

#### 3. Arduino Serial Connection Failed
```
Error: SerialException: Could not open port /dev/ttyUSB0
→ Solution: Check device connected
→ List: ls /dev/ttyUSB*
→ Permissions: sudo chmod 666 /dev/ttyUSB0
```

#### 4. Database Locked
```
Error: sqlite3.OperationalError: database is locked
→ Solution: Close other connections
→ Restart application
```

#### 5. YOLO Inference Slow
```
Issue: Processing > 10 seconds per scan
→ Solution: Check GPU acceleration available
→ Or: Use lighter model (yolov8n instead of yolov8m)
```

#### 6. On-Screen Keyboard Not Appearing
```
Error: WARNING: onboard is not installed
→ Solution: sudo apt-get install onboard
```

---

## Performance Metrics

| Component | Time | Notes |
|-----------|------|-------|
| Detection | 2-3s | Per foot (1 image) |
| Cropping | 0.5s | 10 nails |
| Segmentation | 0.5s | 10×30ms per nail |
| OSI Grading | 0.3s | Grid analysis |
| Visualization | 0.5s | Drawing overlays |
| Database Save | 0.5s | Encode + SQL insert |
| **Total per scan** | **~8s** | Left + Right feet |

**Bottle Neck:** Detection model (YOLO inference)

**Optimization Options:**
- Use TensorRT for GPU acceleration
- Reduce input resolution
- Use pruned/quantized models
- Batch multiple nails (not implemented)

---

## API Quick Reference

### ScanPage
```python
scan_page.on_images_ready(left_img, right_img, source)
scan_page._process_foot_image(img_bgr, "Left"/"Right")
scan_page._calculate_osi_for_nail(...)
```

### Analysis
```python
detector = ToenailDetector("best_tn.pt")
detections = detector.detect(img)  # → [{"bbox": ..., "confidence": ...}]

segmentation = NailSegmentation("best.pt")
masks = segmentation.segment(nail_img)  # → [{"class": ..., "mask": ...}]

osi_result = process_nail_for_grading(nail_img, nail_mask, affected_mask, nail_bbox)
# → {"osi_score": {...}, "grid_visualization": ...}
```

### Database
```python
db = DatabaseManagerV2()
patient_id = db.add_patient("John Doe")
scan_id = db.add_scan(patient_id, images_dict, nails_list)
scans = db.get_patient_scans(patient_id)
img = db.get_image("path/to/image")
```

### UI Navigation
```python
from router import goto, Route
goto(self.stack, Route.LANDING)    # → Landing page
goto(self.stack, Route.SCAN)       # → Scan page
goto(self.stack, Route.HISTORY)    # → History page
goto(self.stack, Route.SERVO_CONTROL)  # → Medication
```

---

## Future Enhancements

- [ ] Cloud storage integration
- [ ] Multi-language support
- [ ] Advanced statistics dashboard
- [ ] Treatment tracking over time
- [ ] Integration with medical records
- [ ] Mobile app companion
- [ ] Remote telemedicine support
- [ ] AI model versioning/updates

---

## License

Proprietary - MycoScan Team 24

---

## Support

For issues or questions:
- Check logs: `tail -f /home/team24/Desktop/debug.log`
- Enable verbose mode in code
- Contact development team

---

**Last Updated:** 2024  
**Version:** 3.005  
**Maintainer:** MycoScan Dev Team