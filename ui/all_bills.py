from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import sys
from models.database import get_db, Bill

class BillsLoaderThread(QThread):
    data_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            db = next(get_db())
            bills = db.query(Bill).order_by(Bill.date.desc()).all()
            result = []
            for b in bills:
                result.append({
                    "id": b.id,
                    "customer_name": b.customer_name,
                    "customer_phone": b.customer_phone or "N/A",
                    "date": b.date.strftime("%Y-%m-%d %H:%M"),
                    "total_amount": b.total_amount
                })
            db.close()
            self.data_loaded.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))

class AllBills(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("All Bills")
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_layout = QHBoxLayout()
        title = QLabel("🧾 All Bills History")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #2c3e50;")
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton { background-color: #0d6efd; color: white; border-radius: 8px; padding: 8px 15px; font-size: 16px; font-weight: bold; }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Bill ID", "Customer Name", "Phone", "Date", "Total Amount (₹)"])
        
        self.table.setMinimumHeight(400)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(65)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)

        self.table.setStyleSheet("""
        QTableWidget { background-color: #ffffff; border: 1px solid #dcdcdc; border-radius: 12px; font-size: 16px; }
        QHeaderView::section { background-color: #f5f6fa; border: none; border-bottom: 2px solid #e0e0e0; font-weight: bold; font-size: 18px; padding: 12px; }
        QTableWidget::item { padding: 10px; }
        QTableWidget::item:selected { background-color: #007bff; color: white; }
        QTableWidget::item:hover { background-color: #f0f4ff; }
        """)
        
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #ffffff; border-radius: 15px; border: 1px solid #e0e0e0; }")
        card_layout = QVBoxLayout()
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(20, 20, 20, 20)
        
        card_layout.addLayout(header_layout)
        card_layout.addWidget(self.table)
        card.setLayout(card_layout)
        
        main_layout.addWidget(card)
        self.setLayout(main_layout)
        
        self.loading_overlay = QLabel("⏳ Fetching bills...", self)
        self.loading_overlay.setStyleSheet("background-color: rgba(255, 255, 255, 220); font-size: 26px; font-weight: bold; color: #333;")
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.hide()
        
        self.data_thread = BillsLoaderThread()
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

    def update_ui(self, bills):
        self.table.setRowCount(len(bills))
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        for row, bill in enumerate(bills):
            id_item = QTableWidgetItem(f"#{bill['id']}")
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setFont(QFont("Segoe UI", 14, QFont.Bold))
            id_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(bill["customer_name"])
            name_item.setTextAlignment(Qt.AlignCenter)
            name_item.setFont(QFont("Segoe UI", 16))
            self.table.setItem(row, 1, name_item)

            phone_item = QTableWidgetItem(bill["customer_phone"])
            phone_item.setTextAlignment(Qt.AlignCenter)
            phone_item.setFont(QFont("Segoe UI", 14))
            self.table.setItem(row, 2, phone_item)

            date_item = QTableWidgetItem(bill["date"])
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setFont(QFont("Segoe UI", 14))
            self.table.setItem(row, 3, date_item)

            total_item = QTableWidgetItem(f"₹{bill['total_amount']:.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont("Segoe UI", 16, QFont.Bold))
            total_item.setForeground(QColor("#00a86b"))
            self.table.setItem(row, 4, total_item)
            
        self.loading_overlay.hide()

    def handle_error(self, err_msg):
        self.loading_overlay.hide()
        QMessageBox.critical(self, "Database Error", f"Failed to load bills data.\nPlease check your connection and try again.\n\nDetails: {err_msg}")
