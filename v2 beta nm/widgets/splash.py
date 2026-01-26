# widgets/splash.py
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtWidgets import QSplashScreen
from styles import BRAND, MUTED

def build_splash():
    pix = QPixmap(420, 220); pix.fill(Qt.white)
    p = QPainter(pix); p.setRenderHint(QPainter.Antialiasing, True)
    p.fillRect(0, 0, 420, 76, QColor(BRAND))
    p.setPen(Qt.white); p.setFont(QFont("Segoe UI", 20, QFont.DemiBold))
    p.drawText(16, 48, "MycoScan")
    p.setPen(QColor(MUTED)); p.setFont(QFont("Segoe UI", 10))
    p.drawText(16, 120, "Booting UI…")
    p.end()
    return QSplashScreen(pix, Qt.WindowStaysOnTopHint)
