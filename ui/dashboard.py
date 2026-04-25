from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from models.database import get_db, Bill, Item
from sqlalchemy import func
from datetime import datetime
import time

class DataLoaderThread(QThread):
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            db = next(get_db())
            today = datetime.utcnow().date()
            
            bills = db.query(Bill).all()
            bills_today = [b for b in bills if b.date.date() == today]
            sales_today = sum(b.total_amount for b in bills_today)
            bills_count = len(bills_today)

            total_products = db.query(Item).count()
            customers_count = len(set(b.customer_name for b in bills))

            recent_bills = db.query(Bill).order_by(Bill.date.desc()).limit(4).all()
            activity_items = [f"Sold to {b.customer_name} - ₹{b.total_amount:,.2f}" for b in recent_bills]
            if not activity_items:
                activity_items = ["No recent activity"]

            low_stock = []  # stock_quantity no longer tracked in new schema
            alert_items = ["Stock alerts not available (no stock_quantity field)"]

            db.close()
            
            self.data_loaded.emit({
                "sales_today": f"₹{sales_today:,.2f}",
                "bills_count": str(bills_count),
                "total_products": str(total_products),
                "customers_count": str(customers_count),
                "activity_items": activity_items,
                "alert_items": alert_items
            })
        except Exception as e:
            self.error_occurred.emit(str(e))

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        # 🔥 APPLY FULL CSS HERE
        self.setStyleSheet("""
        QWidget {
            background-color: #f5f6fa;
            font-family: Segoe UI;
            font-size: 18px;
        }

        QLabel#title {
            font-size: 32px;
            font-weight: bold;
            color: #111;
        }

        QLabel#sectionTitle {
            font-size: 18px;
            color: #555;
        }

        QLabel#highlight {
            font-size: 30px;
            font-weight: bold;
            color: #00a86b;
        }

        /* 🔥 CARD BORDER */
        QFrame#card {
            background-color: #ffffff;
            border: 2px solid #dcdcdc;
            border-radius: 16px;
        }

        QFrame#card:hover {
            border: 2px solid #a0a0a0;
            background-color: #fcfcff;
        }

        /* Divider */
        QFrame#divider {
            background-color: #dcdcdc;
            min-height: 1px;
            max-height: 1px;
        }

        /* List */
        QListWidget {
            background-color: #ffffff;
            border: 1.5px solid #dcdcdc;
            border-radius: 10px;
            padding: 8px;
        }
        """)

        # ================= MAIN LAYOUT =================
        main_layout = QVBoxLayout()
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # 🔥 Header
        header_layout = QHBoxLayout()
        title = QLabel("📊 Dashboard Overview")
        title.setObjectName("title")

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

        # ================= CARDS =================
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        def create_card(title_text):
            card = QFrame()
            card.setObjectName("card")
            card.setMinimumHeight(140)

            layout = QVBoxLayout()
            layout.setSpacing(8)
            layout.setContentsMargins(15, 15, 15, 15)

            card_title = QLabel(title_text)
            card_title.setObjectName("sectionTitle")

            divider = QFrame()
            divider.setObjectName("divider")

            value_label = QLabel("...")
            value_label.setObjectName("highlight")

            layout.addWidget(card_title)
            layout.addWidget(divider)
            layout.addWidget(value_label)
            layout.addStretch()

            card.setLayout(layout)
            return card, value_label

        card1, self.sales_label = create_card("💰 Today Sales")
        card2, self.bills_label = create_card("🧾 Bills Today")
        card3, self.products_label = create_card("📦 Total Products")
        card4, self.customers_label = create_card("👥 Customers")

        cards_layout.addWidget(card1)
        cards_layout.addWidget(card2)
        cards_layout.addWidget(card3)
        cards_layout.addWidget(card4)

        # ================= BOTTOM =================
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)

        def create_section(title_text):
            section = QFrame()
            section.setObjectName("card")

            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(15, 15, 15, 15)

            title = QLabel(title_text)
            title.setObjectName("sectionTitle")

            divider = QFrame()
            divider.setObjectName("divider")

            list_widget = QListWidget()

            layout.addWidget(title)
            layout.addWidget(divider)
            layout.addWidget(list_widget)

            section.setLayout(layout)
            return section, list_widget

        activity_widget, self.activity_list = create_section("🕒 Recent Activity")
        alert_widget, self.alert_list = create_section("⚠ Stock Alerts")

        bottom_layout.addWidget(activity_widget)
        bottom_layout.addWidget(alert_widget)

        # ================= FINAL =================
        main_layout.addLayout(header_layout)
        main_layout.addLayout(cards_layout)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # Loading Overlay
        self.loading_overlay = QLabel("⏳ Fetching live data...", self)
        self.loading_overlay.setStyleSheet("""
            background-color: rgba(255, 255, 255, 220); 
            font-size: 26px; 
            font-weight: bold; 
            color: #333;
        """)
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.hide()

        # Setup Thread
        self.data_thread = DataLoaderThread()
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

    def update_ui(self, data):
        self.sales_label.setText(data["sales_today"])
        self.bills_label.setText(data["bills_count"])
        self.products_label.setText(data["total_products"])
        self.customers_label.setText(data["customers_count"])

        self.activity_list.clear()
        self.activity_list.addItems(data["activity_items"])

        self.alert_list.clear()
        self.alert_list.addItems(data["alert_items"])

        self.loading_overlay.hide()

    def handle_error(self, err_msg):
        self.loading_overlay.hide()
        QMessageBox.critical(self, "Database Error", f"Failed to load dashboard data.\nPlease check your connection and try again.\n\nDetails: {err_msg}")