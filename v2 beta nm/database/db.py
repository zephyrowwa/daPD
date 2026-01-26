# db.py
import os, sqlite3, threading, time
from typing import List, Tuple, Optional, Dict

_DEFAULT_DIR = "data"
_DB_PATH = os.path.join(_DEFAULT_DIR, "mycoscan.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  recommended_action TEXT DEFAULT '',
  captured_path TEXT NOT NULL,
  segmented_path TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

class Database:
    def __init__(self, db_path: str = _DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._db_path = db_path
        self._lock = threading.Lock()
        with sqlite3.connect(self._db_path) as con:
            con.execute(_SCHEMA)
            con.commit()

    def add_scan(self, patient_name: str, severity: str, captured_path: str, segmented_path: str,
                 recommended_action: str = "") -> int:
        with self._lock, sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute(
                "INSERT INTO scans (patient_name, severity, recommended_action, captured_path, segmented_path, created_at) "
                "VALUES (?, ?, ?, ?, ?, datetime('now','localtime'))",
                (patient_name, severity, recommended_action, captured_path, segmented_path),
            )
            con.commit()
            return cur.lastrowid

    def list_scans(self) -> List[Tuple]:
        with self._lock, sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT id, patient_name, severity, recommended_action, captured_path, segmented_path, created_at "
                        "FROM scans ORDER BY datetime(created_at) DESC")
            return cur.fetchall()

    def get_scan(self, scan_id: int) -> Optional[Tuple]:
        with self._lock, sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT id, patient_name, severity, recommended_action, captured_path, segmented_path, created_at "
                        "FROM scans WHERE id = ?", (scan_id,))
            return cur.fetchone()
