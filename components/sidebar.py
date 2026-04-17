 
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class Sidebar(QWidget):
    
    def __init__(self, switch_page):
        super().__init__()
        self.setObjectName("sidebar")

        self.setFixedWidth(200)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignTop)

        buttons = {
            "dashboard": QPushButton("📊 Dashboard"),
            "billing": QPushButton("🧾 Billing"),
            "inventory": QPushButton("📦 Inventory"),
            "reports": QPushButton("📈 Reports"),
        }

        for name, btn in buttons.items():
            btn.clicked.connect(lambda checked, n=name: switch_page(n))
            layout.addWidget(btn)

        self.setLayout(layout)