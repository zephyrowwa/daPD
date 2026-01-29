# main.py
import sys, os
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from styles import BASE_QSS
from router import Route, goto
from widgets.splash import build_splash
from ui.landing import LandingPage
from ui.history.history_page_v2 import HistoryPageV2
from ui.history.scan_detail_view import ScanDetailView
from ui.scan.scan_page import ScanPage
from ui.scan.servo_control_view import ServoControlView


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MycoScan v3.005")
        self.setMinimumSize(800, 480)   # 7" LCD baseline; layouts scale up
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # pages
        self.page_landing = LandingPage(
            on_start_scan=lambda: goto(self.stack, Route.SCAN),
            on_view_history=lambda: goto(self.stack, Route.HISTORY),
            on_servo_control=lambda: goto(self.stack, Route.SERVO_CONTROL)
        )
        self.page_scan = ScanPage(on_back=lambda: goto(self.stack, Route.LANDING))
        self.page_history = HistoryPageV2(
            on_back=lambda: goto(self.stack, Route.LANDING),
            on_view_scan_details=self._show_scan_details
        )
        self.page_scan_detail = ScanDetailView(on_back=lambda: goto(self.stack, Route.HISTORY))
        self.page_servo_control = ServoControlView(on_back=lambda: goto(self.stack, Route.LANDING))

        # add to stack
        self.stack.addWidget(self.page_landing)       # 0
        self.stack.addWidget(self.page_scan)          # 1
        self.stack.addWidget(self.page_history)       # 2
        self.stack.addWidget(self.page_scan_detail)   # 3
        self.stack.addWidget(self.page_servo_control) # 4
        goto(self.stack, Route.LANDING)
    
    def _show_scan_details(self, patient_id):
        """Load and show scan detail view for patient."""
        self.page_scan_detail.show_scan(patient_id, self.page_history.db)
        goto(self.stack, Route.SCAN_DETAIL)

def main():
    # HiDPI-friendly on Pi 7" and desktops
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyleSheet(BASE_QSS)

    splash = build_splash()
    splash.show(); app.processEvents()

    win = AppWindow()
    QTimer.singleShot(900, splash.close)
    QTimer.singleShot(900, win.show)

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
