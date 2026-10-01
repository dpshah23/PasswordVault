; ============================================================
; SecureVault - Master Password Module
; 8086 Assembly
;
; Functions:
;   1. Create master password
;   2. Verify master password
;   3. Generate password checksum
;   4. Compare checksum
;
; Designed for EMU8086
; ============================================================

.MODEL SMALL
.STACK 100H

.DATA

; ------------------------------------------------------------
; Messages
; ------------------------------------------------------------

title_msg       DB 13,10
                DB '========================================',13,10
                DB '          SECUREVAULT - 8086',13,10
                DB '          MASTER PASSWORD',13,10
                DB '========================================',13,10,'$'

create_msg      DB 13,10
                DB 'Create Master Password: $'

confirm_msg     DB 13,10
                DB 'Confirm Master Password: $'

login_msg       DB 13,10
                DB 'Enter Master Password: $'

success_msg     DB 13,10
                DB 13,10
                DB '[+] Master password verified!',13,10
                DB '    Vault unlocked.',13,10,'$'

failure_msg     DB 13,10
                DB 13,10
                DB '[-] Incorrect master password!',13,10
                DB '    Vault remains locked.',13,10,'$'

match_msg       DB 13,10
                DB '[+] Passwords match.',13,10,'$'

mismatch_msg    DB 13,10
                DB '[-] Passwords do not match.',13,10,'$'

newline         DB 13,10,'$'


; ------------------------------------------------------------
; Password buffers
;
; DOS function 0Ah format:
;
; byte 0 = maximum characters
; byte 1 = number of characters entered
; byte 2... = characters
; ------------------------------------------------------------

password1       DB 32
                DB 0
                DB 32 DUP(0)

password2       DB 32
                DB 0
                DB 32 DUP(0)

login_password  DB 32
                DB 0
                DB 32 DUP(0)


; ------------------------------------------------------------
; Stored password checksum
; ------------------------------------------------------------

stored_checksum DW 0

current_checksum DW 0


.CODE

; ============================================================
; MAIN
; ============================================================

MAIN PROC

    MOV AX, @DATA
    MOV DS, AX

    LEA DX, title_msg
    MOV AH, 09H
    INT 21H

    ; --------------------------------------------------------
    ; Create master password
    ; --------------------------------------------------------

    LEA DX, create_msg
    MOV AH, 09H
    INT 21H

    LEA DX, password1
    CALL READ_PASSWORD


    ; --------------------------------------------------------
    ; Confirm password
    ; --------------------------------------------------------

    LEA DX, confirm_msg
    MOV AH, 09H
    INT 21H

    LEA DX, password2
    CALL READ_PASSWORD


    ; --------------------------------------------------------
    ; Compare passwords
    ; --------------------------------------------------------

    LEA SI, password1
    LEA DI, password2

    CALL COMPARE_PASSWORDS

    CMP AL, 1
    JNE PASSWORD_MISMATCH


PASSWORD_MATCH:

    LEA DX, match_msg
    MOV AH, 09H
    INT 21H

    ; --------------------------------------------------------
    ; Generate checksum
    ; --------------------------------------------------------

    LEA SI, password1
    CALL GENERATE_CHECKSUM

    MOV stored_checksum, AX

    JMP TEST_LOGIN


PASSWORD_MISMATCH:

    LEA DX, mismatch_msg
    MOV AH, 09H
    INT 21H

    JMP EXIT_PROGRAM


; ============================================================
; TEST LOGIN
;
; This simulates the second stage:
; user enters master password again.
; ============================================================

TEST_LOGIN:

    LEA DX, login_msg
    MOV AH, 09H
    INT 21H

    LEA DX, login_password
    CALL READ_PASSWORD


    ; --------------------------------------------------------
    ; Calculate checksum of entered password
    ; --------------------------------------------------------

    LEA SI, login_password
    CALL GENERATE_CHECKSUM

    MOV current_checksum, AX


    ; --------------------------------------------------------
    ; Compare with stored checksum
    ; --------------------------------------------------------

    MOV AX, current_checksum
    CMP AX, stored_checksum

    JE LOGIN_SUCCESS

    JMP LOGIN_FAILURE


; ============================================================
; LOGIN SUCCESS
; ============================================================

LOGIN_SUCCESS:

    LEA DX, success_msg
    MOV AH, 09H
    INT 21H

    JMP EXIT_PROGRAM


; ============================================================
; LOGIN FAILURE
; ============================================================

LOGIN_FAILURE:

    LEA DX, failure_msg
    MOV AH, 09H
    INT 21H

    JMP EXIT_PROGRAM


; ============================================================
; READ_PASSWORD
;
; Input:
;   DS:DX -> password buffer
;
; Uses DOS buffered input.
;
; For this first version the characters are not yet masked.
; We will add '*' masking in the next version.
; ============================================================

READ_PASSWORD PROC

    MOV AH, 0AH
    INT 21H

    RET

READ_PASSWORD ENDP


; ============================================================
; COMPARE_PASSWORDS
;
; Input:
;   DS:SI -> first password buffer
;   DS:DI -> second password buffer
;
; Output:
;   AL = 1  -> match
;   AL = 0  -> mismatch
; ============================================================

COMPARE_PASSWORDS PROC

    PUSH BX
    PUSH CX
    PUSH DX
    PUSH SI
    PUSH DI

    ; Get first password length

    MOV BL, [SI + 1]

    ; Get second password length

    MOV BH, [DI + 1]

    ; Compare lengths

    CMP BL, BH
    JNE PASSWORDS_DIFFERENT

    ; Number of characters

    MOV CL, BL
    MOV CH, 0

    ; Move to actual character data

    ADD SI, 2
    ADD DI, 2

    ; Empty password

    CMP CX, 0
    JE PASSWORDS_EQUAL

COMPARE_LOOP:

    MOV AL, [SI]
    MOV DL, [DI]

    CMP AL, DL
    JNE PASSWORDS_DIFFERENT

    INC SI
    INC DI

    LOOP COMPARE_LOOP


PASSWORDS_EQUAL:

    MOV AL, 1
    JMP COMPARE_DONE


PASSWORDS_DIFFERENT:

    MOV AL, 0


COMPARE_DONE:

    POP DI
    POP SI
    POP DX
    POP CX
    POP BX

    RET

COMPARE_PASSWORDS ENDP


; ============================================================
; GENERATE_CHECKSUM
;
; Input:
;   DS:SI -> password buffer
;
; Output:
;   AX -> 16-bit checksum
;
; Educational checksum:
;
;   checksum = checksum + ASCII(character)
;
;   then rotate left by 1 bit.
;
; This is NOT cryptographically secure hashing.
; It is an Assembly demonstration for the project.
; ============================================================

GENERATE_CHECKSUM PROC

    PUSH BX
    PUSH CX
    PUSH DX
    PUSH SI

    XOR AX, AX

    ; Password length

    MOV CL, [SI + 1]
    MOV CH, 0

    ; Move to password characters

    ADD SI, 2

    CMP CX, 0
    JE CHECKSUM_DONE


CHECKSUM_LOOP:

    ; Get character

    XOR BH, BH
    MOV BL, [SI]

    ; Add ASCII value

    ADD AX, BX

    ; Rotate checksum left

    ROL AX, 1

    INC SI

    LOOP CHECKSUM_LOOP


CHECKSUM_DONE:

    POP SI
    POP DX
    POP CX
    POP BX

    RET

GENERATE_CHECKSUM ENDP


; ============================================================
; EXIT
; ============================================================

EXIT_PROGRAM:

    LEA DX, newline
    MOV AH, 09H
    INT 21H

    MOV AH, 4CH
    MOV AL, 00H
    INT 21H


END MAIN