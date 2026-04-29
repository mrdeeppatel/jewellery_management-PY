from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import sys
from models.database import get_db, Item

class InventoryLoaderThread(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            db = next(get_db())
            items = db.query(Item).all()
            result = []
            for item in items:
                result.append({
                    "id": item.id,
                    "tag_no": item.tag_no or "",
                    "item_code": item.item_code or "",
                    "item_name": item.item_name,
                    "design": item.design or "",
                    "gr_wt": item.gr_wt,
                    "net_wt": item.net_wt,
                    "touch": item.touch,
                    "mrp": item.mrp,
                })
            db.close()
            self.data_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ItemDialog(QDialog):
    def __init__(self, item=None):
        super().__init__()
        self.setWindowTitle("Add Item" if not item else "Edit Item")
        self.resize(550, 450)
        self.setStyleSheet("""
            QDialog { background-color: #f8f9fa; }
            QLabel { font-size: 14px; font-weight: bold; color: #495057; }
            QLineEdit {
                padding: 10px 12px;
                font-size: 14px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #0d6efd; }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # Title
        title = QLabel("📦 Add New Item" if not item else "✏️ Edit Item Details")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #212529;")
        main_layout.addWidget(title)

        # Form Layout (2 columns)
        grid = QGridLayout()
        grid.setSpacing(15)
        grid.setVerticalSpacing(20)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("e.g. KD76")
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Tag No")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Item Name (Required)")
        self.design_input = QLineEdit()
        self.design_input.setPlaceholderText("Design / Style")
        self.gr_wt_input = QLineEdit()
        self.gr_wt_input.setPlaceholderText("0.00")
        self.net_wt_input = QLineEdit()
        self.net_wt_input.setPlaceholderText("0.00")
        self.touch_input = QLineEdit()
        self.touch_input.setPlaceholderText("0.00")
        self.mrp_input = QLineEdit()
        self.mrp_input.setPlaceholderText("0.00")

        if item:
            self.code_input.setText(item.item_code or "")
            self.tag_input.setText(item.tag_no or "")
            self.name_input.setText(item.item_name)
            self.design_input.setText(item.design or "")
            self.gr_wt_input.setText(str(item.gr_wt) if item.gr_wt else "")
            self.net_wt_input.setText(str(item.net_wt) if item.net_wt else "")
            self.touch_input.setText(str(item.touch) if item.touch else "")
            self.mrp_input.setText(str(item.mrp) if item.mrp else "")

        # Row 0 & 1: Code and Gross Wt
        grid.addWidget(QLabel("Item Code"), 0, 0)
        grid.addWidget(self.code_input, 1, 0)
        grid.addWidget(QLabel("Gross Weight (g)"), 0, 1)
        grid.addWidget(self.gr_wt_input, 1, 1)

        # Row 2 & 3: Tag and Net Wt
        grid.addWidget(QLabel("Tag No"), 2, 0)
        grid.addWidget(self.tag_input, 3, 0)
        grid.addWidget(QLabel("Net Weight (g)"), 2, 1)
        grid.addWidget(self.net_wt_input, 3, 1)

        # Row 4 & 5: Name and Touch
        grid.addWidget(QLabel("Item Name <span style='color:red;'>*</span>"), 4, 0)
        grid.addWidget(self.name_input, 5, 0)
        grid.addWidget(QLabel("Touch %"), 4, 1)
        grid.addWidget(self.touch_input, 5, 1)

        # Row 6 & 7: Design and MRP
        grid.addWidget(QLabel("Design"), 6, 0)
        grid.addWidget(self.design_input, 7, 0)
        grid.addWidget(QLabel("MRP (₹)"), 6, 1)
        grid.addWidget(self.mrp_input, 7, 1)

        main_layout.addLayout(grid)

        # Buttons
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: #e9ecef; color: #495057; }
            QPushButton:hover { background-color: #ced4da; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.save_btn = QPushButton("Save Item")
        self.save_btn.clicked.connect(self.accept)

        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        main_layout.addStretch()
        main_layout.addLayout(btn_layout)

    def get_data(self):
        return {
            "item_code": self.code_input.text().strip() or None,
            "tag_no": self.tag_input.text().strip() or None,
            "item_name": self.name_input.text().strip(),
            "design": self.design_input.text().strip() or None,
            "gr_wt": float(self.gr_wt_input.text() or 0) or None,
            "net_wt": float(self.net_wt_input.text() or 0) or None,
            "touch": float(self.touch_input.text() or 0) or None,
            "mrp": float(self.mrp_input.text() or 0) or None,
        }

class Inventory(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inventory Dashboard")
        self.resize(900, 550)

        # Store all items for search filtering
        self.all_items = []

        # 🔥 Main Layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 🔥 Header
        header_layout = QHBoxLayout()
        title = QLabel("📦 Today's Stock Overview")
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
        """)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd; color: white; border-radius: 8px; padding: 8px 15px; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        # 🔍 Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search by Item Code, Name, or Category...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 16px;
                background-color: #f8f9fa;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #0d6efd;
                background-color: #ffffff;
            }
        """)
        # Debounce search: filter after user stops typing for 300ms
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)
        self.search_timer.timeout.connect(self.filter_items)
        self.search_input.textChanged.connect(lambda: self.search_timer.start())

        search_layout.addWidget(self.search_input)

        # 🔥 Buttons
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Item")
        self.add_btn.setStyleSheet("background-color: #00c853; color: white; border-radius: 5px; padding: 10px;")
        self.edit_btn = QPushButton("Edit Item")
        self.edit_btn.setStyleSheet("background-color: #007bff; color: white; border-radius: 5px; padding: 10px;")
        self.del_btn = QPushButton("Delete Item")
        self.del_btn.setStyleSheet("background-color: #ff4d4d; color: white; border-radius: 5px; padding: 10px;")
        
        self.add_btn.clicked.connect(self.add_item)
        self.edit_btn.clicked.connect(self.edit_item)
        self.del_btn.clicked.connect(self.delete_item)

        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()

        # 🔥 Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # +1 for hidden ID
        self.table.setHorizontalHeaderLabels([
            "Tag No", "Item Code", "Item Name", "Design", "Gr Wt", "Net Wt", "Touch %", "MRP", "ID"
        ])
        self.table.setColumnHidden(8, True)

        # 🔥 Table UI Improvements
        self.table.setMinimumHeight(400)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(65)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)

        # 🔥 Styling
        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #ffffff;
            border: 1px solid #dcdcdc;
            border-radius: 12px;
            font-size: 16px;
        }

        QHeaderView::section {
            background-color: #f5f6fa;
            border: none;
            border-bottom: 2px solid #e0e0e0;
            font-weight: bold;
            font-size: 18px;
            padding: 12px;
        }

        QTableWidget::item {
            padding: 10px;
        }

        QTableWidget::item:selected {
            background-color: #007bff;
            color: white;
        }

        QTableWidget::item:hover {
            background-color: #f0f4ff;
        }
        """)

        # 🔥 Card Container
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
        """)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)

        card_layout.addLayout(header_layout)
        card_layout.addLayout(search_layout)
        card_layout.addLayout(btn_layout)
        card_layout.addWidget(self.table)

        card.setLayout(card_layout)

        # 🔥 Add to main layout
        main_layout.addWidget(card)
        self.setLayout(main_layout)

        # Loading Overlay
        self.loading_overlay = QLabel("⏳ Fetching inventory...", self)
        self.loading_overlay.setStyleSheet("""
            background-color: rgba(255, 255, 255, 220); 
            font-size: 26px; 
            font-weight: bold; 
            color: #333;
        """)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.hide()

        # Setup Thread
        self.data_thread = InventoryLoaderThread()
        self.data_thread.data_loaded.connect(self.on_data_loaded)
        self.data_thread.error_occurred.connect(self.handle_error)

    def resizeEvent(self, event):
        self.loading_overlay.resize(self.size())
        super().resizeEvent(event)

    def showEvent(self, event):
        self.refresh_data()
        super().showEvent(event)

    def refresh_data(self):
        self.loading_overlay.show()
        if not self.data_thread.isRunning():
            self.data_thread.start()

    def on_data_loaded(self, items):
        """Store items and apply current search filter."""
        self.all_items = items
        self.filter_items()
        self.loading_overlay.hide()

    def filter_items(self):
        """Filter the stored items based on search text and update the table."""
        query = self.search_input.text().strip().lower()
        if query:
            filtered = [
                item for item in self.all_items
                if query in (item["item_code"] or "").lower()
                or query in item["item_name"].lower()
                or query in (item["tag_no"] or "").lower()
                or query in (item["design"] or "").lower()
            ]
        else:
            filtered = self.all_items
        self.update_ui(filtered)

    def update_ui(self, items):
        self.table.setRowCount(len(items))
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        for row, item in enumerate(items):
            def _cell(text, bold=False, size=14):
                wi = QTableWidgetItem(str(text) if text else "-")
                wi.setTextAlignment(Qt.AlignCenter)
                wi.setFont(QFont("Segoe UI", size, QFont.Bold if bold else QFont.Normal))
                wi.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                return wi

            self.table.setItem(row, 0, _cell(item["tag_no"]))
            self.table.setItem(row, 1, _cell(item["item_code"], bold=True))
            self.table.setItem(row, 2, _cell(item["item_name"], size=16))
            self.table.setItem(row, 3, _cell(item["design"]))
            self.table.setItem(row, 4, _cell(f"{item['gr_wt']} g" if item["gr_wt"] else "-"))
            self.table.setItem(row, 5, _cell(f"{item['net_wt']} g" if item["net_wt"] else "-"))
            self.table.setItem(row, 6, _cell(f"{item['touch']}%" if item["touch"] else "-"))
            self.table.setItem(row, 7, _cell(f"{item['mrp']}" if item["mrp"] else "-"))

            id_item = QTableWidgetItem(str(item["id"]))
            self.table.setItem(row, 8, id_item)
                
    def handle_error(self, err_msg):
        self.loading_overlay.hide()
        QMessageBox.critical(self, "Database Error", f"Failed to load inventory data.\nPlease check your connection and try again.\n\nDetails: {err_msg}")

    def add_item(self):
        dialog = ItemDialog()
        if dialog.exec_():
            data = dialog.get_data()
            if not data["item_name"]:
                QMessageBox.warning(self, "Error", "Item name is required")
                return
            db = next(get_db())
            new_item = Item(**data)
            db.add(new_item)
            db.commit()
            self.refresh_data()

    def edit_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Item", "Please select an item to edit")
            return
        
        item_id = int(self.table.item(row, 7).text())
        db = next(get_db())
        item = db.query(Item).get(item_id)
        if not item: return

        dialog = ItemDialog(item)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["item_name"]: return
            item.item_code = data["item_code"]
            item.tag_no = data["tag_no"]
            item.item_name = data["item_name"]
            item.design = data["design"]
            item.gr_wt = data["gr_wt"]
            item.net_wt = data["net_wt"]
            item.touch = data["touch"]
            item.mrp = data["mrp"]
            db.commit()
            self.refresh_data()

    def delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Item", "Please select an item to delete")
            return

        item_id = int(self.table.item(row, 7).text())
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this item?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db = next(get_db())
            item = db.query(Item).get(item_id)
            if item:
                db.delete(item)
                db.commit()
                self.refresh_data()

# 🔥 Run App
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Inventory()
    window.show()
    sys.exit(app.exec_())