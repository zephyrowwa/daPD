# database/db_manager_v2.py
"""
Redesigned database manager for MycoScan v2.7
Stores comprehensive scan data including all images and nail details.
"""
import os
import sqlite3
import json
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(__file__), "mycoscan.db")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "scans")


class DatabaseManagerV2:
    """
    New database structure:
    - patients: id, name, status (under monitoring, follow up, done), created_at, updated_at
    - scans: id, patient_id, date, severity (most dominant), images_json, nails_json
    - nail_data: id, scan_id, nail_number, side, severity, osi_score, affected_area_percent
    """

    def __init__(self, db_path: str = DB_PATH, data_dir: str = DATA_DIR):
        self.db_path = db_path
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        """Create database connection."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database schema."""
        with self._connect() as con:
            cur = con.cursor()

            # Patients table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'under monitoring',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

            # Scans table - one scan = both feet captured at once
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    overall_severity TEXT NOT NULL,
                    images_json TEXT NOT NULL,
                    nails_json TEXT NOT NULL,
                    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
                );
            """)

            # Nail details table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS nail_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    nail_number INTEGER NOT NULL,
                    side TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    osi_score INTEGER NOT NULL,
                    affected_area_percent REAL NOT NULL,
                    FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
                );
            """)

            con.commit()

    # ========== PATIENT OPERATIONS ==========

    def add_patient(self, name: str, status: str = "under monitoring") -> int:
        """Add a new patient. Returns patient_id."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO patients (name, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, status, now, now),
            )
            con.commit()
            return cur.lastrowid

    def get_patient(self, patient_id: int) -> Optional[Dict]:
        """Get patient info by ID."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, name, status, created_at, updated_at FROM patients WHERE id = ?", (patient_id,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }

    def get_patient_by_name(self, name: str) -> Optional[Dict]:
        """Get patient info by name. Returns first match."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, name, status, created_at, updated_at FROM patients WHERE name = ?", (name,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }

    def get_all_patients(self) -> List[Dict]:
        """Get all patients."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, name, status, created_at, updated_at FROM patients ORDER BY updated_at DESC")
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "status": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                }
                for row in cur.fetchall()
            ]

    def update_patient(self, patient_id: int, name: str = None, status: str = None):
        """Update patient name and/or status."""
        with self._connect() as con:
            cur = con.cursor()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if name and status:
                cur.execute(
                    "UPDATE patients SET name = ?, status = ?, updated_at = ? WHERE id = ?",
                    (name, status, now, patient_id),
                )
            elif name:
                cur.execute("UPDATE patients SET name = ?, updated_at = ? WHERE id = ?", (name, now, patient_id))
            elif status:
                cur.execute("UPDATE patients SET status = ?, updated_at = ? WHERE id = ?", (status, now, patient_id))

            con.commit()

    def delete_patient(self, patient_id: int):
        """Delete patient and all their scans and images."""
        with self._connect() as con:
            cur = con.cursor()

            # Get all scans for this patient
            cur.execute("SELECT id FROM scans WHERE patient_id = ?", (patient_id,))
            scan_ids = [row[0] for row in cur.fetchall()]

            # Delete associated images
            for scan_id in scan_ids:
                self._delete_scan_images(scan_id)

            # Delete patient (cascades to scans and nail_details)
            cur.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            con.commit()

    # ========== SCAN OPERATIONS ==========

    def add_scan(
        self,
        patient_id: int,
        feet_data: Dict,  # Contains 'left' and 'right' foot data with all nail info
        overall_severity: str,
    ) -> int:
        """
        Add a complete scan with all foot/nail images and data.
        
        feet_data structure:
        {
            'left': {
                'image': np.ndarray,  # full foot image with detection labels
                'cropped_nails': [
                    {
                        'image': np.ndarray,  # original nail
                        'osi_result': {...},  # OSI grading result with visualizations
                    },
                    ...
                ]
            },
            'right': { ... }
        }
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        with self._connect() as con:
            cur = con.cursor()

            # Save images and collect metadata
            images_dict = {}
            nails_list = []

            for side in ["left", "right"]:
                side_data = feet_data.get(side, {})
                cropped_nails = side_data.get("cropped_nails", [])

                for nail_idx, nail in enumerate(cropped_nails, 1):
                    nail_number = nail_idx

                    # Save nail images
                    nail_images = self._save_nail_images(
                        patient_id, side, nail_number, nail
                    )
                    images_dict[f"{side}_nail_{nail_number}"] = nail_images

                    # Extract OSI data
                    osi_result = nail.get("osi_result", {})
                    osi_score_data = osi_result.get("osi_score", {})

                    severity = osi_score_data.get("severity", "Unknown")
                    osi_score = osi_score_data.get("total_osi_score", 0)
                    affected_area = osi_score_data.get("area_percent", 0)

                    nails_list.append(
                        {
                            "nail_number": nail_number,
                            "side": side,
                            "severity": severity,
                            "osi_score": osi_score,
                            "affected_area_percent": affected_area,
                        }
                    )

                # Save full foot image with detection labels
                foot_image = side_data.get("image")
                detection_viz = side_data.get("detection_visualization")
                
                if foot_image is not None:
                    foot_img_path = self._save_image(
                        patient_id, f"{side}_foot_full.jpg", foot_image
                    )
                    images_dict[f"{side}_foot_full"] = foot_img_path
                
                # Save detection visualization (with bounding boxes and labels)
                if detection_viz is not None:
                    detection_path = self._save_image(
                        patient_id, f"{side}_foot_detection.jpg", detection_viz
                    )
                    images_dict[f"{side}_foot_detection"] = detection_path

            # Insert scan into database
            cur.execute(
                "INSERT INTO scans (patient_id, date, time, overall_severity, images_json, nails_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    patient_id,
                    date_str,
                    time_str,
                    overall_severity,
                    json.dumps(images_dict),
                    json.dumps(nails_list),
                ),
            )
            con.commit()
            scan_id = cur.lastrowid

            # Insert nail details
            for nail in nails_list:
                cur.execute(
                    "INSERT INTO nail_details (scan_id, nail_number, side, severity, osi_score, affected_area_percent) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        scan_id,
                        nail["nail_number"],
                        nail["side"],
                        nail["severity"],
                        nail["osi_score"],
                        nail["affected_area_percent"],
                    ),
                )
            con.commit()

            return scan_id

    def get_scans_by_patient(self, patient_id: int) -> List[Dict]:
        """Get all scans for a patient."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, patient_id, date, time, overall_severity, images_json, nails_json "
                "FROM scans WHERE patient_id = ? ORDER BY date DESC, time DESC",
                (patient_id,),
            )
            scans = []
            for row in cur.fetchall():
                scans.append(
                    {
                        "id": row[0],
                        "patient_id": row[1],
                        "date": row[2],
                        "time": row[3],
                        "overall_severity": row[4],
                        "images": json.loads(row[5]),
                        "nails": json.loads(row[6]),
                    }
                )
            return scans

    def get_scan(self, scan_id: int) -> Optional[Dict]:
        """Get a specific scan with all its data."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "SELECT id, patient_id, date, time, overall_severity, images_json, nails_json "
                "FROM scans WHERE id = ?",
                (scan_id,),
            )
            row = cur.fetchone()
            if not row:
                return None

            return {
                "id": row[0],
                "patient_id": row[1],
                "date": row[2],
                "time": row[3],
                "overall_severity": row[4],
                "images": json.loads(row[5]),
                "nails": json.loads(row[6]),
            }

    def delete_scan(self, scan_id: int):
        """Delete a scan and its associated images."""
        self._delete_scan_images(scan_id)
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
            con.commit()

    def delete_all_scans(self):
        """Delete all scans and their associated images."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id FROM scans")
            scan_ids = [row[0] for row in cur.fetchall()]

        for scan_id in scan_ids:
            self._delete_scan_images(scan_id)

        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM scans")
            con.commit()

    # ========== IMAGE OPERATIONS ==========

    def _save_image(self, patient_id: int, filename: str, img_bgr: np.ndarray) -> str:
        """Save image to file system and return path."""
        patient_dir = os.path.join(self.data_dir, f"patient_{patient_id}")
        os.makedirs(patient_dir, exist_ok=True)
        img_path = os.path.join(patient_dir, filename)
        cv2.imwrite(img_path, img_bgr)
        return img_path

    def _save_nail_images(
        self, patient_id: int, side: str, nail_number: int, nail_data: Dict
    ) -> Dict[str, str]:
        """
        Save all nail images (original, segmentation+grid, etc).
        Returns dict with image names and paths.
        """
        severity = nail_data.get("osi_result", {}).get("osi_score", {}).get("severity", "Unknown")
        nail_images = {}

        # Original cropped nail
        original_img = nail_data.get("image")
        if original_img is not None:
            filename = f"{side}_nail_{nail_number}_original.jpg"
            nail_images["original"] = self._save_image(patient_id, filename, original_img)

        # Segmentation with grid visualization
        osi_result = nail_data.get("osi_result", {})
        grid_viz = osi_result.get("grid_visualization")
        if grid_viz is not None:
            filename = f"{side}_nail_{nail_number}_grid.jpg"
            nail_images["grid"] = self._save_image(patient_id, filename, grid_viz)

        # Nail segmentation overlay
        nail_seg = osi_result.get("nail_segmentation_visualization")
        if nail_seg is not None:
            filename = f"{side}_nail_{nail_number}_segmentation.jpg"
            nail_images["segmentation"] = self._save_image(patient_id, filename, nail_seg)

        return nail_images

    def _delete_scan_images(self, scan_id: int):
        """Delete all images associated with a scan."""
        scan = self.get_scan(scan_id)
        if not scan:
            return

        images = scan.get("images", {})
        for img_path in images.values():
            if isinstance(img_path, dict):  # nested dict of images
                for nested_path in img_path.values():
                    if isinstance(nested_path, str) and os.path.exists(nested_path):
                        os.remove(nested_path)
            elif isinstance(img_path, str) and os.path.exists(img_path):
                os.remove(img_path)

    def get_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load and return an image."""
        if not os.path.exists(image_path):
            return None
        return cv2.imread(image_path)

    # ========== STATS ==========

    def get_patient_statistics(self, patient_id: int) -> Dict:
        """Get statistics for a patient."""
        scans = self.get_scans_by_patient(patient_id)
        if not scans:
            return {
                "total_scans": 0,
                "total_nails": 0,
                "severity_distribution": {},
                "average_osi_score": 0,
            }

        total_nails = 0
        severity_counts = {}
        total_osi = 0
        nail_count = 0

        for scan in scans:
            nails = scan.get("nails", [])
            total_nails += len(nails)
            for nail in nails:
                severity = nail.get("severity", "Unknown")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                total_osi += nail.get("osi_score", 0)
                nail_count += 1

        return {
            "total_scans": len(scans),
            "total_nails": total_nails,
            "severity_distribution": severity_counts,
            "average_osi_score": total_osi / nail_count if nail_count > 0 else 0,
        }
