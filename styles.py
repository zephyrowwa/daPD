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
# Add these in styles.py
BTN_PRIMARY = """
QPushButton {
  background: %(brand)s;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-family: 'DejaVu Sans', 'Segoe UI';
  font-size: 14px;
  font-weight: 700;
}
QPushButton:hover { background: #1d4ed8; }
"""

BTN_ACCENT = """
QPushButton {
  background: %(accent)s;
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  font-family: 'DejaVu Sans', 'Segoe UI';
  font-size: 14px;
  font-weight: 700;
}
QPushButton:hover { background: #15803d; }
"""

BTN_OUTLINE = """
QPushButton {
  background: transparent;
  color: %(brand)s;
  border: 2px solid %(brand)s;
  border-radius: 12px;
  padding: 10px 20px;
  font-family: 'DejaVu Sans', 'Segoe UI';
  font-size: 14px;
  font-weight: 700;
}
QPushButton:hover { background: rgba(37,99,235,0.06); }
"""

# Then format with your colors when applying:
# btn.setStyleSheet(BTN_PRIMARY % {"brand": BRAND})
# btn.setStyleSheet(BTN_ACCENT  % {"accent": ACCENT})
# btn.setStyleSheet(BTN_OUTLINE % {"brand": BRAND})
