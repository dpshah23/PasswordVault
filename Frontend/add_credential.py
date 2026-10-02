from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)
from PySide6.QtCore import Signal

from vault import add_credential


class AddCredentialWindow(QWidget):

    # Signal sent to Dashboard after a credential is saved
    credential_saved = Signal()

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Add Credential - SecureVault")
        self.setFixedSize(500, 600)

        self.create_ui()

    def create_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            40, 35, 40, 35
        )

        layout.setSpacing(15)

        # ==================================================
        # TITLE
        # ==================================================

        title = QLabel("Add New Credential")
        title.setObjectName("title")

        subtitle = QLabel(
            "Store your credentials securely in SecureVault."
        )
        subtitle.setObjectName("subtitle")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # ==================================================
        # WEBSITE
        # ==================================================

        website_label = QLabel("Website")

        self.website_input = QLineEdit()
        self.website_input.setPlaceholderText(
            "e.g. github.com"
        )

        layout.addWidget(website_label)
        layout.addWidget(self.website_input)

        # ==================================================
        # USERNAME
        # ==================================================

        username_label = QLabel(
            "Username / Email"
        )

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(
            "e.g. deep@example.com"
        )

        layout.addWidget(username_label)
        layout.addWidget(self.username_input)

        # ==================================================
        # PASSWORD
        # ==================================================

        password_label = QLabel("Password")

        password_layout = QHBoxLayout()

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Enter password"
        )

        self.password_input.setEchoMode(
            QLineEdit.Password
        )

        generate_button = QPushButton(
            "Generate"
        )

        generate_button.clicked.connect(
            self.generate_password
        )

        password_layout.addWidget(
            self.password_input
        )

        password_layout.addWidget(
            generate_button
        )

        layout.addWidget(password_label)
        layout.addLayout(password_layout)

        # ==================================================
        # NOTES
        # ==================================================

        notes_label = QLabel("Notes")

        self.notes_input = QLineEdit()

        self.notes_input.setPlaceholderText(
            "Optional notes"
        )

        layout.addWidget(notes_label)
        layout.addWidget(self.notes_input)

        layout.addStretch()

        # ==================================================
        # BUTTONS
        # ==================================================

        buttons = QHBoxLayout()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.clicked.connect(
            self.close
        )

        save_button = QPushButton(
            "Save Credential"
        )

        save_button.setObjectName(
            "saveButton"
        )

        save_button.clicked.connect(
            self.save_credential
        )

        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        self.apply_styles()

    # ======================================================
    # PASSWORD GENERATOR
    # ======================================================

    def generate_password(self):

        import secrets
        import string

        groups = (
            string.ascii_uppercase,
            string.ascii_lowercase,
            string.digits,
            "!@#$%^&*",
        )
        characters = "".join(groups)
        password_parts = [secrets.choice(group) for group in groups]
        password_parts.extend(
            secrets.choice(characters)
            for _ in range(12)
        )
        secrets.SystemRandom().shuffle(password_parts)
        password = "".join(password_parts)

        self.password_input.setText(
            password
        )

    # ======================================================
    # SAVE CREDENTIAL
    # ======================================================

    def save_credential(self):

        website = (
            self.website_input
            .text()
            .strip()
        )

        username = (
            self.username_input
            .text()
            .strip()
        )

        password = (
            self.password_input
            .text()
        )

        notes = (
            self.notes_input
            .text()
            .strip()
        )

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if not website:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a website."
            )

            self.website_input.setFocus()

            return

        if not username:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a username."
            )

            self.username_input.setFocus()

            return

        if not password:

            QMessageBox.warning(
                self,
                "Missing Information",
                "Please enter a password."
            )

            self.password_input.setFocus()

            return

        # --------------------------------------------------
        # SAVE TO VAULT
        # --------------------------------------------------

        try:

            credential = add_credential(
                website=website,
                username=username,
                password=password,
                notes=notes
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Save Error",
                f"Could not save credential.\n\n{error}"
            )

            return

        # --------------------------------------------------
        # TELL DASHBOARD TO REFRESH
        # --------------------------------------------------

        self.credential_saved.emit()

        QMessageBox.information(
            self,
            "Credential Saved",
            f"{website} has been added to your vault."
        )

        self.close()

    # ======================================================
    # STYLES
    # ======================================================

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