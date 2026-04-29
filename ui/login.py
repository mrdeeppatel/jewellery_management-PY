import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from models.database import get_db, User


class _LoginNavFilter(QWidget):
    """Event filter for billing-style keyboard navigation on the login form."""

    def __init__(self, parent, tab_order):
        super().__init__(parent)
        self._tab_order = tab_order
        self._parent = parent

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            modifiers = event.modifiers()

            # ── ENTER key ──
            if key in (Qt.Key_Return, Qt.Key_Enter):
                if isinstance(obj, QPushButton):
                    obj.click()
                    return True
                if isinstance(obj, QLineEdit):
                    self._move_focus(obj, forward=True)
                    return True

            # ── TAB ──
            if key == Qt.Key_Tab and not (modifiers & Qt.ShiftModifier):
                if obj in self._tab_order:
                    self._move_focus(obj, forward=True)
                    return True

            # ── Shift+TAB ──
            if key == Qt.Key_Backtab or (key == Qt.Key_Tab and (modifiers & Qt.ShiftModifier)):
                if obj in self._tab_order:
                    self._move_focus(obj, forward=False)
                    return True

        # ── Auto-select-all on focus-in ──
        if event.type() == QEvent.FocusIn and isinstance(obj, QLineEdit):
            QTimer.singleShot(0, obj.selectAll)

        return False

    def _move_focus(self, current, forward=True):
        if current not in self._tab_order:
            return
        idx = self._tab_order.index(current)
        step = 1 if forward else -1
        total = len(self._tab_order)
        for _ in range(total):
            idx = (idx + step) % total
            target = self._tab_order[idx]
            if not target.isEnabled() or not target.isVisible():
                continue
            if isinstance(target, QLineEdit) and target.isReadOnly():
                continue
            target.setFocus()
            return


class LoginWindow(QWidget):
    login_successful = pyqtSignal(object)  # Emits the user object on success

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Jewellery Management")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)

        self.login_btn = QPushButton("Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                margin-top: 10px;
                border: 2px solid transparent;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:focus {
                background-color: #0b5ed7;
                border: 2px solid #86b7fe;
                outline: none;
            }
        """)
        self.login_btn.clicked.connect(self.handle_login)

        layout.addWidget(title)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

        # ── Keyboard Navigation ──
        self._tab_order = [self.username_input, self.password_input, self.login_btn]
        self._nav_filter = _LoginNavFilter(self, self._tab_order)
        for w in self._tab_order:
            w.setFocusPolicy(Qt.StrongFocus)
            w.installEventFilter(self._nav_filter)

        # Auto-focus username on open
        QTimer.singleShot(100, self.username_input.setFocus)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        db = next(get_db())
        user = db.query(User).filter(User.username == username).first()

        # Note: We are using a simple string match for passwords in this test phase.
        if user and user.password_hash == password:
            self.login_successful.emit(user)
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
