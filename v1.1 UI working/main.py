# main.py
import sys, os
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from styles import BASE_QSS
from router import Route, goto
from widgets.splash import build_splash
from ui.landing import LandingPage
from ui.scan import ScanPage
from ui.history import HistoryPage

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MycoScan — UI Prototype")
        self.setMinimumSize(800, 480)   # 7" LCD baseline; layouts scale up
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # pages
        self.page_landing = LandingPage(
            on_start_scan=lambda: goto(self.stack, Route.SCAN),
            on_view_history=lambda: goto(self.stack, Route.HISTORY)
        )
        self.page_scan = ScanPage(on_back=lambda: goto(self.stack, Route.LANDING))
        self.page_history = HistoryPage(on_back=lambda: goto(self.stack, Route.LANDING))

        # add to stack
        self.stack.addWidget(self.page_landing)   # 0
        self.stack.addWidget(self.page_scan)      # 1
        self.stack.addWidget(self.page_history)   # 2
        goto(self.stack, Route.LANDING)

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
