# styles.py
BRAND = "#2563eb"   # blue-600
ACCENT = "#16a34a"  # green-600
TEXT  = "#111827"   # gray-900
MUTED = "#6b7280"   # gray-500
BG    = "#ffffff"
CANVAS= "#f3f4f6"   # gray-100
BORD  = "#e5e7eb"   # gray-200

BASE_QSS = f"""
QMainWindow {{ background: {BG}; }}
QWidget#Canvas {{ background: {CANVAS}; }}
QPushButton {{
  min-height: 40px; border-radius: 10px; font: 600 14px 'Segoe UI';
}}
QGroupBox {{
  font: 600 12px 'Segoe UI';
  border: 1px solid {BORD}; border-radius: 8px; margin-top: 8px;
}}
QGroupBox::title {{
  subcontrol-origin: margin; left: 8px; padding: 0 4px; color: {MUTED};
}}
QTableWidget {{
  gridline-color: {BORD};
}}
"""
