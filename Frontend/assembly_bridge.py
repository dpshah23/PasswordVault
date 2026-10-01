"""Bridge between Python and the EMU8086/DOS Assembly backend.

The bridge never performs encryption itself. Configure the compiled backend with
SECUREVAULT_ASSEMBLY_EXE, or place securevault.com in the Backend directory.
"""

import os
import shlex
import subprocess
import tempfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DEFAULT = BASE_DIR / "Backend" / "securevault.com"
BACKEND_CANDIDATES = (
    BASE_DIR / "Backend" / "securevault.com",
    BASE_DIR / "Backend" / "securevault.exe",
)
DOSBOX_CANDIDATES = (
    Path(r"C:\Program Files (x86)\DOSBox-0.74-3\DOSBox.exe"),
    Path(r"C:\Program Files\DOSBox-0.74-3\DOSBox.exe"),
)


class AssemblyBackendError(RuntimeError):
    """Base error for backend communication failures."""


class AssemblyBackendUnavailable(AssemblyBackendError):
    """Raised when the compiled EMU8086 backend cannot be started."""


class AssemblyProtocolError(AssemblyBackendError):
    """Raised when the backend returns malformed data or an error status."""


class AssemblyBridge:
    def __init__(self, executable=None, timeout=5):
        configured = executable or os.environ.get("SECUREVAULT_ASSEMBLY_EXE")
        self.executable = (
            Path(configured)
            if configured
            else next(
                (candidate for candidate in BACKEND_CANDIDATES if candidate.exists()),
                BACKEND_DEFAULT,
            )
        )
        self.runner = os.environ.get("SECUREVAULT_RUNNER")
        configured_dosbox = os.environ.get("SECUREVAULT_DOSBOX")
        self.dosbox = configured_dosbox or next(
            (str(path) for path in DOSBOX_CANDIDATES if path.exists()),
            None,
        )
        self.timeout = timeout

    @property
    def master_file(self):
        return BASE_DIR / "data" / "master.dat"

    def is_master_configured(self):
        return self.master_file.exists()

    @staticmethod
    def _hex(value):
        return value.hex().upper()

    def _request(self, command, password, data=b"", checksum=""):
        request = "\r\n".join(
            [
                command,
                f"PASSWORD={self._hex(password.encode('utf-8'))}",
                f"DATA={self._hex(data)}",
                f"CHECKSUM={checksum}",
                "",
            ]
        )

        if not self.executable.exists():
            raise AssemblyBackendUnavailable(
                "Assembly backend not found. Build the EMU8086 DOS target and "
                "place securevault.com or securevault.exe in Backend, or set "
                f"SECUREVAULT_ASSEMBLY_EXE. Checked: {', '.join(str(path) for path in BACKEND_CANDIDATES)}"
            )

        with tempfile.TemporaryDirectory(prefix="securevault-") as directory:
            request_path = Path(directory) / "request.txt"
            response_path = Path(directory) / "response.txt"
            request_path.write_text(request, encoding="ascii")

            try:
                process_command = self._build_command(
                    request_path,
                    response_path,
                    Path(directory),
                )
                result = subprocess.run(
                    process_command,
                    capture_output=True,
                    timeout=self.timeout,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired) as error:
                raise AssemblyBackendError(
                    "Could not communicate with the Assembly backend. "
                    "Install DOSBox or set SECUREVAULT_DOSBOX to its "
                    "DOSBox.exe path."
                ) from error

            if result.returncode != 0:
                raise AssemblyBackendError(
                    f"Assembly backend exited with status {result.returncode}."
                )

            if not response_path.exists():
                raise AssemblyProtocolError("Assembly backend returned no response.")

            response = self._parse_response(response_path.read_text(encoding="ascii"))

        if response["status"] == 2:
            raise AssemblyProtocolError("Master password verification failed.")
        if response["status"] == 3:
            raise AssemblyProtocolError("Vault integrity verification failed.")
        if response["status"] != 0:
            raise AssemblyProtocolError(
                f"Assembly backend rejected the request: {response['status']}"
            )
        return response

    def _build_command(self, request_path, response_path, temporary_directory):
        direct_command = [
            str(self.executable),
            str(request_path),
            str(response_path),
        ]

        if self.dosbox:
            project_directory = self.executable.parent.parent
            relative_backend = self.executable.relative_to(project_directory)
            mount_backend = f'mount c "{project_directory}"'
            mount_temporary = f'mount d "{temporary_directory}"'
            run_backend = (
                f"c:\\{relative_backend} "
                "d:\\request.txt d:\\response.txt"
            )
            return [
                self.dosbox,
                "-c",
                mount_backend,
                "-c",
                mount_temporary,
                "-c",
                run_backend,
                "-c",
                "exit",
            ]

        if self.runner:
            return shlex.split(self.runner, posix=False) + direct_command

        return direct_command

    @staticmethod
    def _parse_response(text):
        values = {}
        for line in text.splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.upper()] = value.strip()

        try:
            status = int(values["STATUS"])
            data = bytes.fromhex(values.get("DATA", ""))
            checksum = values.get("CHECKSUM", "")
        except (KeyError, ValueError) as error:
            raise AssemblyProtocolError("Malformed Assembly response.") from error

        return {"status": status, "data": data, "checksum": checksum}

    def setup_master_password(self, password):
        return self._request("SETUP", password)

    def verify_master_password(self, password):
        self._request("VERIFY", password)
        return True

    def encrypt(self, password, data):
        response = self._request("ENCRYPT", password, data)
        return response["data"], response["checksum"]

    def decrypt(self, password, data, checksum):
        response = self._request("DECRYPT", password, data, checksum)
        return response["data"]

    def check(self, password, data, checksum):
        self._request("CHECK", password, data, checksum)
        return True


bridge = AssemblyBridge()
