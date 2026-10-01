"""Encrypted credential vault service.

CRUD remains intentionally small so the existing dashboard can keep using the
same functions. The vault must be unlocked before any credential is exposed.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from assembly_bridge import AssemblyBackendError, bridge


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VAULT_FILE = DATA_DIR / "vault.dat"
LEGACY_FILE = DATA_DIR / "vault.json"

_unlocked_password = None
_credentials = []


class VaultLockedError(RuntimeError):
    """Raised when a credential operation is attempted while locked."""


class VaultCorruptError(RuntimeError):
    """Raised when encrypted vault data cannot be validated."""


def initialize_vault():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def is_unlocked():
    return _unlocked_password is not None


def _require_unlocked():
    if not is_unlocked():
        raise VaultLockedError("Unlock the vault before accessing credentials.")


def _read_envelope():
    initialize_vault()
    if not VAULT_FILE.exists() or VAULT_FILE.stat().st_size == 0:
        return None
    try:
        return json.loads(VAULT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VaultCorruptError("The vault file is not valid.") from error


def _write_envelope(encrypted, checksum):
    temporary = VAULT_FILE.with_suffix(".tmp")
    envelope = {
        "format": 1,
        "data": encrypted.hex().upper(),
        "checksum": checksum,
    }
    temporary.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    os.replace(temporary, VAULT_FILE)


def _load_plaintext():
    envelope = _read_envelope()
    if envelope is None:
        if LEGACY_FILE.exists():
            raise VaultCorruptError(
                "A plaintext vault exists. Export or remove it before creating an encrypted vault."
            )
        return []

    try:
        encrypted = bytes.fromhex(envelope["data"])
        checksum = str(envelope["checksum"])
    except (KeyError, ValueError, TypeError) as error:
        raise VaultCorruptError("The encrypted vault metadata is malformed.") from error

    try:
        plaintext = bridge.decrypt(_unlocked_password, encrypted, checksum)
    except AssemblyBackendError as error:
        raise VaultCorruptError(str(error)) from error

    try:
        records = json.loads(plaintext.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VaultCorruptError("The decrypted vault contents are malformed.") from error

    if not isinstance(records, list):
        raise VaultCorruptError("The decrypted vault must contain a list.")
    return records


def _save_plaintext(records):
    payload = json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    encrypted, checksum = bridge.encrypt(_unlocked_password, payload)
    _write_envelope(encrypted, checksum)


def setup_master_password(password, confirmation):
    if not password or password != confirmation:
        return False
    bridge.setup_master_password(password)
    return True


def unlock_vault(password):
    global _unlocked_password, _credentials
    bridge.verify_master_password(password)
    _unlocked_password = password
    try:
        _credentials = _load_plaintext()
    except Exception:
        _unlocked_password = None
        _credentials = []
        raise
    return True


def lock_vault():
    global _unlocked_password, _credentials
    _credentials = []
    _unlocked_password = None


def verify_integrity():
    _require_unlocked()
    envelope = _read_envelope()
    if envelope is None:
        return True
    try:
        encrypted = bytes.fromhex(envelope["data"])
        checksum = str(envelope["checksum"])
        bridge.check(_unlocked_password, encrypted, checksum)
    except (KeyError, ValueError, TypeError, AssemblyBackendError) as error:
        raise VaultCorruptError("Vault integrity verification failed.") from error
    return True


def get_credentials():
    _require_unlocked()
    return [dict(item) for item in _credentials]


def get_credential(credential_id):
    _require_unlocked()
    return next(
        (dict(item) for item in _credentials if item["id"] == credential_id),
        None,
    )


def search_credentials(query):
    _require_unlocked()
    query = query.lower().strip()
    return [
        dict(item)
        for item in _credentials
        if query in item["website"].lower() or query in item["username"].lower()
    ]


def add_credential(website, username, password, notes=""):
    _require_unlocked()
    credential = {
        "id": str(uuid.uuid4()),
        "website": website,
        "username": username,
        "password": password,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }
    _credentials.append(credential)
    _save_plaintext(_credentials)
    return dict(credential)


def delete_credential(credential_id):
    _require_unlocked()
    original_count = len(_credentials)
    _credentials[:] = [item for item in _credentials if item["id"] != credential_id]
    if len(_credentials) == original_count:
        return False
    _save_plaintext(_credentials)
    return True


def update_credential(credential_id, website=None, username=None, password=None, notes=None):
    _require_unlocked()
    for credential in _credentials:
        if credential["id"] != credential_id:
            continue
        if website is not None:
            credential["website"] = website
        if username is not None:
            credential["username"] = username
        if password is not None:
            credential["password"] = password
        if notes is not None:
            credential["notes"] = notes
        credential["updated_at"] = datetime.now().isoformat()
        _save_plaintext(_credentials)
        return True
    return False
