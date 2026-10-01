"""Authentication boundary used by the PySide6 login window."""

from assembly_bridge import AssemblyBackendError, bridge
from vault import setup_master_password, unlock_vault


def first_run():
    return not bridge.is_master_configured()


def create_master_password(password, confirmation):
    return setup_master_password(password, confirmation)


def authenticate(password):
    return unlock_vault(password)


__all__ = [
    "AssemblyBackendError",
    "authenticate",
    "create_master_password",
    "first_run",
]