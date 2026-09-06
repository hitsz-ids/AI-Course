## 1. 哪部分是 bootloader / 内核启动代码

现在的代码已经不只是单纯 bootloader，而是“启动 + 最小内核入口”。核心汇编在 [kernel.S](/home/codex/minios/kernel.S)。

### 启动入口 `_start`

位置：[kernel.S (line 16)](/home/codex/minios/kernel.S:16)

```
_start:
    msr spsel, #1
    isb

    adrp x0, boot_stack_top
    add x0, x0, :lo12:boot_stack_top
    mov sp, x0

    msr sctlr_el1, xzr
    isb

    mov x0, #(3 << 20)
    msr cpacr_el1, x0
    isb

    adrp x0, vectors
    add x0, x0, :lo12:vectors
    msr vbar_el1, x0
    isb

    bl kernel_main
    b .
```

理解：

- `msr spsel, #1`：让 EL1 使用 `SP_EL1`。
- 设置启动栈到 `boot_stack_top`。
- `sctlr_el1 = 0`：关闭 MMU，当前最小 OS 使用物理地址直接执行。
- `cpacr_el1 = 3 << 20`：允许 EL0/EL1 使用 FP/SIMD，避免 C 编译出的 NEON 指令触发异常。
- 把异常向量表地址写入 `vbar_el1`。
- 最后跳到 C 代码 `kernel_main`。

这一整段就是系统启动后的第一条执行路径，也就是 bootloader/内核入口。

### 异常向量表

位置：[kernel.S (line 150)](/home/codex/minios/kernel.S:150)

```
vectors:
    b hang
    ...
    b el0_sync
    ...
```

理解：

- 这个最小 OS 只处理 EL0 发起的同步异常，也就是用户态执行 `svc #0`。
- `el0_sync` 就是系统调用入口。

### 用户上下文保存和恢复

位置：

- `SAVE_USER`：[kernel.S (line 102)](/home/codex/minios/kernel.S:102)
- `restore_user`：[kernel.S (line 69)](/home/codex/minios/kernel.S:69)

理解：

- `SAVE_USER` 把 `x0-x30`、`sp_el0`、`elr_el1`、`spsr_el1` 保存到当前进程的 `trapframe`。
- `restore_user` 把这些状态恢复回来，最后执行 `eret` 返回 EL0。
- `elr_el1` 保存的是用户态被中断时的下一条指令地址，所以 `eret` 能回到 `svc` 后面的指令。

------

## 2. 哪部分是 fork 相关汇编和内核实现

### 用户态 fork 系统调用桩

位置：[user_start.S (line 25)](/home/codex/minios/user_start.S:25)

```
sys_fork:
    mov x8, #SYS_FORK
    svc #0
    ret
```

理解：

- `x8 = 2`，这是本项目自定义的系统调用号。
- `svc #0` 让 CPU 进入 EL1，执行我们自己的 `el0_sync`。
- 这不是 Linux 的 `fork()`。

### 内核态 fork 实现

位置：[kernel.c (line 192)](/home/codex/minios/kernel.c:192)

关键逻辑：

```
static void sys_fork(struct task *parent) {
    struct task *child = alloc_task();

    child->pid = next_pid++;
    child->state = TASK_READY;
    child->parent = parent;

    child->user_stack_base = ...;
    child->user_stack_top = ...;

    uint64_t parent_sp = parent->tf.sp_el0;
    uint64_t used = parent->user_stack_top - parent_sp;

    child->user_sp = child->user_stack_top - used;
    copy_memory((void *)child->user_sp, (const void *)parent_sp, used);

    copy_memory(&child->tf, &parent->tf, sizeof(child->tf));
    child->tf.x[0] = 0;
    child->tf.sp_el0 = child->user_sp;

    init_context(&child->ctx, ret_from_fork, ...);

    parent->tf.x[0] = child->pid;
}
```

理解：

- 从空闲任务表分配一个子任务。
- 复制父进程当前用户栈到子进程自己的栈空间。
- 复制父进程的 `trapframe`。
- 子进程 `x0 = 0`，所以子进程从 `fork()` 返回 0。
- 父进程 `x0 = child->pid`，所以父进程从 `fork()` 返回子进程 PID。
- 子进程内核上下文入口设置成 `ret_from_fork`。

### 任务切换汇编

位置：[kernel.S (line 42)](/home/codex/minios/kernel.S:42)

```
switch_to:
    mov x9, sp
    str x9, [x0, #96]

    stp x19, x20, [x0]
    ...
    stp x29, x30, [x0, #80]

    ldr x9, [x1, #96]
    mov sp, x9

    ldp x19, x20, [x1]
    ...
    ldp x29, x30, [x1, #80]
    ret
```

理解：

- 保存当前任务需要跨函数调用保留的寄存器 `x19-x30` 和栈指针。
- 恢复下一个任务的这些寄存器。
- `ret` 会跳到下一个任务之前保存的 `x30`，从而恢复其执行流。

新任务第一次被调度时，`x30` 被初始化成：

```
ret_from_fork:
    b restore_user
```

位置：[kernel.S (line 65)](/home/codex/minios/kernel.S:65)

所以子进程第一次被切换到时，会进入 `restore_user`，恢复用户寄存器并 `eret` 到用户态。

------

## 3. 哪部分是用户态程序代码

用户态有两部分：

### 用户态启动和系统调用桩

文件：[user_start.S](/home/codex/minios/user_start.S)

```
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
```

理解：

- `_start` 是用户态真正入口，先调用 C 语言的 `main`。
- `main` 如果正常返回，则自动执行 `sys_exit(0)`。
- 每个 `sys_*` 函数只做一件事：设置 `x8` 系统调用号，然后执行 `svc #0`。

### 用户态 C 主程序

文件：[user.c](/home/codex/minios/user.c)

核心：

```
int main(void) {
    long pid = sys_fork();

    if (pid == 0) {
        // 子进程：输出 6 次，然后退出
        for (int i = 0; i < 6; i++) {
            ...
            sys_write(1, line, n);
            sys_sleep(20);
        }
        sys_exit(0);
    } else {
        // 父进程：输出 6 次，然后退出
        for (int i = 0; i < 6; i++) {
            ...
            sys_write(1, line, n);
            sys_sleep(20);
        }
        sys_exit(0);
    }
}
```

理解：

- 这就是你要求的用户态 `testfork` 程序。
- `main` 是入口。
- `fork`、`write`、`getpid`、`sleep`、`exit` 全部通过我们自己的 `svc` 进入内核。

------

## 4. 如何确定不是直接使用宿主系统调用

可以从构建方式、运行方式、指令路径、系统调用号四个角度证明。

### 4.1 编译时没有链接宿主 libc

看 [Makefile (line 6)](/home/codex/minios/Makefile:6)：

```
CFLAGS = -ffreestanding -fno-builtin -fno-stack-protector \
         -fno-pic -fno-pie -fomit-frame-pointer -O2 -Wall -Wextra
LDFLAGS = -nostdlib
```

关键：

- `-ffreestanding`：告诉编译器这是独立环境，不依赖宿主 C 库。
- `-nostdlib`：不链接 Linux 的 `libc`、`crt0`、动态链接器。
- `-fno-builtin`：不使用编译器自动替换成宿主 `memcpy`、`printf` 等函数。

所以用户态代码里没有调用宿主系统的 `fork`、`write`、`getpid`。

### 4.2 用户程序不是宿主进程，而是 QEMU 虚拟机里的裸二进制

看 [Makefile (line 12)](/home/codex/minios/Makefile:12)：

```
user.bin: user.c user_start.S
	$(CC) ... -c user.c -o user.o
	$(AS) -o user_start.o user_start.S
	$(LD) ... -Ttext=0x40200000 -e _start -o user.elf user_start.o user.o
	$(OBJCOPY) -O binary user.elf user.bin
```

理解：

- 用户程序被编译成 ELF。
- 然后用 `objcopy -O binary` 转成纯二进制 `user.bin`。
- 它不是一个在 Linux 上运行的进程，而是被嵌入到 `minios.elf` 里的裸机代码。

嵌入方式在 [user_blob.S](/home/codex/minios/user_blob.S)：

```
user_bin_start:
    .incbin "user.bin"
user_bin_end:
```

内核启动时把它复制到固定用户代码地址：

位置：[kernel.c (line 274)](/home/codex/minios/kernel.c:274)

```
copy_memory((void *)USER_CODE_BASE, user_bin_start, user_size);
```

所以用户程序运行在 QEMU 的 ARM 虚拟 CPU 上，而不是运行在宿主 Linux 用户态。

### 4.3 系统调用通过自己的 `svc` 和异常向量进入内核

用户态调用：

```
sys_fork:
    mov x8, #SYS_FORK
    svc #0
    ret
```

`svc #0` 会让 CPU 跳到我们设置的 `vbar_el1` 向量表：

位置：[kernel.S (line 168)](/home/codex/minios/kernel.S:168)

```
b el0_sync
```

然后进入：

```
el0_sync:
    SAVE_USER
    bl syscall_dispatch
    b restore_user
```

位置：[kernel.S (line 137)](/home/codex/minios/kernel.S:137)

也就是说，用户程序的所有系统调用都进入我们自己编写的 `syscall_dispatch`，而不是宿主 Linux 内核。

### 4.4 系统调用号不是 Linux 系统调用号

本项目自定义：

```
#define SYS_WRITE  1
#define SYS_FORK   2
#define SYS_GETPID 3
#define SYS_EXIT   4
#define SYS_SLEEP  5
```

Linux AArch64 的真实系统调用号不是这样：

- Linux `write` 通常是 64
- Linux `fork` 通常是 220
- Linux `getpid` 通常是 172
- Linux `exit` 通常是 93
- Linux 没有我们这里的 `SYS_SLEEP=5`

所以即使代码看起来叫 `sys_fork`，实际进入的是我们自己定义的内核，不是宿主系统调用。

------

## 5. 详细流程图

### 构建流程

```
user.c + user_start.S
        |
        v
    user.elf
        |
        | objcopy -O binary
        v
    user.bin
        |
        | user_blob.S: .incbin "user.bin"
        v
    user_blob.o
        |
        | 链接进内核
        v
kernel.S + kernel.c + user_blob.o
        |
        v
    minios.elf
        |
        | qemu-system-aarch64 -kernel minios.elf
        v
   QEMU 从 _start 开始执行
```

### 启动和进入用户态流程

```
QEMU reset
  |
  v
kernel.S: _start
  |
  +-- 设置 EL1 栈、异常向量、FP/SIMD
  |
  v
kernel.c: kernel_main()
  |
  +-- 初始化任务表、内核栈、用户栈
  +-- 把 user.bin 复制到 0x40200000
  +-- 创建父进程 task[0]
  +-- 创建 idle_task
  |
  v
switch_to(boot_ctx, parent.ctx)
  |
  v
parent.ctx.x30 = ret_from_fork
  |
  v
restore_user
  |
  v
eret 到 EL0
  |
  v
user_start.S: _start
  |
  v
user.c: main()
```

### fork 系统调用流程

```
EL0 用户态
  |
  v
sys_fork()
  |
  +-- mov x8, #2
  +-- svc #0
  |
  v
EL1 异常向量 el0_sync
  |
  +-- SAVE_USER
  |
  v
syscall_dispatch()
  |
  +-- nr = current->tf.x[8]
  +-- nr == SYS_FORK
  |
  v
sys_fork(parent)
  |
  +-- alloc_task()
  +-- child.pid = next_pid++
  +-- 复制父进程用户栈
  +-- child.tf.x[0] = 0
  +-- parent.tf.x[0] = child.pid
  +-- child.ctx.x30 = ret_from_fork
  |
  v
schedule()
  |
  +-- pick_next()
  +-- switch_to(parent.ctx, child.ctx)
  |
  v
ret_from_fork -> restore_user
  |
  v
子进程在 EL0 继续执行，fork() 返回 0
```

### 父进程和子进程轮流输出流程

```
父进程 main()
  |
  +-- sys_fork()
  +-- 输出一行
  +-- sys_sleep(20)
         |
         v
      schedule()
         |
         +-- 父进程变为 SLEEPING
         +-- 切换到子进程
         |
         v
      子进程输出一行
         |
         +-- sys_sleep(20)
         |
         v
      schedule()
         |
         +-- 子进程变为 SLEEPING
         +-- 切换回父进程或 idle
```

### 进程退出后等待 q 的流程

```
父进程 sys_exit(0)
  |
  v
task.state = TASK_EXITED
  |
  v
schedule()
  |
  v
子进程 sys_exit(0)
  |
  v
task.state = TASK_EXITED
  |
  v
schedule()
  |
  v
idle_entry()
  |
  +-- 所有用户任务已退出
  +-- 输出：Press q to exit OS
  |
  +-- 轮询 UART
  |
  v
用户输入 q
  |
  v
semihost_exit(0)
  |
  v
QEMU 退出
```

------

## 6. 代码 review 总结

当前实现是一个可运行的最小 OS，优点：

- 启动、异常、上下文切换、用户态、系统调用边界清晰。
- `fork` 思路正确：复制用户栈 + 复制 trapframe + 父/子返回不同 PID。
- 用户态程序是真正的 EL0 裸机程序，不依赖宿主 libc。
- 通过 idle 任务实现了进程退出后 OS 仍存活，并通过 `q` 退出 OS。

当前作为最小 OS 的限制：

- 没有 MMU/页表，用户态和内核共享同一物理地址空间。
- `fork` 只复制用户栈，代码段和只读数据段共享。
- 调度器是协作式 tick 调度，`sleep` 不是硬件定时器驱动的抢占式休眠。
- 只处理 EL0 同步异常，未处理 IRQ、page fault、非法指令等。
- 内核访问用户指针时没有做地址合法性检查。