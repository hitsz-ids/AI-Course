CC = gcc
AS = as
LD = ld
OBJCOPY = objcopy

CFLAGS = -ffreestanding -fno-builtin -fno-stack-protector \
         -fno-pic -fno-pie -fomit-frame-pointer -O2 -Wall -Wextra
LDFLAGS = -nostdlib

all: minios.elf

user.bin: user.c user_start.S
	$(CC) $(CFLAGS) -c user.c -o user.o
	$(AS) -o user_start.o user_start.S
	$(LD) $(LDFLAGS) -Ttext=0x40200000 -e _start -o user.elf user_start.o user.o
	$(OBJCOPY) -O binary user.elf user.bin

user_blob.o: user.bin user_blob.S
	$(AS) -o user_blob.o user_blob.S

kernel.o: kernel.S
	$(AS) -o kernel.o kernel.S

kmain.o: kernel.c
	$(CC) $(CFLAGS) -c kernel.c -o kmain.o

minios.elf: kernel.o kmain.o user_blob.o
	$(LD) $(LDFLAGS) -Ttext=0x40000000 -e _start -o minios.elf kernel.o kmain.o user_blob.o

run: minios.elf
	qemu-system-aarch64 -M virt -cpu cortex-a72 -m 64 -nographic -semihosting -kernel minios.elf

clean:
	rm -f *.o *.elf *.bin

.PHONY: all run clean
