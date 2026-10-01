; SecureVault Assembly bridge contract.
; The final EMU8086 DOS executable must implement this request/response format.
;
; Request file:
;   COMMAND\r\n
;   PASSWORD=<uppercase hexadecimal UTF-8 bytes>\r\n
;   DATA=<uppercase hexadecimal bytes>\r\n
;   CHECKSUM=<four hexadecimal digits>\r\n
;
; Supported commands: SETUP, VERIFY, ENCRYPT, DECRYPT, CHECK.
; Response file:
;   STATUS=<numeric status>\r\n
;   DATA=<uppercase hexadecimal bytes>\r\n
;   CHECKSUM=<four hexadecimal digits>\r\n
;
; Status values: 0 success, 1 invalid request, 2 authentication failure,
; 3 checksum failure, 4 malformed data, 5 I/O failure.
;
; Include Encryption.asm in the EMU8086 build target and call its procedures.
; The DOS target must not print plaintext credentials or password material.