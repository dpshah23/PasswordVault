# SecureVault - 8086 Assembly Password Manager

SecureVault is a college project that combines a PySide6 interface with an
8086 Assembly backend. Python owns the application workflow and GUI; Assembly
owns master-password verification, encryption, decryption, and checksums.

## Architecture

```mermaid
flowchart LR
    UI[PySide6 GUI] --> AUTH[login.py]
    UI --> VAULT[vault.py]
    AUTH --> BRIDGE[assembly_bridge.py]
    VAULT --> BRIDGE
    BRIDGE --> ASM[EMU8086 DOS backend]
    ASM --> STORE[data/vault.dat]
```

`vault.py` keeps decrypted credentials only in the active unlocked session.
The persistent file contains an encrypted byte payload and its Assembly
checksum. CRUD operations are unavailable while the vault is locked.

## Setup

1. Install the dependency with `pip install -r requirements.txt`.
2. Build the DOS-compatible Assembly command program from
   `Backend/assembly_interface.asm` and `Backend/Encryption.asm` in EMU8086.
3. Place the resulting executable at `Backend/securevault.com`, or set
   `SECUREVAULT_ASSEMBLY_EXE` to its path.
4. Run `python Frontend/main.py`.

The Assembly program must accept request and response file paths and implement
the protocol described in `Backend/assembly_interface.asm`. Python does not
fall back to Python cryptography when the executable is missing.

## Algorithm and limitations

The Assembly transformation XORs each byte with a changing key, adds a changing
seed, and rotates the result. Decryption reverses those operations. A rotating
16-bit additive checksum detects accidental or basic intentional modification.
These routines demonstrate 8086 arithmetic and memory handling; they are not
production-grade cryptography and must not protect real secrets.

For $n$ bytes, encryption, decryption, and checksum calculation each take
$O(n)$ time and $O(1)$ additional Assembly space. Vault serialization requires
$O(n)$ Python memory for the decrypted record list.

## Tests

Run the isolated Python tests from the project root:

```powershell
python -m unittest discover -s Frontend -p "test_*.py"
```

The tests use a fake Assembly boundary only to test vault state and CRUD logic.
The EMU8086 backend must additionally be tested with known encryption vectors,
wrong passwords, malformed requests, and modified ciphertext.
