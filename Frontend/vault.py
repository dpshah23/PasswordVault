import json
import os
import uuid
from datetime import datetime


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")

VAULT_FILE = os.path.join(DATA_DIR, "vault.json")


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_vault():
    """
    Create the data directory and vault file if they don't exist.
    """

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(VAULT_FILE):

        with open(VAULT_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)


# ============================================================
# LOAD VAULT
# ============================================================

def load_vault():
    """
    Load all credentials from the vault.
    """

    initialize_vault()

    try:

        with open(VAULT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, FileNotFoundError):

        return []


# ============================================================
# SAVE VAULT
# ============================================================

def save_vault(credentials):
    """
    Save the complete credential list.
    """

    initialize_vault()

    with open(VAULT_FILE, "w", encoding="utf-8") as file:

        json.dump(
            credentials,
            file,
            indent=4
        )


# ============================================================
# ADD CREDENTIAL
# ============================================================

def add_credential(
    website,
    username,
    password,
    notes=""
):
    """
    Add a new credential to the vault.

    NOTE:
    Password is currently stored as plaintext for development.
    Later this will be replaced by the 8086 Assembly encryption
    engine.
    """

    credentials = load_vault()

    credential = {

        "id": str(uuid.uuid4()),

        "website": website,

        "username": username,

        "password": password,

        "notes": notes,

        "created_at": datetime.now().isoformat(),

    }

    credentials.append(credential)

    save_vault(credentials)

    return credential


# ============================================================
# GET ALL CREDENTIALS
# ============================================================

def get_credentials():
    """
    Return all saved credentials.
    """

    return load_vault()


# ============================================================
# GET ONE CREDENTIAL
# ============================================================

def get_credential(credential_id):
    """
    Find a credential by ID.
    """

    credentials = load_vault()

    for credential in credentials:

        if credential["id"] == credential_id:

            return credential

    return None


# ============================================================
# SEARCH CREDENTIALS
# ============================================================

def search_credentials(query):
    """
    Search by website or username.
    """

    credentials = load_vault()

    query = query.lower().strip()

    results = []

    for credential in credentials:

        website = credential["website"].lower()

        username = credential["username"].lower()

        if query in website or query in username:

            results.append(credential)

    return results


# ============================================================
# DELETE CREDENTIAL
# ============================================================

def delete_credential(credential_id):
    """
    Delete a credential by ID.
    """

    credentials = load_vault()

    updated_credentials = [

        credential

        for credential in credentials

        if credential["id"] != credential_id

    ]

    if len(updated_credentials) == len(credentials):

        return False

    save_vault(updated_credentials)

    return True


# ============================================================
# UPDATE CREDENTIAL
# ============================================================

def update_credential(
    credential_id,
    website=None,
    username=None,
    password=None,
    notes=None
):
    """
    Update an existing credential.
    """

    credentials = load_vault()

    for credential in credentials:

        if credential["id"] == credential_id:

            if website is not None:
                credential["website"] = website

            if username is not None:
                credential["username"] = username

            if password is not None:
                credential["password"] = password

            if notes is not None:
                credential["notes"] = notes

            credential["updated_at"] = datetime.now().isoformat()

            save_vault(credentials)

            return True

    return False