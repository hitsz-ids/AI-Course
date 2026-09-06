.equ SYS_WRITE,  1
.equ SYS_FORK,   2
.equ SYS_GETPID, 3
.equ SYS_EXIT,   4
.equ SYS_SLEEP,  5

.section .text
.global _start
.global sys_write
.global sys_fork
.global sys_getpid
.global sys_exit
.global sys_sleep

_start:
    bl main
    mov x0, #0
    b sys_exit

sys_write:
    mov x8, #SYS_WRITE
    svc #0
    ret

sys_fork:
    mov x8, #SYS_FORK
    svc #0
    ret

sys_getpid:
    mov x8, #SYS_GETPID
    svc #0
    ret

sys_sleep:
    mov x8, #SYS_SLEEP
    svc #0
    ret

sys_exit:
    mov x8, #SYS_EXIT
    svc #0
    b .
