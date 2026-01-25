
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import Qt
import sys
from database.db import Database
from ui.scan.scan_page import ScanPage
from ui.history.history_page import HistoryPage

class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MycoScan V1")
        self.setMinimumSize(800, 480)

        self.db = Database()

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.scan = ScanPage(on_back=self.show_history, db=self.db)
        self.history = HistoryPage(on_back=self.show_scan, db=self.db)

        self.stack.addWidget(self.scan)
        self.stack.addWidget(self.history)
        self.show_scan()

    def show_scan(self):
        self.stack.setCurrentWidget(self.scan)

    def show_history(self):
        self.history.load_data()
        self.stack.setCurrentWidget(self.history)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    win = AppWindow()
    win.show()
    sys.exit(app.exec_())
