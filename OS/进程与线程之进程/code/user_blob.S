.section .rodata
.balign 16
.global user_bin_start
.global user_bin_end
user_bin_start:
    .incbin "user.bin"
user_bin_end:
