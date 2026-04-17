from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
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
                    "name": item.name,
                    "category": item.category,
                    "weight": item.weight,
                    "stock_quantity": item.stock_quantity
                })
            db.close()
            self.data_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ItemDialog(QDialog):
    def __init__(self, item=None):
        super().__init__()
        self.setWindowTitle("Add Item" if not item else "Edit Item")
        self.setFixedSize(300, 300)
        self.layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Category")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Weight (g)")
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Stock Qty")

        if item:
            self.name_input.setText(item.name)
            self.cat_input.setText(item.category or "")
            self.weight_input.setText(str(item.weight) if item.weight else "")
            self.stock_input.setText(str(item.stock_quantity))

        self.layout.addWidget(QLabel("Item Name"))
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(QLabel("Category"))
        self.layout.addWidget(self.cat_input)
        self.layout.addWidget(QLabel("Weight (g)"))
        self.layout.addWidget(self.weight_input)
        self.layout.addWidget(QLabel("Stock Quantity"))
        self.layout.addWidget(self.stock_input)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.save_btn)
        self.setLayout(self.layout)

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "category": self.cat_input.text().strip(),
            "weight": float(self.weight_input.text() or 0),
            "stock_quantity": int(self.stock_input.text() or 0)
        }

class Inventory(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inventory Dashboard")
        self.resize(900, 550)

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
        self.table.setColumnCount(6) # +1 for hidden ID
        self.table.setHorizontalHeaderLabels([
            "Sr No", "Item Name", "Category", "Weight", "Stock Qty", "ID"
        ])
        self.table.setColumnHidden(5, True)

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
        self.data_thread.data_loaded.connect(self.update_ui)
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

    def update_ui(self, items):
        self.table.setRowCount(len(items))
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        for row, item in enumerate(items):
            index_item = QTableWidgetItem(str(row + 1))
            index_item.setTextAlignment(Qt.AlignCenter)
            index_item.setFont(QFont("Segoe UI", 14))
            index_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, index_item)

            name_item = QTableWidgetItem(item["name"])
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFont(QFont("Segoe UI", 16))
            self.table.setItem(row, 1, name_item)

            cat_item = QTableWidgetItem(item["category"] or "-")
            cat_item.setTextAlignment(Qt.AlignCenter)
            cat_item.setFont(QFont("Segoe UI", 14))
            self.table.setItem(row, 2, cat_item)

            weight_str = f"{item['weight']} g" if item["weight"] else "-"
            weight_item = QTableWidgetItem(weight_str)
            weight_item.setTextAlignment(Qt.AlignCenter)
            weight_item.setFont(QFont("Segoe UI", 14))
            self.table.setItem(row, 3, weight_item)

            stock_item = QTableWidgetItem(str(item["stock_quantity"]))
            stock_item.setTextAlignment(Qt.AlignCenter)
            stock_item.setFont(QFont("Segoe UI", 16, QFont.Bold))
            self.table.setItem(row, 4, stock_item)
            
            id_item = QTableWidgetItem(str(item["id"]))
            self.table.setItem(row, 5, id_item)

            if item["stock_quantity"] < 5:
                stock_item.setBackground(QColor("#ff4d4d"))
                stock_item.setForeground(QColor("white"))
            elif item["stock_quantity"] < 10:
                stock_item.setBackground(QColor("#ffd166"))
            else:
                stock_item.setBackground(QColor("#00c853"))
                stock_item.setForeground(QColor("white"))
                
        self.loading_overlay.hide()

    def handle_error(self, err_msg):
        self.loading_overlay.hide()
        QMessageBox.critical(self, "Database Error", f"Failed to load inventory data.\nPlease check your connection and try again.\n\nDetails: {err_msg}")

    def add_item(self):
        dialog = ItemDialog()
        if dialog.exec_():
            data = dialog.get_data()
            if not data["name"]:
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
        
        item_id = int(self.table.item(row, 5).text())
        db = next(get_db())
        item = db.query(Item).get(item_id)
        if not item: return

        dialog = ItemDialog(item)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["name"]: return
            item.name = data["name"]
            item.category = data["category"]
            item.weight = data["weight"]
            item.stock_quantity = data["stock_quantity"]
            db.commit()
            self.refresh_data()

    def delete_item(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Select Item", "Please select an item to delete")
            return

        item_id = int(self.table.item(row, 5).text())
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