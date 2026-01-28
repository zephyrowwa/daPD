from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QPushButton, QHBoxLayout, QFrame,
    QInputDialog, QMessageBox
)
from styles import BRAND, ACCENT, BORD
from ui.history.detail_page import DetailPage


class HistoryPage(QWidget):
    """Displays saved scans table with full DB functions."""

    def __init__(self, on_back, db):
        super().__init__()
        self.on_back = on_back
        self.db = db
        self._build_ui()
        self.load_data()

    # -------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ---------- Top Bar ----------
        top_bar = QHBoxLayout()

        btn_back = QPushButton("← Back")
        btn_back.setFixedSize(80, 34)
        btn_back.clicked.connect(self.on_back)
        btn_back.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {BRAND};
                border: 1.5px solid {BRAND};
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(37, 99, 235, 0.08);
            }}
            """
        )

        title = QLabel("Previous Scans")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font: 700 22px 'Segoe UI'; color: #111827;")

        # right-side control buttons
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete_all = QPushButton("Delete All")

        for b in (self.btn_edit, self.btn_delete, self.btn_delete_all):
            b.setFixedSize(130, 36)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton{{background:{BRAND};color:white;border:none;border-radius:8px;font-weight:600;}}"
                "QPushButton:hover{background:#2563eb;}"
            )

        self.btn_edit.clicked.connect(self.edit_name)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_delete_all.clicked.connect(self.delete_all)

        right_controls = QHBoxLayout()
        right_controls.setSpacing(8)
        right_controls.addWidget(self.btn_edit)
        right_controls.addWidget(self.btn_delete)
        right_controls.addWidget(self.btn_delete_all)

        top_bar.addWidget(btn_back, 0, Qt.AlignLeft)
        top_bar.addWidget(title, 1, Qt.AlignCenter)
        top_bar.addLayout(right_controls)
        layout.addLayout(top_bar)

        # ---------- Scrollable Table ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QFrame()
        scroll.setWidget(container)

        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Patient", "Severity", "Recommended Action", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                gridline-color: #e5e7eb;
                alternate-background-color: #f9fafb;
            }
            QHeaderView::section {
                background: #f3f4f6;
                font-weight: 600;
                border: none;
                padding: 6px;
            }
            """
        )
        self.table.cellDoubleClicked.connect(self.open_details)
        vbox.addWidget(self.table)
        layout.addWidget(scroll)
        self.setLayout(layout)

    # -------------------------------------------------------------
    def load_data(self):
        """Load all scans from database into table."""
        self.table.setRowCount(0)
        rows = self.db.list_scans()
        for r, row in enumerate(rows):
            scan_id, name, severity, rec, cap_path, seg_path, date = row
            self.table.insertRow(r)
            for c, val in enumerate((name, severity, rec, date)):
                item = QTableWidgetItem(str(val))
                item.setData(Qt.UserRole, scan_id)  # store DB id
                self.table.setItem(r, c, item)

    def showEvent(self, event):
        """Auto-refresh when page is shown."""
        self.load_data()
        super().showEvent(event)

    # -------------------------------------------------------------
    # Button handlers
    # -------------------------------------------------------------
    def _current_scan_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 0).data(Qt.UserRole)

    def edit_name(self):
        scan_id = self._current_scan_id()
        if scan_id is None:
            QMessageBox.information(self, "Edit", "Select a record first.")
            return
        current = self.table.item(self.table.currentRow(), 0).text()
        new_name, ok = QInputDialog.getText(self, "Edit Patient Name", "Enter new name:", text=current)
        if not ok or not new_name.strip():
            return
        try:
            # use standard sqlite update instead of _connect
            import sqlite3
            con = sqlite3.connect(self.db._db_path)
            cur = con.cursor()
            cur.execute("UPDATE scans SET patient_name=? WHERE id=?", (new_name.strip(), scan_id))
            con.commit()
            con.close()
            self.load_data()
            QMessageBox.information(self, "Updated", f"Name updated to '{new_name.strip()}'.")
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))


    def delete_selected(self):
        scan_id = self._current_scan_id()
        if scan_id is None:
            QMessageBox.information(self, "Delete", "Select a record to delete.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected scan?") != QMessageBox.Yes:
            return
        try:
            import sqlite3
            con = sqlite3.connect(self.db._db_path)
            cur = con.cursor()
            cur.execute("DELETE FROM scans WHERE id=?", (scan_id,))
            con.commit()
            con.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))


    def delete_all(self):
        if QMessageBox.question(self, "Confirm", "Delete ALL scans?") != QMessageBox.Yes:
            return
        try:
            import sqlite3
            con = sqlite3.connect(self.db._db_path)
            cur = con.cursor()
            cur.execute("DELETE FROM scans")
            con.commit()
            con.close()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "DB Error", str(e))


    def open_details(self, row, column):
        """Open detail window showing image, name, and severity."""
        item = self.table.item(row, 0)
        scan_id = item.data(Qt.UserRole)
        record = self.db.get_scan(scan_id)
        if record is None:
            return
        _, name, severity, rec, cap_path, seg_path, date = record
        self.detail = DetailPage(name, severity, seg_path, parent=self)
        self.detail.show()
