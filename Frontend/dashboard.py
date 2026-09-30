from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QLineEdit,
    QScrollArea,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from vault import get_credentials, delete_credential, search_credentials


class CredentialCard(QFrame):
    deleted = Signal(str)

    def __init__(self, credential):
        super().__init__()

        self.credential_id = credential["id"]
        self.website = credential["website"]
        self.username = credential["username"]
        self.password = credential["password"]

        self.password_visible = False

        self.setObjectName("credentialCard")
        self.setFixedHeight(100)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)

        # Website icon
        icon = QLabel("🌐")
        icon.setFixedWidth(45)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI Emoji", 20))

        # Website + username
        info_layout = QVBoxLayout()

        website_label = QLabel(self.website)
        website_label.setObjectName("websiteLabel")

        username_label = QLabel(self.username)
        username_label.setObjectName("usernameLabel")

        info_layout.addWidget(website_label)
        info_layout.addWidget(username_label)

        # Password
        self.password_label = QLabel("••••••••••")
        self.password_label.setObjectName("passwordLabel")
        self.password_label.setAlignment(Qt.AlignCenter)
        self.password_label.setMinimumWidth(130)

        # Show/hide
        self.show_button = QPushButton("👁")
        self.show_button.setObjectName("iconButton")
        self.show_button.setFixedSize(40, 40)
        self.show_button.clicked.connect(self.toggle_password)

        # Delete
        delete_button = QPushButton("🗑")
        delete_button.setObjectName("deleteButton")
        delete_button.setFixedSize(40, 40)
        delete_button.clicked.connect(self.delete_clicked)

        layout.addWidget(icon)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(self.password_label)
        layout.addWidget(self.show_button)
        layout.addWidget(delete_button)

    def toggle_password(self):
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.password_label.setText(self.password)
            self.show_button.setText("🙈")
        else:
            self.password_label.setText("••••••••••")
            self.show_button.setText("👁")

    def delete_clicked(self):
        self.deleted.emit(self.credential_id)


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SecureVault")
        self.resize(1100, 700)

        self.credential_cards = []

        self.create_ui()

    def create_ui(self):

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ==================================================
        # SIDEBAR
        # ==================================================

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 25, 20, 20)
        sidebar_layout.setSpacing(10)

        logo = QLabel("🔐 SecureVault")
        logo.setObjectName("logo")

        subtitle = QLabel("Password Manager")
        subtitle.setObjectName("sidebarSubtitle")

        sidebar_layout.addWidget(logo)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(35)

        dashboard_button = QPushButton("🏠   Dashboard")
        passwords_button = QPushButton("🔑   Passwords")
        security_button = QPushButton("🛡   Security")
        settings_button = QPushButton("⚙   Settings")

        dashboard_button.setObjectName("activeMenu")
        passwords_button.setObjectName("menuButton")
        security_button.setObjectName("menuButton")
        settings_button.setObjectName("menuButton")

        sidebar_layout.addWidget(dashboard_button)
        sidebar_layout.addWidget(passwords_button)
        sidebar_layout.addWidget(security_button)
        sidebar_layout.addWidget(settings_button)

        sidebar_layout.addStretch()

        version = QLabel("SecureVault v1.0\n8086 Assembly Engine")
        version.setObjectName("version")

        sidebar_layout.addWidget(version)

        # ==================================================
        # CONTENT
        # ==================================================

        content = QWidget()
        content_layout = QVBoxLayout(content)

        content_layout.setContentsMargins(35, 30, 35, 30)
        content_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        greeting = QLabel("Welcome back 👋")
        greeting.setObjectName("greeting")

        title_layout.addWidget(title)
        title_layout.addWidget(greeting)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        user_label = QLabel("👤  Deep")
        user_label.setObjectName("userLabel")

        header_layout.addWidget(user_label)

        content_layout.addLayout(header_layout)

        # ==================================================
        # SEARCH
        # ==================================================

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search credentials...")
        self.search_box.setObjectName("searchBox")

        # Search as the user types
        self.search_box.textChanged.connect(self.search_credentials)

        content_layout.addWidget(self.search_box)

        # ==================================================
        # STATISTICS
        # ==================================================

        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.password_count_card = self.create_stat_card(
            "🔑", "0", "Saved Passwords"
        )

        self.security_card = self.create_stat_card(
            "🛡", "Ready", "Security Status"
        )

        self.alert_card = self.create_stat_card(
            "⚠", "0", "Security Alerts"
        )

        stats_layout.addWidget(self.password_count_card)
        stats_layout.addWidget(self.security_card)
        stats_layout.addWidget(self.alert_card)

        content_layout.addLayout(stats_layout)

        # ==================================================
        # CREDENTIALS HEADER
        # ==================================================

        credentials_header = QHBoxLayout()

        credentials_title = QLabel("Your Credentials")
        credentials_title.setObjectName("sectionTitle")

        self.add_button = QPushButton("+  Add Credential")
        self.add_button.setObjectName("addButton")
        self.add_button.clicked.connect(self.open_add_credential)

        credentials_header.addWidget(credentials_title)
        credentials_header.addStretch()
        credentials_header.addWidget(self.add_button)

        content_layout.addLayout(credentials_header)

        # ==================================================
        # CREDENTIAL LIST
        # ==================================================

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.credential_container = QWidget()

        self.credential_layout = QVBoxLayout(
            self.credential_container
        )
        self.credential_layout.setSpacing(12)
        self.credential_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll.setWidget(self.credential_container)

        content_layout.addWidget(self.scroll)

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        self.apply_styles()

        # Load real credentials from vault.py
        self.load_credentials()

    # ======================================================
    # LOAD CREDENTIALS
    # ======================================================

    def load_credentials(self, credentials=None):

        # If no list was supplied, load everything
        if credentials is None:
            credentials = get_credentials()

        # Remove current cards
        while self.credential_layout.count():

            item = self.credential_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self.credential_cards.clear()

        # Update saved-password count
        self.update_password_count(len(credentials))

        # Empty state
        if not credentials:

            empty_label = QLabel(
                "🔐\n\n"
                "No credentials found.\n\n"
                "Click '+ Add Credential' to add your first password."
            )

            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setObjectName("emptyLabel")

            self.credential_layout.addWidget(empty_label)
            self.credential_layout.addStretch()

            return

        # Add credential cards
        for credential in credentials:

            card = CredentialCard(credential)

            card.deleted.connect(
                self.delete_credential
            )

            self.credential_layout.addWidget(card)

            self.credential_cards.append(card)

        self.credential_layout.addStretch()

    # ======================================================
    # SEARCH
    # ======================================================

    def search_credentials(self, query):

        query = query.strip()

        if not query:

            self.load_credentials()
            return

        results = search_credentials(query)

        self.load_credentials(results)

    # ======================================================
    # DELETE
    # ======================================================

    def delete_credential(self, credential_id):

        result = QMessageBox.question(
            self,
            "Delete Credential",
            "Are you sure you want to permanently delete this credential?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result != QMessageBox.Yes:
            return

        success = delete_credential(credential_id)

        if success:

            self.load_credentials(
                get_credentials()
            )

            QMessageBox.information(
                self,
                "Credential Deleted",
                "The credential was deleted successfully."
            )

        else:

            QMessageBox.warning(
                self,
                "Error",
                "The credential could not be deleted."
            )

    # ======================================================
    # ADD CREDENTIAL
    # ======================================================

    def open_add_credential(self):

        from add_credential import AddCredentialWindow

        self.add_window = AddCredentialWindow()

        # This works with the credential_saved signal
        # added to add_credential.py.
        if hasattr(self.add_window, "credential_saved"):

            self.add_window.credential_saved.connect(
                self.refresh_after_add
            )

        self.add_window.show()

    def refresh_after_add(self):

        # Clear an existing search so the newly-added
        # credential is immediately visible.
        self.search_box.clear()

        self.load_credentials()

    # ======================================================
    # STAT CARD
    # ======================================================

    def create_stat_card(self, icon, value, label):

        card = QFrame()
        card.setObjectName("statCard")

        layout = QHBoxLayout(card)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 22))

        text_layout = QVBoxLayout()

        value_label = QLabel(value)
        value_label.setObjectName("statValue")

        label_text = QLabel(label)
        label_text.setObjectName("statLabel")

        text_layout.addWidget(value_label)
        text_layout.addWidget(label_text)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)

        # Keep references so their values can be updated later
        card.value_label = value_label

        return card

    def update_password_count(self, count):

        self.password_count_card.value_label.setText(
            str(count)
        )

    # ======================================================
    # STYLES
    # ======================================================

    def apply_styles(self):

        self.setStyleSheet("""

        QWidget {
            background-color: #f7f8fc;
            color: #1f2937;
            font-family: "Segoe UI";
        }

        /* ================= SIDEBAR ================= */

        #sidebar {
            background-color: #111827;
        }

        #logo {
            color: white;
            font-size: 22px;
            font-weight: bold;
        }

        #sidebarSubtitle {
            color: #9ca3af;
            font-size: 12px;
        }

        #menuButton,
        #activeMenu {
            border: none;
            text-align: left;
            padding: 13px 15px;
            border-radius: 9px;
            font-size: 14px;
        }

        #menuButton {
            color: #cbd5e1;
            background-color: transparent;
        }

        #menuButton:hover {
            background-color: #1f2937;
            color: white;
        }

        #activeMenu {
            background-color: #2563eb;
            color: white;
            font-weight: bold;
        }

        #version {
            color: #6b7280;
            font-size: 11px;
        }

        /* ================= HEADER ================= */

        #pageTitle {
            font-size: 28px;
            font-weight: bold;
            color: #111827;
        }

        #greeting {
            color: #6b7280;
            font-size: 14px;
        }

        #userLabel {
            background-color: white;
            padding: 10px 15px;
            border-radius: 10px;
            color: #374151;
        }

        /* ================= SEARCH ================= */

        #searchBox {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 12px 15px;
            font-size: 14px;
        }

        #searchBox:focus {
            border: 1px solid #2563eb;
        }

        /* ================= STATS ================= */

        #statCard {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            min-height: 75px;
        }

        #statValue {
            font-size: 20px;
            font-weight: bold;
            color: #111827;
        }

        #statLabel {
            font-size: 12px;
            color: #6b7280;
        }

        /* ================= SECTION ================= */

        #sectionTitle {
            font-size: 18px;
            font-weight: bold;
        }

        #addButton {
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 8px;
            font-weight: bold;
        }

        #addButton:hover {
            background-color: #1d4ed8;
        }

        /* ================= CREDENTIAL ================= */

        #credentialCard {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
        }

        #credentialCard:hover {
            border: 1px solid #2563eb;
        }

        #websiteLabel {
            font-size: 15px;
            font-weight: bold;
        }

        #usernameLabel {
            color: #6b7280;
            font-size: 12px;
        }

        #passwordLabel {
            color: #374151;
            font-family: Consolas;
        }

        #iconButton {
            background-color: #f3f4f6;
            border: none;
            border-radius: 8px;
        }

        #iconButton:hover {
            background-color: #e5e7eb;
        }

        #deleteButton {
            background-color: #fee2e2;
            border: none;
            border-radius: 8px;
        }

        #deleteButton:hover {
            background-color: #fecaca;
        }

        #emptyLabel {
            color: #9ca3af;
            font-size: 15px;
            padding: 60px;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        """)
