# main.py
import sys, os
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from styles import BASE_QSS
from router import Route, goto
from widgets.splash import build_splash
from ui.landing import LandingPage
from ui.history.history_page_v2 import HistoryPageV2
from ui.history.scan_detail_view import ScanDetailView
from ui.scan.scan_page import ScanPage
from ui.scan.servo_control_view import ServoControlView
from keyboard_manager import get_keyboard_manager


class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MycoScan v3.005")
        self.setMinimumSize(800, 480)   # 7" LCD baseline; layouts scale up
        
        # Enable fullscreen while allowing on-screen keyboard to appear
        # Set window flags to allow top-level keyboard window
        from PyQt5.QtCore import Qt
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.showFullScreen()  # Show in fullscreen mode
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # pages
        self.page_landing = LandingPage(
            on_start_scan=lambda: goto(self.stack, Route.SCAN),
            on_view_history=lambda: goto(self.stack, Route.HISTORY)
        )
        self.page_scan = ScanPage(
            on_back=lambda: goto(self.stack, Route.LANDING),
            on_apply_med=lambda: goto(self.stack, Route.SERVO_CONTROL)
        )
        self.page_history = HistoryPageV2(
            on_back=lambda: goto(self.stack, Route.LANDING),
            on_view_scan_details=self._show_scan_details
        )
        self.page_scan_detail = ScanDetailView(on_back=lambda: goto(self.stack, Route.HISTORY))
        self.page_servo_control = ServoControlView(
            on_back=lambda: self._return_to_scan_results(),
            on_medication_done=lambda: self._return_to_scan_results()
        )

        # add to stack
        self.stack.addWidget(self.page_landing)       # 0
        self.stack.addWidget(self.page_scan)          # 1
        self.stack.addWidget(self.page_history)       # 2
        self.stack.addWidget(self.page_scan_detail)   # 3
        self.stack.addWidget(self.page_servo_control) # 4
        goto(self.stack, Route.LANDING)
        
        # Initialize keyboard manager for onboard on-screen keyboard
        self.keyboard_manager = get_keyboard_manager()
        self.keyboard_manager.install_on_parent(self.stack)
    
    def _show_scan_details(self, patient_id):
        """Load and show scan detail view for patient."""
        self.page_scan_detail.show_scan(patient_id, self.page_history.db)
        goto(self.stack, Route.SCAN_DETAIL)
    
    def _return_to_scan_results(self):
        """Return to the scan results page after medication applied."""
        # Set flag to prevent showEvent from overriding
        self.page_scan.returning_from_medication = True
        # Set the ScanPage internal stack to show result_view
        self.page_scan.stack.setCurrentWidget(self.page_scan.result_view)
        self.page_scan.btn_back.raise_()
        # Now navigate to ScanPage
        self.stack.setCurrentWidget(self.page_scan)

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
