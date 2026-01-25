
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QInputDialog

class HistoryPage(QWidget):
    def __init__(self, on_back, db):
        super().__init__()
        self.db = db
        self.on_back = on_back

        layout = QVBoxLayout(self)
        top = QHBoxLayout()

        back = QPushButton("Back")
        back.clicked.connect(on_back)
        top.addWidget(back)

        edit = QPushButton("Edit Name")
        edit.clicked.connect(self.edit)
        top.addWidget(edit)

        delete = QPushButton("Delete Selected")
        delete.clicked.connect(self.delete)
        top.addWidget(delete)

        delete_all = QPushButton("Delete All")
        delete_all.clicked.connect(db.delete_all)
        top.addWidget(delete_all)

        layout.addLayout(top)

        self.table = QTableWidget(0,4)
        self.table.setHorizontalHeaderLabels(["ID","Name","Severity","Date"])
        layout.addWidget(self.table)

    def load_data(self):
        self.table.setRowCount(0)
        for r in self.db.list_scans():
            row = self.table.rowCount()
            self.table.insertRow(row)
            for i,v in enumerate(r[:4]):
                self.table.setItem(row,i,QTableWidgetItem(str(v)))

    def edit(self):
        row = self.table.currentRow()
        if row<0: return
        scan_id = int(self.table.item(row,0).text())
        name,ok = QInputDialog.getText(self,"Edit","New name")
        if ok:
            self.db.update_name(scan_id,name)
            self.load_data()

    def delete(self):
        row = self.table.currentRow()
        if row<0: return
        scan_id = int(self.table.item(row,0).text())
        self.db.delete_scan(scan_id)
        self.load_data()
