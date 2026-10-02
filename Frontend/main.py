import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox
)
from PySide6.QtCore import Qt

from dashboard import Dashboard
from login import AssemblyBackendError, authenticate, create_master_password, first_run


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.dashboard = None
        self.setup_mode = first_run()

        self.setWindowTitle("SecureVault")
        self.setFixedSize(450, 500)

        self.create_ui()

    def create_ui(self):

        title = QLabel("🔐 SecureVault")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("8086 Assembly Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(
            "Create master password" if self.setup_mode else "Enter master password"
        )
        self.password_input.setEchoMode(QLineEdit.Password)

        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm master password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setVisible(self.setup_mode)

        unlock_button = QPushButton("Unlock Vault")

        if self.setup_mode:
            unlock_button.setText("Create Vault Password")

        unlock_button.clicked.connect(self.login)

        layout = QVBoxLayout()

        layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_input)
        layout.addWidget(unlock_button)

        layout.addStretch()

        self.setLayout(layout)

    def login(self):

        password = self.password_input.text()

        if password == "":
            QMessageBox.warning(
                self,
                "Error",
                "Please enter your master password."
            )
            return

        try:
            if self.setup_mode:
                if not create_master_password(password, self.confirm_input.text()):
                    QMessageBox.warning(self, "Error", "Passwords do not match.")
                    return
                self.setup_mode = False
                authenticate(password)
            else:
                authenticate(password)
        except Exception as error:
            QMessageBox.critical(self, "Vault Error", str(error))
            return

        try:
            self.dashboard = Dashboard(on_lock=self.lock_vault)
        except Exception as error:
            QMessageBox.critical(self, "Vault Error", str(error))
            from vault import lock_vault

            lock_vault()
            return
        self.dashboard.show()
        self.hide()

    def lock_vault(self):
        from vault import lock_vault

        lock_vault()
        if self.dashboard is not None:
            self.dashboard.close()
            self.dashboard = None
        self.password_input.clear()
        self.confirm_input.clear()
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())