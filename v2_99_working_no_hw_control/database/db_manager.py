# database/db_manager.py
import os, sqlite3, cv2, numpy as np
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "mycoscan.db")

class DatabaseManager:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        self._init_db()

    # ---------- internal ----------
    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    recommendation TEXT,
                    date TEXT NOT NULL,
                    image BLOB
                );
            """)
            con.commit()

    # ---------- image helpers ----------
    @staticmethod
    def _encode_image(img_bgr) -> bytes:
        ok, buf = cv2.imencode(".jpg", img_bgr)
        if not ok:
            raise RuntimeError("Failed to encode image")
        return buf.tobytes()

    @staticmethod
    def _decode_image(blob) -> np.ndarray | None:
        if blob is None:
            return None
        arr = np.frombuffer(blob, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)

    # ---------- CRUD ----------
    def add_scan(self, patient: str, severity: str, recommendation: str, img_bgr):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO scans (patient, severity, recommendation, date, image) VALUES (?, ?, ?, ?, ?)",
                (patient, severity, recommendation, datetime.now().strftime("%Y-%m-%d"),
                 sqlite3.Binary(self._encode_image(img_bgr))),
            )
            con.commit()

    def get_all_scans(self):
        """Return rows as list of tuples: (id, patient, severity, recommendation, date)."""
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT id, patient, severity, recommendation, date FROM scans ORDER BY id DESC")
            return cur.fetchall()

    def get_scan_by_id(self, scan_id: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("SELECT patient, severity, recommendation, date, image FROM scans WHERE id=?", (scan_id,))
            row = cur.fetchone()
            if not row:
                return None
            patient, severity, reco, date, blob = row
            return {
                "patient": patient,
                "severity": severity,
                "recommendation": reco,
                "date": date,
                "image": self._decode_image(blob),
            }

    def update_patient_name(self, scan_id: int, new_name: str):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("UPDATE scans SET patient=? WHERE id=?", (new_name, scan_id))
            con.commit()

    def delete_scan(self, scan_id: int):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM scans WHERE id=?", (scan_id,))
            con.commit()

    def delete_all(self):
        with self._connect() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM scans")
            con.commit()
