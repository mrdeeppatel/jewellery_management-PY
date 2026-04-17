from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt

class Navbar(QWidget):
    def __init__(self, pages, switch_page):
        super().__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 🔥 Auto-create buttons from pages dict
        for key in pages.keys():
            btn = QPushButton(key.capitalize())  # dashboard → Dashboard
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(40)

            btn.clicked.connect(lambda checked, k=key: switch_page(k))

            layout.addWidget(btn)

        layout.addStretch()

        self.setLayout(layout)