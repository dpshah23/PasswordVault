from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vault import update_credential


class EditCredentialWindow(QWidget):
    credential_saved = Signal()

    def __init__(self, credential):
        super().__init__()
        self.credential_id = credential["id"]
        self.setWindowTitle("Edit Credential - SecureVault")
        self.setFixedSize(500, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(12)

        title = QLabel("Edit Credential")
        title.setObjectName("title")
        layout.addWidget(title)

        self.website_input = self._field(layout, "Website", credential["website"])
        self.username_input = self._field(layout, "Username / Email", credential["username"])
        self.password_input = self._field(layout, "Password", credential["password"])
        self.password_input.setEchoMode(QLineEdit.Password)
        self.notes_input = self._field(layout, "Notes", credential.get("notes", ""))

        layout.addStretch()
        buttons = QHBoxLayout()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        save_button = QPushButton("Save Changes")
        save_button.setObjectName("saveButton")
        save_button.clicked.connect(self.save_changes)
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)
        layout.addLayout(buttons)

    @staticmethod
    def _field(layout, label, value):
        layout.addWidget(QLabel(label))
        field = QLineEdit(value)
        layout.addWidget(field)
        return field

    def save_changes(self):
        website = self.website_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        notes = self.notes_input.text().strip()

        if not website or not username or not password:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Website, username, and password are required.",
            )
            return

        try:
            updated = update_credential(
                self.credential_id,
                website=website,
                username=username,
                password=password,
                notes=notes,
            )
        except Exception as error:
            QMessageBox.critical(self, "Update Error", str(error))
            return

        if not updated:
            QMessageBox.warning(self, "Update Error", "Credential no longer exists.")
            return

        self.credential_saved.emit()
        self.close()