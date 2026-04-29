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
    QLabel, QStackedWidget, QMessageBox
)
from PyQt5.QtCore import Qt

# ------------------ NAVBAR ------------------

class Navbar(QWidget):
    def __init__(self, pages, switch_page, logout_callback):
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
        
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedHeight(40)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.logout_btn.clicked.connect(logout_callback)
        layout.addWidget(self.logout_btn)
        
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
        self.navbar = Navbar(self.pages, self.switch_page, self.handle_logout)

        # Layout structure
        main_layout.addWidget(self.navbar)
        main_layout.addWidget(self.stack)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    # 🔥 Switch page using index (fast & clean)
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)

    def handle_logout(self):
        reply = QMessageBox.question(
            self, "Confirm Logout", "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.current_user = None
            self.hide()
            
            # Reset login inputs
            login_window.username_input.clear()
            login_window.password_input.clear()
            login_window.username_input.setFocus()
            login_window.show()

    def apply_role_permissions(self):
        if not hasattr(self, "current_user") or not self.current_user:
            return
        
        username = self.current_user.username.lower() if self.current_user.username else ""
        role = self.current_user.role.lower() if self.current_user.role else ""
        
        is_master = ("master" in username or "master" in role or "owner" in role or "owner" in username)
        is_staff = ("staf" in username or "staf" in role)
        
        for key, btn in self.navbar.buttons.items():
            if is_master:
                btn.setVisible(True)
                btn.setEnabled(True)
            elif is_staff:
                if key == "live billing":
                    btn.setVisible(True)
                    btn.setEnabled(True)
                else:
                    btn.setVisible(False)
            else:
                btn.setVisible(False)
                
        if is_staff and not is_master:
            if "live billing" in self.pages:
                live_billing_index = list(self.pages.keys()).index("live billing")
                self.switch_page(live_billing_index)


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
    main_window.apply_role_permissions()
    main_window.show()

login_window.login_successful.connect(on_login_success)
login_window.show()

sys.exit(app.exec_())