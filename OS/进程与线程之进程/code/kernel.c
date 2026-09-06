#include <stdint.h>

#define UART0_BASE 0x09000000UL
#define USER_CODE_BASE 0x40200000UL

#define MAX_TASKS 4
#define KSTACK_SIZE 0x4000
#define USTACK_SIZE 0x10000

#define SYS_WRITE  1
#define SYS_FORK   2
#define SYS_GETPID 3
#define SYS_EXIT   4
#define SYS_SLEEP  5

#define TASK_FREE      0
#define TASK_READY     1
#define TASK_SLEEPING  2
#define TASK_EXITED    3

struct trapframe {
    uint64_t x[31];
    uint64_t sp_el0;
    uint64_t elr_el1;
    uint64_t spsr_el1;
};

struct context {
    uint64_t x19;
    uint64_t x20;
    uint64_t x21;
    uint64_t x22;
    uint64_t x23;
    uint64_t x24;
    uint64_t x25;
    uint64_t x26;
    uint64_t x27;
    uint64_t x28;
    uint64_t x29;
    uint64_t x30;
    uint64_t sp;
};

struct task {
    struct trapframe tf;
    struct context ctx;
    uint64_t user_sp;
    uint64_t user_stack_base;
    uint64_t user_stack_top;
    uint64_t sleep_until;
    int pid;
    int state;
    int exit_code;
    int pad;
    struct task *parent;
};

extern char user_bin_start[];
extern char user_bin_end[];
extern void switch_to(struct context *prev, struct context *next);
extern void ret_from_fork(void);

struct task tasks[MAX_TASKS];
struct task idle_task;

static uint8_t kstacks[MAX_TASKS][KSTACK_SIZE] __attribute__((aligned(16)));
static uint8_t ustacks[MAX_TASKS][USTACK_SIZE] __attribute__((aligned(16)));
static uint8_t idle_stack[KSTACK_SIZE] __attribute__((aligned(16)));

struct task *current_task;
static uint64_t ticks;
static int last_user_task;
static int next_pid = 1;

static void copy_memory(void *dst, const void *src, uint64_t len) {
    uint8_t *d = dst;
    const uint8_t *s = src;
    for (uint64_t i = 0; i < len; i++) d[i] = s[i];
}

static void zero_memory(void *dst, uint64_t len) {
    uint8_t *d = dst;
    for (uint64_t i = 0; i < len; i++) d[i] = 0;
}

static volatile uint32_t *const UARTFR = (volatile uint32_t *)(UART0_BASE + 0x18);
static volatile uint32_t *const UARTDR = (volatile uint32_t *)(UART0_BASE + 0x00);

static void uart_putc(char c) {
    if (c == '\n') uart_putc('\r');
    while (*UARTFR & (1U << 5)) { }
    *UARTDR = (uint32_t)(unsigned char)c;
}

static void uart_puts(const char *s) {
    while (*s) uart_putc(*s++);
}

static int uart_has_char(void) {
    return ((*UARTFR & (1U << 4)) == 0);
}

static char uart_getc(void) {
    return (char)(*UARTDR & 0xff);
}

static void semihost_exit(int status) {
    register uint64_t x0 asm("x0") = 0x18; // SYS_EXIT
    register uint64_t x1 asm("x1") = (uint64_t)status;
    asm volatile("hlt #0xf000" : : "r"(x0), "r"(x1) : "memory");
    __builtin_unreachable();
}

static void init_context(struct context *ctx, void (*entry)(void), uint8_t *stack_top) {
    zero_memory(ctx, sizeof(*ctx));
    ctx->sp = (uint64_t)stack_top;
    ctx->x30 = (uint64_t)entry;
}

static void tick(void) {
    ticks++;
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks[i].state == TASK_SLEEPING && tasks[i].sleep_until <= ticks) {
            tasks[i].state = TASK_READY;
        }
    }
}

static struct task *pick_next(void) {
    tick();

    for (int n = 0; n < MAX_TASKS; n++) {
        int i = (last_user_task + n) % MAX_TASKS;
        if (tasks[i].state == TASK_READY) {
            last_user_task = (i + 1) % MAX_TASKS;
            return &tasks[i];
        }
    }

    return &idle_task;
}

static void schedule(void) {
    struct task *prev = current_task;
    struct task *next = pick_next();

    if (next == prev) return;

    current_task = next;
    switch_to(&prev->ctx, &next->ctx);
}

static int user_tasks_remaining(void) {
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks[i].state != TASK_FREE && tasks[i].state != TASK_EXITED) {
            return 1;
        }
    }
    return 0;
}

static void idle_entry(void) {
    static int idle_announced;

    while (1) {
        if (!idle_announced && !user_tasks_remaining()) {
            idle_announced = 1;
            uart_puts("OS idle: all user processes stopped. Press q to exit OS.\n");
        }

        if (!user_tasks_remaining()) {
            if (uart_has_char()) {
                char c = uart_getc();
                uart_putc(c);
                if (c == 'q' || c == 'Q') {
                    semihost_exit(0);
                }
            }
        }

        schedule();
    }
}

static struct task *alloc_task(void) {
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks[i].state == TASK_FREE) return &tasks[i];
    }
    return 0;
}

static void sys_fork(struct task *parent) {
    struct task *child = alloc_task();
    if (!child) {
        parent->tf.x[0] = (uint64_t)-1;
        return;
    }

    int idx = (int)(child - tasks);
    child->pid = next_pid++;
    child->state = TASK_READY;
    child->parent = parent;
    child->user_stack_base = (uint64_t)&ustacks[idx][0];
    child->user_stack_top = (uint64_t)&ustacks[idx][USTACK_SIZE];

    uint64_t parent_sp = parent->tf.sp_el0;
    uint64_t used = parent->user_stack_top - parent_sp;
    if (parent_sp < parent->user_stack_base ||
        parent_sp > parent->user_stack_top ||
        used > USTACK_SIZE) {
        child->state = TASK_FREE;
        parent->tf.x[0] = (uint64_t)-1;
        return;
    }

    child->user_sp = child->user_stack_top - used;
    copy_memory((void *)child->user_sp, (const void *)parent_sp, used);
    copy_memory(&child->tf, &parent->tf, sizeof(child->tf));
    child->tf.x[0] = 0;
    child->tf.sp_el0 = child->user_sp;

    init_context(&child->ctx, (void (*)(void))ret_from_fork, &kstacks[idx][KSTACK_SIZE]);

    parent->tf.x[0] = (uint64_t)child->pid;
}

void syscall_dispatch(struct task *t) {
    current_task = t;
    uint64_t nr = t->tf.x[8];

    switch (nr) {
    case SYS_WRITE: {
        int fd = (int)t->tf.x[0];
        const char *buf = (const char *)t->tf.x[1];
        uint64_t len = t->tf.x[2];
        uint64_t written = 0;
        if (fd == 1) {
            for (uint64_t i = 0; i < len; i++) uart_putc(buf[i]);
            written = len;
        }
        t->tf.x[0] = written;
        break;
    }
    case SYS_FORK:
        sys_fork(t);
        break;
    case SYS_GETPID:
        t->tf.x[0] = (uint64_t)t->pid;
        break;
    case SYS_SLEEP:
        t->state = TASK_SLEEPING;
        t->sleep_until = ticks + t->tf.x[0];
        t->tf.x[0] = 0;
        break;
    case SYS_EXIT:
        t->state = TASK_EXITED;
        t->exit_code = (int)t->tf.x[0];
        break;
    default:
        t->tf.x[0] = (uint64_t)-1;
        break;
    }

    schedule();
}

void kernel_main(void) {
    zero_memory(tasks, sizeof(tasks));
    zero_memory(&idle_task, sizeof(idle_task));
    zero_memory(kstacks, sizeof(kstacks));
    zero_memory(ustacks, sizeof(ustacks));
    zero_memory(idle_stack, sizeof(idle_stack));

    uint64_t user_size = (uint64_t)(user_bin_end - user_bin_start);
    copy_memory((void *)USER_CODE_BASE, user_bin_start, user_size);
    asm volatile("ic iallu; dsb sy; isb" : : : "memory");

    // The idle task keeps the OS alive after all user processes exit.
    idle_task.state = TASK_READY;
    init_context(&idle_task.ctx, idle_entry, &idle_stack[KSTACK_SIZE]);

    struct task *parent = &tasks[0];
    parent->pid = next_pid++;
    parent->state = TASK_READY;
    parent->user_stack_base = (uint64_t)&ustacks[0][0];
    parent->user_stack_top = (uint64_t)&ustacks[0][USTACK_SIZE];
    parent->user_sp = parent->user_stack_top;
    parent->tf.sp_el0 = parent->user_stack_top;
    parent->tf.elr_el1 = USER_CODE_BASE;
    parent->tf.spsr_el1 = 0;
    init_context(&parent->ctx, (void (*)(void))ret_from_fork, &kstacks[0][KSTACK_SIZE]);

    struct context boot_ctx;
    current_task = parent;
    uart_puts("Mini OS booted.\n");
    switch_to(&boot_ctx, &parent->ctx);
    __builtin_unreachable();
}
