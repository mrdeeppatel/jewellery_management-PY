from PyQt5.QtWidgets import *
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sys
from models.database import get_db, Bill
from datetime import datetime


class Reports(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reports")
        self.resize(700, 400)

        # 🔥 Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

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
        card_layout.setSpacing(20)
        card_layout.setContentsMargins(30, 30, 30, 30)

        # 🔥 Title
        title = QLabel("📈 Reports Dashboard")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #2c3e50;
        """)

        # 🔥 Sales Info Card
        sales_box = QFrame()
        sales_box.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        sales_layout = QVBoxLayout()

        sales_label = QLabel("Daily Sales")
        sales_label.setFont(QFont("Segoe UI", 16))
        sales_label.setAlignment(Qt.AlignCenter)

        db = next(get_db())
        today = datetime.utcnow().date()
        bills = db.query(Bill).all()
        sales_today = sum(b.total_amount for b in bills if b.date.date() == today)

        amount_label = QLabel(f"₹ {sales_today:,.2f}")
        amount_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        amount_label.setAlignment(Qt.AlignCenter)
        amount_label.setStyleSheet("color: #28a745;")

        sales_layout.addWidget(sales_label)
        sales_layout.addWidget(amount_label)
        sales_box.setLayout(sales_layout)

        export_btn = QPushButton("⬇ Export to Excel")
        export_btn.setCursor(Qt.PointingHandCursor)

        export_btn.setStyleSheet("""
        QPushButton {
            background-color: #007bff;
            color: white;
            font-size: 16px;
            font-weight: 600;
            border-radius: 10px;
            padding: 10px 20px;
        }

        QPushButton:hover {
            background-color: #0056b3;
        }
        """)

        # Optional: control width instead of height
        export_btn.setMinimumHeight(45)
        # 🔥 Add Widgets
        card_layout.addWidget(title)
        card_layout.addWidget(sales_box)
        card_layout.addWidget(export_btn)

        card.setLayout(card_layout)
        main_layout.addWidget(card)

        self.setLayout(main_layout)


# 🔥 Run standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Reports()
    window.show()
    sys.exit(app.exec_())