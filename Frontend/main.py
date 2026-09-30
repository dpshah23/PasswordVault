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


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SecureVault")
        self.setFixedSize(450, 500)

        self.create_ui()

    def create_ui(self):

        title = QLabel("🔐 SecureVault")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("8086 Assembly Password Manager")
        subtitle.setAlignment(Qt.AlignCenter)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter master password")
        self.password_input.setEchoMode(QLineEdit.Password)

        unlock_button = QPushButton("Unlock Vault")

        unlock_button.clicked.connect(self.login)

        layout = QVBoxLayout()

        layout.addStretch()

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(30)

        layout.addWidget(self.password_input)
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

        QMessageBox.information(
            self,
            "SecureVault",
            "Login successful!"
        )


app = QApplication(sys.argv)

window = LoginWindow()
window.show()

sys.exit(app.exec())