// Minimal AArch64 kernel entry, exception vectors, and user-context helpers.
// The user program runs at EL0 and invokes system calls with `svc #0`.

.equ UART0_BASE, 0x09000000

// Offsets into struct task / struct trapframe. They must match kernel.c.
.equ TF_X0,      0
.equ TF_X8,      64
.equ TF_X9,      72
.equ TF_X18,     144
.equ TF_SP,      248
.equ TF_PC,      256
.equ TF_PSTATE,  264
.section .text

.global _start
_start:
    // Use SP_EL1 while executing in EL1.
    msr spsel, #1
    isb

    // Set up a temporary boot stack.
    adrp x0, boot_stack_top
    add x0, x0, :lo12:boot_stack_top
    mov sp, x0

    // Keep the MMU off and use the low exception vectors.
    msr sctlr_el1, xzr
    isb
    // Enable FP/SIMD for EL0 and EL1 so compiled C code can use NEON.
    mov x0, #(3 << 20)
    msr cpacr_el1, x0
    isb
    adrp x0, vectors
    add x0, x0, :lo12:vectors
    msr vbar_el1, x0
    isb

    bl kernel_main
    b .

// switch_to(struct context *prev, struct context *next)
// Saves x19-x30 and sp into prev->ctx, then restores next->ctx.
.global switch_to
switch_to:
    mov x9, sp
    str x9, [x0, #96]
    stp x19, x20, [x0]
    stp x21, x22, [x0, #16]
    stp x23, x24, [x0, #32]
    stp x25, x26, [x0, #48]
    stp x27, x28, [x0, #64]
    stp x29, x30, [x0, #80]

    ldr x9, [x1, #96]
    mov sp, x9
    ldp x19, x20, [x1]
    ldp x21, x22, [x1, #16]
    ldp x23, x24, [x1, #32]
    ldp x25, x26, [x1, #48]
    ldp x27, x28, [x1, #64]
    ldp x29, x30, [x1, #80]
    ret

.global ret_from_fork
ret_from_fork:
    b restore_user

.global restore_user
restore_user:
    adrp x9, current_task
    ldr x9, [x9, :lo12:current_task]

    // Restore exception-return state first.
    ldr x10, [x9, #TF_SP]
    msr sp_el0, x10
    ldr x10, [x9, #TF_PC]
    msr elr_el1, x10
    ldr x10, [x9, #TF_PSTATE]
    msr spsr_el1, x10

    // Restore user registers. x9 is the base pointer and is restored last.
    ldp x0, x1, [x9, #TF_X0]
    ldp x2, x3, [x9, #TF_X0+16]
    ldp x4, x5, [x9, #TF_X0+32]
    ldp x6, x7, [x9, #TF_X0+48]
    ldr x8, [x9, #TF_X8]
    ldp x10, x11, [x9, #TF_X0+80]
    ldp x12, x13, [x9, #TF_X0+96]
    ldp x14, x15, [x9, #TF_X0+112]
    ldp x16, x17, [x9, #TF_X0+128]
    ldr x18, [x9, #TF_X18]
    ldp x19, x20, [x9, #TF_X0+152]
    ldp x21, x22, [x9, #TF_X0+168]
    ldp x23, x24, [x9, #TF_X0+184]
    ldp x25, x26, [x9, #TF_X0+200]
    ldp x27, x28, [x9, #TF_X0+216]
    ldp x29, x30, [x9, #TF_X0+232]
    ldr x9, [x9, #TF_X9]
    eret

.macro SAVE_USER
    sub sp, sp, #16
    str x18, [sp]

    adrp x18, current_task
    ldr x18, [x18, :lo12:current_task]

    stp x0, x1, [x18, #TF_X0]
    stp x2, x3, [x18, #TF_X0+16]
    stp x4, x5, [x18, #TF_X0+32]
    stp x6, x7, [x18, #TF_X0+48]
    stp x8, x9, [x18, #TF_X0+64]
    stp x10, x11, [x18, #TF_X0+80]
    stp x12, x13, [x18, #TF_X0+96]
    stp x14, x15, [x18, #TF_X0+112]
    stp x16, x17, [x18, #TF_X0+128]
    stp x19, x20, [x18, #TF_X0+152]
    stp x21, x22, [x18, #TF_X0+168]
    stp x23, x24, [x18, #TF_X0+184]
    stp x25, x26, [x18, #TF_X0+200]
    stp x27, x28, [x18, #TF_X0+216]
    stp x29, x30, [x18, #TF_X0+232]

    ldr x17, [sp]
    add sp, sp, #16
    str x17, [x18, #TF_X18]

    mrs x17, sp_el0
    str x17, [x18, #TF_SP]
    mrs x17, elr_el1
    str x17, [x18, #TF_PC]
    mrs x17, spsr_el1
    str x17, [x18, #TF_PSTATE]
.endm

el0_sync:
    SAVE_USER
    adrp x0, current_task
    ldr x0, [x0, :lo12:current_task]
    bl syscall_dispatch
    b restore_user

hang:
    wfi
    b hang

// Exception vector table. Only the synchronous lower-EL entry at 0x400 is used
// here because this minimal kernel handles `svc` from EL0 and no interrupts.
.balign 0x800
vectors:
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b el0_sync
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80
    b hang
    .balign 0x80

.section .bss
.balign 16
.global boot_stack_top
boot_stack:
    .skip 0x20000
boot_stack_top:
