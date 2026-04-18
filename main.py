import sys
from components.sidebar import Sidebar
from ui.dashboard import Dashboard
from ui.billing import Billing
from ui.live_billing import LiveBillingPage
from ui.item_billing import ItemBillingPage
from ui.inventory import Inventory
from ui.reports import Reports
from ui.all_bills import AllBills
from ui.login import LoginWindow
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget
)
from PyQt5.QtCore import Qt

# ------------------ NAVBAR ------------------

class Navbar(QWidget):
    def __init__(self, pages, switch_page):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        self.buttons = {}

        for index, key in enumerate(pages.keys()):
            btn = QPushButton(key.capitalize())
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)

            btn.clicked.connect(lambda checked, i=index: switch_page(i))

            layout.addWidget(btn)
            self.buttons[key] = btn

        layout.addStretch()
        self.setLayout(layout)


# ------------------ MAIN WINDOW ------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("💎 Jewellery Management Software")
        self.setGeometry(100, 100, 1000, 600)

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        # 🔥 Pages dictionary
        self.pages = {
            "dashboard": Dashboard(),
            "billing": Billing(),
            "live billing": LiveBillingPage(),
            "item billing": ItemBillingPage(),
            "inventory": Inventory(),
            "all bills": AllBills(),
            "reports": Reports()
        }

        # 🔥 Stacked Widget (BEST PRACTICE)
        self.stack = QStackedWidget()
        for page in self.pages.values():
            self.stack.addWidget(page)

        # 🔥 Navbar
        self.navbar = Navbar(self.pages, self.switch_page)

        # Layout structure
        main_layout.addWidget(self.navbar)
        main_layout.addWidget(self.stack)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # 🔥 Switch page using index (fast & clean)
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)


# ------------------ RUN APP ------------------

app = QApplication(sys.argv)

# Optional styling
app.setStyleSheet("""
QWidget {
    background-color: #f8f9fa;
    font-size: 16px;
}

QPushButton {
    background-color: transparent;
    border: none;
    padding: 8px 15px;
}

QPushButton:hover {
    background-color: #e9ecef;
    border-radius: 6px;
}

QLabel {
    font-size: 24px;
    font-weight: bold;
}
""")

login_window = LoginWindow()
main_window = MainWindow()

def on_login_success(user):
    print(f"Logged in as: {user.username} (Role: {user.role})")
    main_window.current_user = user # Keep track of who is logged in
    main_window.show()

login_window.login_successful.connect(on_login_success)
login_window.show()

sys.exit(app.exec_())