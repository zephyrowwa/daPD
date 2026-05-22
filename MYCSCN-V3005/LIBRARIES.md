# MycoScan Libraries Documentation

This document provides an overview of the key libraries and tools used throughout the MycoScan application.

## Core Libraries

### PyQt5
**Purpose:** GUI Framework and User Interface

PyQt5 is used to build the entire graphical user interface for MycoScan. It provides cross-platform support for creating desktop applications with custom layouts, widgets, and styling.

**Usage:**
- `PyQt5.QtWidgets` - Main UI components (QMainWindow, QWidget, QPushButton, QLabel, QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget, QSlider)
- `PyQt5.QtCore` - Core functionality (Qt constants, QTimer for frame updates, QEvent for user interactions, QSize, signals/slots)
- `PyQt5.QtGui` - Graphics and styling (QPixmap for image display, QImage for image conversion, QFont for typography, QColor for styling)

**Key Features Used:**
- Multi-page navigation using QStackedWidget
- Real-time frame updates with QTimer
- Touch event handling for interactive controls
- Custom QSS styling for consistent visual design
- Virtual keyboard integration with QLineEdit/QTextEdit focus events

---

### OpenCV (cv2)
**Purpose:** Image Processing and Computer Vision

OpenCV is used for real-time image processing, camera frame manipulation, and image analysis tasks.

**Usage:**
- Image color space conversions (BGR to RGB)
- Frame capture and manipulation from camera feeds
- Image encoding/decoding for database storage
- Drawing annotations on images (contours, grids, overlays)
- Image resizing and transformations
- Contour detection and analysis for nail segmentation

**Key Operations:**
- `cv2.cvtColor()` - Convert between color spaces
- `cv2.findContours()` - Detect nail boundaries and affected areas
- `cv2.boundingRect()` - Extract bounding boxes
- `cv2.drawContours()` - Visualize detection results
- `cv2.imread()` / `cv2.imwrite()` - File I/O for scan images

---

### Ultralytics (YOLO)
**Purpose:** Deep Learning Object Detection and Segmentation

Ultralytics provides pre-trained YOLO models for automated nail detection and disease area segmentation.

**Usage:**
- Nail detection using `best_tn.pt` model (detects individual toenails in full foot images)
- Nail segmentation using `best.pt` model (segments affected/diseased areas on cropped nails)
- Model prediction inference with configurable confidence thresholds

**Key Components:**
- `ToenailDetector` class - Detects toenails using YOLO object detection
- `NailSegmentation` class - Segments affected areas using YOLO segmentation models
- Processes results to extract class labels, confidence scores, and pixel masks

**Workflow:**
1. Full foot image → YOLO detection → Toenail bounding boxes
2. Cropped nails → YOLO segmentation → Affected area masks
3. Masks → OSI grading analysis

---

### NumPy
**Purpose:** Numerical Computing and Array Operations

NumPy handles all numerical and array manipulations throughout the application, especially for image data processing.

**Usage:**
- Image array manipulation (create, reshape, convert data types)
- Mask creation and operations for segmentation results
- Array-to-binary conversions for database storage
- Statistical calculations for disease severity analysis
- Image overlay and blending operations

**Key Operations:**
- `np.ndarray` - Core data structure for image data
- `np.frombuffer()` / `tobytes()` - Image serialization for database
- `np.uint8` - Standard image data type
- Array indexing and slicing for image regions
- Mask generation: `np.zeros()`, `np.ones()`

---

### Picamera2
**Purpose:** Raspberry Pi Camera Interface

Picamera2 provides the interface to Raspberry Pi camera hardware, enabling live video capture and frame-by-frame image acquisition.

**Usage:**
- Initialize and configure camera with `Picamera2(camera_num=X)`
- Capture live preview frames in real-time
- Support multiple camera IDs for multi-camera setups (left foot, right foot)
- Frame acquisition at configurable resolutions
- Camera property management (autofocus, exposure, etc.)

**Key Features:**
- Real-time video streaming to PyQt5 display
- Frame capture for scan processing
- Multi-camera support with camera ID selection
- Integration with QTimer for synchronized frame updates

---

### PySerial
**Purpose:** Serial Communication with Arduino

PySerial enables communication with Arduino hardware for servo motor control.

**Usage:**
- Establish serial connections to Arduino (`/dev/ttyUSB0` at 9600 baud)
- Send servo positioning commands
- Receive acknowledgment messages
- Control physical servo motors for camera positioning/foot scanning automation

**Key Operations:**
- `serial.Serial()` - Establish connection
- `.write()` - Send commands to Arduino
- `.read()` - Receive responses
- `.is_open` - Check connection status
- `.close()` - Gracefully close connection

---

## Additional Libraries

### SQLite3
**Purpose:** Local Database Management

SQLite3 stores patient scan data, image records, and OSI grading results locally.

**Features:**
- Persistent data storage for scan history
- Patient record management
- Image BLOB storage (compressed images)
- Query-based retrieval of historical scans
- Transaction support for data integrity

---

### JSON
**Purpose:** Data Serialization

JSON is used for storing structured metadata and analysis results.

**Usage:**
- Serialize scan metadata (timestamps, patient info)
- Store analysis results and grading data
- Configuration file handling

---

### Datetime
**Purpose:** Timestamp Management

Datetime module provides timestamp recording for scan sessions and historical data tracking.

---

### OS & Pathlib
**Purpose:** File System Operations

Used for:
- File path management (cross-platform compatibility)
- Directory creation and navigation
- Image file organization
- Configuration file access

---

## Architecture Overview

```
User Interface (PyQt5)
    ↓
Camera Input (Picamera2) / File Upload
    ↓
Image Processing (OpenCV + NumPy)
    ↓
AI Analysis (Ultralytics YOLO)
    ↓
Disease Grading (NumPy calculations)
    ↓
Hardware Control (PySerial → Arduino → Servos)
    ↓
Data Storage (SQLite3 + File System)
    ↓
Display & History (PyQt5)
```

---

## Data Flow

1. **Capture**: Picamera2 captures live frames, displayed via PyQt5
2. **Process**: OpenCV processes frames; NumPy handles arrays
3. **Analyze**: Ultralytics YOLO detects nails and segments affected areas
4. **Grade**: Custom OSI grading algorithm calculates severity using NumPy
5. **Store**: Results saved to SQLite3 database with image BLOBs
6. **Control**: PySerial sends commands to Arduino for servo positioning
7. **Retrieve**: PyQt5 displays historical data from SQLite3

---

## Summary

| Library | Role | Primary Use |
|---------|------|-------------|
| **PyQt5** | UI Framework | Application interface, real-time display |
| **OpenCV** | Image Processing | Frame processing, contour detection, visualization |
| **Ultralytics** | AI/ML | Nail detection and disease area segmentation |
| **NumPy** | Numerical Computing | Array manipulation, mask operations, calculations |
| **Picamera2** | Camera Interface | Capture video frames from Raspberry Pi camera |
| **PySerial** | Serial Communication | Control Arduino servo motors |
| **SQLite3** | Database | Store patient records and scan history |
| **JSON** | Data Format | Serialize metadata and results |
