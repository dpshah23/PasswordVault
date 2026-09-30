from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt
from vault import add_credential


class AddCredentialWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Credential - SecureVault")
        self.setFixedSize(500, 600)

        self.create_ui()

    def create_ui(self):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(15)

        # Title
        title = QLabel("Add New Credential")
        title.setObjectName("title")

        subtitle = QLabel(
            "Store your credentials securely in SecureVault."
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Website
        website_label = QLabel("Website")
        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText("e.g. github.com")

        layout.addWidget(website_label)
        layout.addWidget(self.website_input)

        # Username
        username_label = QLabel("Username / Email")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g. deep@example.com")

        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Password")

        password_layout = QHBoxLayout()

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)

        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(self.generate_password)

        password_layout.addWidget(self.password_input)
        password_layout.addWidget(generate_button)

        layout.addWidget(password_label)
        layout.addLayout(password_layout)

        # Notes
        notes_label = QLabel("Notes")

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText(
            "Optional notes"
        )

        layout.addWidget(notes_label)
        layout.addWidget(self.notes_input)

        layout.addStretch()

        # Buttons
        buttons = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        save_button = QPushButton("Save Credential")
        save_button.setObjectName("saveButton")
        save_button.clicked.connect(self.save_credential)

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        self.apply_styles()

    def generate_password(self):

        import secrets
        import string

        characters = (
            string.ascii_letters
            + string.digits
            + "!@#$%^&*"
        )

        password = "".join(
            secrets.choice(characters)
            for _ in range(16)
        )

        self.password_input.setText(password)

    def save_credential(self):

        website = self.website_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        notes = self.notes_input.text().strip()

        if not website:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a website."
            )

            return

        if not username:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a username."
            )

            return

        if not password:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a password."
            )

            return

        # Save credential
        credential = add_credential(
            website=website,
            username=username,
            password=password,
            notes=notes
        )

        QMessageBox.information(
            self,
            "Credential Saved",
            f"{website} has been added to your vault."
        )

        self.close()

    def apply_styles(self):

        self.setStyleSheet("""
        
        QWidget {
            background-color: #f7f8fc;
            color: #111827;
            font-family: "Segoe UI";
        }

        #title {
            font-size: 26px;
            font-weight: bold;
        }

        #subtitle {
            color: #6b7280;
        }

        QLineEdit {
            background-color: white;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 1px solid #2563eb;
        }

        QPushButton {
            background-color: #e5e7eb;
            border: none;
            border-radius: 8px;
            padding: 11px 15px;
        }

        QPushButton:hover {
            background-color: #d1d5db;
        }

        #saveButton {
            background-color: #2563eb;
            color: white;
            font-weight: bold;
        }

        #saveButton:hover {
            background-color: #1d4ed8;
        }

        """)