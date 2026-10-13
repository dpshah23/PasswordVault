
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

# Password Vault/
BASE_DIR = Path(__file__).resolve().parent.parent

# Password Vault/Backend/
BACKEND_DIR = BASE_DIR / "Backend"

# Password Vault/data/
DATA_DIR = BASE_DIR / "data"

# Main Assembly backend. The short filename is required by DOSBox 0.74.
BACKEND_DEFAULT = BACKEND_DIR / "SVFIX.COM"


# Possible Assembly backend executables
BACKEND_CANDIDATES = (
    BACKEND_DIR / "SVFIX.COM",
    BACKEND_DIR / "securevault.com",
    BACKEND_DIR / "SV.com",
    BACKEND_DIR / "securevault.exe",
)


# Possible DOSBox installations
DOSBOX_CANDIDATES = (
    Path(r"C:\Program Files (x86)\DOSBox-0.74-3\DOSBox.exe"),
    Path(r"C:\Program Files\DOSBox-0.74-3\DOSBox.exe"),
    Path(r"C:\Program Files (x86)\DOSBox\DOSBox.exe"),
    Path(r"C:\Program Files\DOSBox\DOSBox.exe"),
)


# ============================================================
# EXCEPTIONS
# ============================================================

class AssemblyBackendError(RuntimeError):
    """Base error for Assembly backend failures."""


class AssemblyBackendUnavailable(AssemblyBackendError):
    """Raised when the Assembly backend cannot be started."""


class AssemblyProtocolError(AssemblyBackendError):
    """Raised when Assembly returns an invalid response."""


# ============================================================
# ASSEMBLY BRIDGE
# ============================================================

class AssemblyBridge:

    def __init__(self, executable=None, timeout=10):

        # ----------------------------------------------------
        # Find Assembly executable
        # ----------------------------------------------------

        configured = executable or os.environ.get(
            "SECUREVAULT_ASSEMBLY_EXE"
        )

        if configured:
            self.executable = Path(configured)
        else:
            self.executable = next(
                (
                    candidate
                    for candidate in BACKEND_CANDIDATES
                    if candidate.exists()
                ),
                BACKEND_DEFAULT,
            )

        # ----------------------------------------------------
        # Optional custom runner
        # ----------------------------------------------------

        self.runner = os.environ.get(
            "SECUREVAULT_RUNNER"
        )

        # ----------------------------------------------------
        # Find DOSBox
        # ----------------------------------------------------

        configured_dosbox = os.environ.get(
            "SECUREVAULT_DOSBOX"
        )

        if configured_dosbox:

            self.dosbox = configured_dosbox

        else:

            self.dosbox = next(
                (
                    str(path)
                    for path in DOSBOX_CANDIDATES
                    if path.exists()
                ),
                None,
            )

        self.timeout = timeout

    # ========================================================
    # MASTER FILE
    # ========================================================

    @property
    def master_file(self):
        return DATA_DIR / "master.dat"

    def is_master_configured(self):
        return self.master_file.exists()

    # ========================================================
    # HEX ENCODING
    # ========================================================

    @staticmethod
    def _hex(value: bytes) -> str:
        return value.hex().upper()

    # ========================================================
    # REQUEST
    # ========================================================

    def _request(
        self,
        command,
        password,
        data=b"",
        checksum="",
    ):

        # ----------------------------------------------------
        # Build request
        # ----------------------------------------------------

        request = "\r\n".join(
            [
                command,
                f"PASSWORD={self._hex(password.encode('utf-8'))}",
                f"DATA={self._hex(data)}",
                f"CHECKSUM={checksum}",
                "",
            ]
        )

        # ----------------------------------------------------
        # Verify Assembly executable
        # ----------------------------------------------------

        if not self.executable.exists():

            raise AssemblyBackendUnavailable(
                "Assembly backend not found.\n\n"
                f"Expected:\n{self.executable}\n\n"
                "Build securevault.com and place it in Backend."
            )

        # ----------------------------------------------------
        # Verify DOSBox
        # ----------------------------------------------------

        if not self.dosbox:

            raise AssemblyBackendUnavailable(
                "DOSBox was not found.\n\n"
                "Install DOSBox or set the "
                "SECUREVAULT_DOSBOX environment variable."
            )

        # ----------------------------------------------------
        # Temporary communication directory
        # ----------------------------------------------------

        with tempfile.TemporaryDirectory(
            prefix="securevault_"
        ) as directory:

            temporary_directory = Path(directory)

            request_path = (
                temporary_directory / "request.txt"
            )

            response_path = (
                temporary_directory / "response.txt"
            )

            # ------------------------------------------------
            # Write request
            # ------------------------------------------------

            request_path.write_text(
                request,
                encoding="ascii",
            )

            # Make absolutely sure no stale response exists
            if response_path.exists():
                response_path.unlink()

            # ------------------------------------------------
            # Build DOSBox command
            # ------------------------------------------------

            process_command = self._build_command(
                request_path,
                response_path,
                temporary_directory,
            )

            # Useful debugging output
            print("\n========== SecureVault Assembly ==========")
            print("Assembly:")
            print(self.executable)

            print("\nDOSBox:")
            print(self.dosbox)

            print("\nRequest:")
            print(request)

            print("\nDOSBox command:")
            print(process_command)

            # ------------------------------------------------
            # Execute
            # ------------------------------------------------

            try:

                result = subprocess.run(
                    process_command,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                )

            except subprocess.TimeoutExpired as error:

                raise AssemblyBackendError(
                    "DOSBox/Assembly backend timed out."
                ) from error

            except OSError as error:

                raise AssemblyBackendError(
                    "Could not start DOSBox.\n\n"
                    f"{error}"
                ) from error

            # ------------------------------------------------
            # Debug DOSBox output
            # ------------------------------------------------

            print("\nDOSBox stdout:")
            print(result.stdout)

            print("\nDOSBox stderr:")
            print(result.stderr)

            print("\nDOSBox return code:")
            print(result.returncode)

            # ------------------------------------------------
            # Check response
            # ------------------------------------------------

            if not response_path.exists():

                raise AssemblyProtocolError(
                    "Assembly backend returned no response.\n\n"
                    "Expected response file:\n"
                    f"{response_path}\n\n"
                    f"DOSBox return code: {result.returncode}\n\n"
                    f"DOSBox stdout:\n{result.stdout}\n\n"
                    f"DOSBox stderr:\n{result.stderr}"
                )

            # ------------------------------------------------
            # Read response
            # ------------------------------------------------

            try:

                response_text = response_path.read_text(
                    encoding="ascii"
                )

            except Exception as error:

                raise AssemblyProtocolError(
                    "response.txt was created but could not "
                    "be read."
                ) from error

            print("\nAssembly response:")
            print(response_text)

            # ------------------------------------------------
            # Parse
            # ------------------------------------------------

            response = self._parse_response(
                response_text
            )

        # ====================================================
        # STATUS HANDLING
        # ====================================================

        if response["status"] == 2:

            raise AssemblyProtocolError(
                "Master password verification failed."
            )

        if response["status"] == 3:

            raise AssemblyProtocolError(
                "Vault integrity verification failed."
            )

        if response["status"] == 4:

            raise AssemblyProtocolError(
                "Assembly rejected the request as malformed."
            )

        if response["status"] == 5:

            raise AssemblyProtocolError(
                "Assembly reported a file error."
            )

        if response["status"] != 0:

            raise AssemblyProtocolError(
                "Assembly backend rejected the request: "
                f"{response['status']}"
            )

        return response

    # ========================================================
    # BUILD DOSBOX COMMAND
    # ========================================================

    def _build_command(
        self,
        request_path,
        response_path,
        temporary_directory,
    ):

        # ----------------------------------------------------
        # IMPORTANT
        #
        # Windows project:
        #
        # D:\...\Password Vault\
        #
        # DOSBox mount:
        #
        # C:\
        #
        # Therefore:
        #
        # C:\BACKEND\securevault.com
        #
        # is the Assembly executable.
        # ----------------------------------------------------

        project_directory = self.executable.parent.parent

        relative_backend = (
            self.executable.relative_to(
                project_directory
            )
        )

        # Convert Windows Path to DOS-style path
        backend_dos_path = str(
            relative_backend
        ).replace("/", "\\")

        # ----------------------------------------------------
        # Temporary files are mounted as D:
        # ----------------------------------------------------

        request_dos_path = r"D:\request.txt"
        response_dos_path = r"D:\response.txt"

        # ----------------------------------------------------
        # Assembly command
        # ----------------------------------------------------

        # DOSBox's mounted filesystem accepts the long filename here. Do not
        # invent an 8.3 alias: Windows may assign a different short name
        # depending on the files already present in the directory.
        executable_name = Path(relative_backend).name
        assembly_command = (
            f"{executable_name} "
            f"{request_dos_path} "
            f"{response_dos_path}"
        )

        # ----------------------------------------------------
        # Optional custom runner
        # ----------------------------------------------------

        if self.runner:
            runner = shlex.split(self.runner, posix=False)
            replacements = {
                "{exe}": str(self.executable),
                "{request}": str(request_path),
                "{response}": str(response_path),
                "{project}": str(project_directory),
                "{temp}": str(temporary_directory),
            }
            return [
                next(
                    (
                        argument.replace(token, value)
                        for token, value in replacements.items()
                        if token in argument
                    ),
                    argument,
                )
                for argument in runner
            ]

        # ----------------------------------------------------
        # DOSBox execution
        # ----------------------------------------------------

        return [
            self.dosbox,
            "-exit",
            "-c",
            f'mount c "{project_directory}"',
            "-c",
            f'mount d "{temporary_directory}"',
            "-c",
            "c:",
            "-c",
            "cd Backend",
            "-c",
            assembly_command,
            "-c",
            "exit",
        ]

    # ========================================================
    # RESPONSE PARSER
    # ========================================================

    @staticmethod
    def _parse_response(text):

        values = {}

        for line in text.splitlines():

            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1,
            )

            values[key.upper()] = value.strip()

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        try:

            status = int(
                values["STATUS"]
            )

        except (KeyError, ValueError) as error:

            raise AssemblyProtocolError(
                "Malformed Assembly response: "
                "STATUS is missing or invalid."
            ) from error

        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        try:

            data = bytes.fromhex(
                values.get("DATA", "")
            )

        except ValueError as error:

            raise AssemblyProtocolError(
                "Malformed Assembly response: "
                "DATA is not valid hexadecimal."
            ) from error

        # ----------------------------------------------------
        # CHECKSUM
        # ----------------------------------------------------

        checksum = values.get(
            "CHECKSUM",
            "",
        )

        return {
            "status": status,
            "data": data,
            "checksum": checksum,
        }

    # ========================================================
    # PUBLIC API
    # ========================================================

    def setup_master_password(
        self,
        password,
    ):

        return self._request(
            "SETUP",
            password,
        )

    def verify_master_password(
        self,
        password,
    ):

        self._request(
            "VERIFY",
            password,
        )

        return True

    def encrypt(
        self,
        password,
        data,
    ):

        response = self._request(
            "ENCRYPT",
            password,
            data,
        )

        return (
            response["data"],
            response["checksum"],
        )

    def decrypt(
        self,
        password,
        data,
        checksum,
    ):

        response = self._request(
            "DECRYPT",
            password,
            data,
            checksum,
        )

        return response["data"]

    def check(
        self,
        password,
        data,
        checksum,
    ):

        self._request(
            "CHECK",
            password,
            data,
            checksum,
        )

        return True


# ============================================================
# GLOBAL BRIDGE INSTANCE
# ============================================================

bridge = AssemblyBridge()