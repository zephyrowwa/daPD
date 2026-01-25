
import sqlite3, os, threading

DB_PATH = "mycoscan.db"

SCHEMA = '''
CREATE TABLE IF NOT EXISTS scans (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 patient_name TEXT,
 severity TEXT,
 recommendation TEXT,
 image_path TEXT,
 created_at TEXT
)
'''

class Database:
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute(SCHEMA)

    def add_scan(self, name, severity, rec, path):
        with self.lock:
            self.conn.execute(
                "INSERT INTO scans VALUES (NULL,?,?,?, ?, datetime('now'))",
                (name, severity, rec, path)
            )
            self.conn.commit()

    def list_scans(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM scans ORDER BY id DESC")
            return cur.fetchall()

    def update_name(self, scan_id, name):
        with self.lock:
            self.conn.execute("UPDATE scans SET patient_name=? WHERE id=?", (name, scan_id))
            self.conn.commit()

    def delete_scan(self, scan_id):
        with self.lock:
            self.conn.execute("DELETE FROM scans WHERE id=?", (scan_id,))
            self.conn.commit()

    def delete_all(self):
        with self.lock:
            self.conn.execute("DELETE FROM scans")
            self.conn.commit()
