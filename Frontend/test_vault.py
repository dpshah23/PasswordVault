import tempfile
import unittest
from pathlib import Path

import vault
from assembly_bridge import AssemblyBridge


class FakeAssemblyBridge:
    def __init__(self):
        self.configured = True

    def is_master_configured(self):
        return self.configured

    def setup_master_password(self, password):
        return {"status": 0}

    def verify_master_password(self, password):
        if password != "correct-password":
            raise vault.AssemblyBackendError("Master password verification failed.")
        return True

    def encrypt(self, password, data):
        return data, str(len(data))

    def decrypt(self, password, data, checksum):
        if checksum != str(len(data)):
            raise vault.AssemblyBackendError("Vault integrity verification failed.")
        return data


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.old_paths = vault.DATA_DIR, vault.VAULT_FILE, vault.LEGACY_FILE, vault.bridge
        vault.DATA_DIR = root
        vault.VAULT_FILE = root / "vault.dat"
        vault.LEGACY_FILE = root / "vault.json"
        vault.bridge = FakeAssemblyBridge()
        vault.lock_vault()

    def tearDown(self):
        vault.lock_vault()
        vault.DATA_DIR, vault.VAULT_FILE, vault.LEGACY_FILE, vault.bridge = self.old_paths
        self.temp_dir.cleanup()

    def test_locked_vault_rejects_access(self):
        with self.assertRaises(vault.VaultLockedError):
            vault.get_credentials()

    def test_crud_round_trip(self):
        vault.unlock_vault("correct-password")
        credential = vault.add_credential("example.com", "user", "secret", "note")
        self.assertEqual(vault.search_credentials("EXAMPLE"), [credential])
        self.assertEqual(vault.get_credential(credential["id"]), credential)
        self.assertTrue(vault.update_credential(credential["id"], password="changed"))
        self.assertEqual(vault.get_credential(credential["id"])["password"], "changed")
        self.assertTrue(vault.delete_credential(credential["id"]))
        self.assertEqual(vault.get_credentials(), [])

    def test_lock_clears_session(self):
        vault.unlock_vault("correct-password")
        vault.add_credential("example.com", "user", "secret")
        vault.lock_vault()
        self.assertFalse(vault.is_unlocked())
        with self.assertRaises(vault.VaultLockedError):
            vault.get_credentials()

    def test_response_parser(self):
        response = AssemblyBridge._parse_response("STATUS=0\nDATA=4142\nCHECKSUM=00AF\n")
        self.assertEqual(response["data"], b"AB")
        self.assertEqual(response["checksum"], "00AF")


if __name__ == "__main__":
    unittest.main()
