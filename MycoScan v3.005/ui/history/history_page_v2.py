"""
History Page V2 - View previous scans with new database structure
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QPushButton, QHBoxLayout, QFrame,
    QInputDialog, QMessageBox, QComboBox
)
from PyQt5.QtGui import QFont
from styles import BRAND, ACCENT, BORD, MUTED
from database.db_manager_v2 import DatabaseManagerV2


class HistoryPageV2(QWidget):
    """Displays patient history table with scan management."""

    def __init__(self, on_back, on_view_scan_details):
        super().__init__()
        self.on_back = on_back
        self.on_view_scan_details = on_view_scan_details
        self.db = DatabaseManagerV2()
        self.selected_patient_id = None
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        """Build the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()

        btn_back = QPushButton("← Back")
        btn_back.setFixedSize(80, 40)
        btn_back.clicked.connect(self.on_back)
        btn_back.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {BRAND};
                border: 2px solid {BRAND};
                border-radius: 6px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(37, 99, 235, 0.1);
            }}
            """
        )

        title = QLabel("Previous Scans")
        title_font = QFont("Segoe UI", 22)
        title_font.setWeight(QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1f2937;")

        # Control buttons
        self.btn_edit = QPushButton("Edit")
        self.btn_delete_selected = QPushButton("Delete Selected")
        self.btn_delete_all = QPushButton("Delete All")

        for btn in [self.btn_edit, self.btn_delete_selected, self.btn_delete_all]:
            btn.setFixedSize(130, 40)
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {BRAND};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: 700;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: #1d4ed8;
                }}
                QPushButton:pressed {{
                    background-color: #1e40af;
                }}
                """
            )

        self.btn_edit.clicked.connect(self.edit_selected)
        self.btn_delete_selected.clicked.connect(self.delete_selected)
        self.btn_delete_all.clicked.connect(self.delete_all)

        top_bar.addWidget(btn_back, 0, Qt.AlignLeft)
        top_bar.addWidget(title, 1, Qt.AlignCenter)
        top_bar.addWidget(self.btn_edit)
        top_bar.addWidget(self.btn_delete_selected)
        top_bar.addWidget(self.btn_delete_all)

        layout.addLayout(top_bar)

        # ===== TABLE =====
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d1d5db;
                border-radius: 8px;
            }
        """)

        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Patient", "Status", "Recommended Action", "Date"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #d1d5db;
                gridline-color: #e5e7eb;
                alternate-background-color: #f9fafb;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                color: #1f2937;
                padding: 8px;
                border: none;
                font-weight: 700;
            }
            QTableWidget::item:selected {
                background-color: #dbeafe;
            }
            """
        )
        self.table.doubleClicked.connect(self.open_scan_details)
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

        container_layout.addWidget(self.table)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

    def load_data(self):
        """Load all patients and their scans."""
        self.table.setRowCount(0)
        patients = self.db.get_all_patients()

        for row, patient in enumerate(patients):
            # Get scans for this patient
            scans = self.db.get_scans_by_patient(patient["id"])
            if not scans:
                continue

            # Use most recent scan info
            latest_scan = scans[0]  # sorted by date desc
            nails = latest_scan.get("nails", [])

            # Determine recommended action (most severe)
            severity_priority = {
                "Clinically Cured / No involvement": 0,
                "Mild": 1,
                "Moderate": 2,
                "Severe": 3,
            }
            all_severities = [nail.get("severity", "Unknown") for nail in nails]
            most_severe = max(
                all_severities, key=lambda x: severity_priority.get(x, -1)
            ) if all_severities else "Unknown"

            # Map severity to recommendation
            recommendations = {
                "Clinically Cured / No involvement": "Continue monitoring",
                "Mild": "Topical treatment recommended",
                "Moderate": "Consult dermatologist",
                "Severe": "Urgent dermatologist consultation",
            }
            recommended_action = recommendations.get(most_severe, "Consult specialist")

            # Format date with time
            date_str = f"{latest_scan['date']} {latest_scan['time']}"

            self.table.insertRow(row)

            # Store patient_id in first column
            patient_item = QTableWidgetItem(patient["name"])
            patient_item.setData(Qt.UserRole, patient["id"])
            self.table.setItem(row, 0, patient_item)

            status_item = QTableWidgetItem(patient["status"])
            self.table.setItem(row, 1, status_item)

            action_item = QTableWidgetItem(recommended_action)
            self.table.setItem(row, 2, action_item)

            date_item = QTableWidgetItem(date_str)
            self.table.setItem(row, 3, date_item)

    def showEvent(self, event):
        """Auto-refresh when page is shown."""
        self.load_data()
        super().showEvent(event)

    def on_selection_changed(self):
        """Track selected patient."""
        row = self.table.currentRow()
        if row >= 0:
            self.selected_patient_id = self.table.item(row, 0).data(Qt.UserRole)

    def edit_selected(self):
        """Edit patient name and status."""
        if self.selected_patient_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a patient to edit.")
            return

        patient = self.db.get_patient(self.selected_patient_id)
        if not patient:
            QMessageBox.warning(self, "Error", "Patient not found.")
            return

        # Dialog for new name
        new_name, ok = QInputDialog.getText(
            self,
            "Edit Patient",
            "Patient Name:",
            text=patient["name"]
        )
        if not ok or not new_name.strip():
            return

        # Dialog for new status
        status, ok = QInputDialog.getItem(
            self,
            "Edit Patient",
            "Status:",
            ["under monitoring", "follow up", "done"],
            ["under monitoring", "follow up", "done"].index(patient["status"])
        )
        if not ok:
            return

        try:
            self.db.update_patient(self.selected_patient_id, new_name.strip(), status)
            self.load_data()
            QMessageBox.information(self, "Success", "Patient updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update patient: {str(e)}")

    def delete_selected(self):
        """Delete selected patient and all their scans."""
        if self.selected_patient_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a patient to delete.")
            return

        patient = self.db.get_patient(self.selected_patient_id)
        if not patient:
            QMessageBox.warning(self, "Error", "Patient not found.")
            return

        if QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete all scans for patient '{patient['name']}'?\nThis action cannot be undone."
        ) != QMessageBox.Yes:
            return

        try:
            self.db.delete_patient(self.selected_patient_id)
            self.load_data()
            QMessageBox.information(self, "Deleted", "Patient and all scans deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    def delete_all(self):
        """Delete all patients and scans."""
        if QMessageBox.question(
            self,
            "Confirm Delete All",
            "Delete ALL patients and scans?\nThis action cannot be undone."
        ) != QMessageBox.Yes:
            return

        try:
            self.db.delete_all_scans()
            # Also delete all patients
            patients = self.db.get_all_patients()
            for patient in patients:
                self.db.delete_patient(patient["id"])
            self.load_data()
            QMessageBox.information(self, "Deleted", "All data has been deleted.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete: {str(e)}")

    def open_scan_details(self, index):
        """Open detail view for patient's scans."""
        if self.selected_patient_id is None:
            return

        # Navigate to detail view page with patient data
        self.on_view_scan_details(self.selected_patient_id)
