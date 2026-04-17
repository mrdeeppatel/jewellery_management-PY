import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from models.database import get_db, Item, Bill, BillItem

class Billing(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Jewellery Billing System")
        self.setGeometry(200, 100, 1000, 550)

        self.total_amount = 0
        self.items = []

        self.setStyleSheet(self.get_styles())

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ================= LEFT PANEL =================
        left_card = QFrame()
        left_card.setObjectName("card")
        left_layout = QVBoxLayout()

        title = QLabel("🧾 Billing Panel")
        title.setObjectName("title")

        self.customer_name = QLineEdit()
        self.customer_name.setPlaceholderText("Customer Name")
        
        self.customer_phone = QLineEdit()
        self.customer_phone.setPlaceholderText("Customer Phone")

        self.product = QComboBox()
        
        db = next(get_db())
        items = db.query(Item).all()
        item_names = [i.name for i in items]
        if not item_names:
            item_names = ["No items in inventory"]
        self.product.addItems(item_names)

        self.weight = QLineEdit()
        self.weight.setPlaceholderText("Enter weight (grams)")

        self.price = QLineEdit()
        self.price.setPlaceholderText("Enter price per gram")

        self.total_label = QLabel("Total: ₹0.00")
        self.total_label.setObjectName("total")

        add_btn = QPushButton("Add to Bill")
        add_btn.setObjectName("primary")
        add_btn.clicked.connect(self.calculate)

        left_layout.addWidget(title)
        left_layout.addSpacing(10)
        left_layout.addWidget(QLabel("Customer Name"))
        left_layout.addWidget(self.customer_name)
        left_layout.addWidget(QLabel("Customer Phone (Optional)"))
        left_layout.addWidget(self.customer_phone)
        left_layout.addSpacing(10)
        left_layout.addWidget(QLabel("Product"))
        left_layout.addWidget(self.product)
        left_layout.addWidget(QLabel("Weight"))
        left_layout.addWidget(self.weight)
        left_layout.addWidget(QLabel("Price per gram"))
        left_layout.addWidget(self.price)
        left_layout.addSpacing(10)
        left_layout.addWidget(add_btn)
        left_layout.addWidget(self.total_label)
        left_layout.addStretch()

        left_card.setLayout(left_layout)

        # ================= RIGHT PANEL =================
        right_card = QFrame()
        right_card.setObjectName("card")
        right_layout = QVBoxLayout()

        summary_title = QLabel("Bill Summary")
        summary_title.setObjectName("section")

        # TABLE
        self.bill_table = QTableWidget()
        self.bill_table.setColumnCount(4)
        self.bill_table.setHorizontalHeaderLabels(
            ["Product", "Weight (g)", "Price", "Total"]
        )

        self.bill_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bill_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.bill_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self.remove_item)

        self.grand_total = QLabel("Grand Total: ₹0.00")
        self.grand_total.setObjectName("grand")

        self.checkout_btn = QPushButton("Save & Complete Bill")
        self.checkout_btn.setObjectName("primary")
        self.checkout_btn.clicked.connect(self.checkout)

        right_layout.addWidget(summary_title)
        right_layout.addWidget(self.bill_table)
        right_layout.addWidget(remove_btn)
        right_layout.addWidget(self.grand_total)
        right_layout.addWidget(self.checkout_btn)

        right_card.setLayout(right_layout)

        # ================= MAIN =================
        main_layout.addWidget(left_card, 2)
        main_layout.addWidget(right_card, 3)

        self.setLayout(main_layout)

    # ================= LOGIC =================
    def calculate(self):
        try:
            w = float(self.weight.text())
            p = float(self.price.text())

            if w <= 0 or p <= 0:
                raise ValueError

            total = w * p

            self.total_label.setText(f"Total: ₹{total:.2f}")

            row = self.bill_table.rowCount()
            self.bill_table.insertRow(row)

            self.bill_table.setItem(row, 0, QTableWidgetItem(self.product.currentText()))
            self.bill_table.setItem(row, 1, QTableWidgetItem(f"{w}"))
            self.bill_table.setItem(row, 2, QTableWidgetItem(f"₹{p}"))
            self.bill_table.setItem(row, 3, QTableWidgetItem(f"₹{total:.2f}"))

            self.items.append({
                "name": self.product.currentText(),
                "weight": w,
                "price": p,
                "total": total
            })
            self.total_amount += total

            self.grand_total.setText(f"Grand Total: ₹{self.total_amount:.2f}")

            self.weight.clear()
            self.price.clear()

        except ValueError:
            self.total_label.setText("⚠️ Enter valid numbers")

    def remove_item(self):
        row = self.bill_table.currentRow()

        if row >= 0:
            self.total_amount -= self.items[row]["total"]
            self.items.pop(row)

            self.bill_table.removeRow(row)
            self.grand_total.setText(f"Grand Total: ₹{self.total_amount:.2f}")

    def checkout(self):
        customer = self.customer_name.text().strip()
        if not customer:
            QMessageBox.warning(self, "Error", "Please enter a customer name")
            return
        if not self.items:
            QMessageBox.warning(self, "Error", "No items in the bill")
            return

        db = next(get_db())
        try:
            new_bill = Bill(
                customer_name=customer, 
                customer_phone=self.customer_phone.text().strip(), 
                total_amount=self.total_amount, 
                is_estimate=False
            )
            db.add(new_bill)
            db.commit()

            for item in self.items:
                db_item = db.query(Item).filter_by(name=item["name"]).first()
                if db_item:
                    # Deduct stock quantity
                    if db_item.stock_quantity > 0:
                        db_item.stock_quantity -= 1
                    b_item = BillItem(bill_id=new_bill.id, item_id=db_item.id, quantity=1, price=item["total"])
                    db.add(b_item)
                    
            db.commit()
            QMessageBox.information(self, "Success", "Bill saved to database successfully!")

            # Reset form
            self.items.clear()
            self.total_amount = 0
            self.bill_table.setRowCount(0)
            self.grand_total.setText("Grand Total: ₹0.00")
            self.customer_name.clear()
            self.customer_phone.clear()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save bill: {str(e)}")

    # ================= STYLES =================
    def get_styles(self):
        return """
        QWidget {
            background-color: #f5f6fa;
            color: #2d3436;
            font-family: Segoe UI;
            font-size: 16px;
        }

        QFrame#card {
            background-color: white;
            border-radius: 12px;
            padding: 18px;
            border: 1px solid #ddd;
        }

        QLabel#title {
            font-size: 26px;
            font-weight: bold;
            color: #d4a017;
        }

        QLabel#section {
            font-size: 20px;
            font-weight: bold;
            color: #0984e3;
        }

        QLineEdit, QComboBox {
            background-color: #ffffff;
            border: 1px solid #ccc;
            padding: 10px;
            border-radius: 8px;
            font-size: 15px;
        }

        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #0984e3;
        }

        QPushButton {
            border-radius: 8px;
            padding: 12px;
            font-size: 15px;
        }

        QPushButton#primary {
            background-color: #00b894;
            color: white;
            font-weight: bold;
        }

        QPushButton#primary:hover {
            background-color: #00cec9;
        }

        QPushButton#danger {
            background-color: #d63031;
            color: white;
        }

        QTableWidget {
            background-color: #ffffff;
            border-radius: 8px;
            border: 1px solid #ccc;
            gridline-color: #ddd;
        }

        QHeaderView::section {
            background-color: #f1f2f6;
            padding: 8px;
            border: none;
            font-weight: bold;
        }

        QTableWidget::item {
            padding: 6px;
        }

        QLabel#total {
            font-size: 20px;
            color: #00b894;
            font-weight: bold;
        }

        QLabel#grand {
            font-size: 22px;
            color: #d4a017;
            font-weight: bold;
        }
        """

# ================= RUN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = Billing()
    window.show()

    sys.exit(app.exec_())