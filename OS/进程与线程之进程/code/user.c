typedef unsigned long u64;

extern long sys_write(long fd, const char *buf, long len);
extern long sys_fork(void);
extern long sys_getpid(void);
extern void sys_exit(long status);
extern void sys_sleep(long ticks);

static void put_str(char *buf, int *pos, const char *s) {
    while (*s) {
        if (*pos < 127) buf[(*pos)++] = *s;
        s++;
    }
}

static void put_u64(char *buf, int *pos, u64 v) {
    char tmp[24];
    int n = 0;

    if (v == 0) {
        tmp[n++] = '0';
    } else {
        while (v && n < (int)sizeof(tmp) - 1) {
            tmp[n++] = (char)('0' + (v % 10));
            v /= 10;
        }
    }

    while (n > 0 && *pos < 127) {
        buf[(*pos)++] = tmp[--n];
    }
}

int main(void) {
    long pid = sys_fork();

    if (pid < 0) {
        sys_write(1, "fork failed\n", 12);
        sys_exit(1);
    }

    if (pid == 0) {
        for (int i = 0; i < 6; i++) {
            char line[128];
            int n = 0;
            put_str(line, &n, "child: pid=");
            put_u64(line, &n, (u64)sys_getpid());
            put_str(line, &n, ", tick=");
            put_u64(line, &n, (u64)i);
            line[n++] = '\n';
            sys_write(1, line, n);
            sys_sleep(20);
        }
        sys_write(1, "child exiting\n", 14);
        sys_exit(0);
    } else {
        for (int i = 0; i < 6; i++) {
            char line[128];
            int n = 0;
            put_str(line, &n, "parent: pid=");
            put_u64(line, &n, (u64)sys_getpid());
            put_str(line, &n, ", child pid=");
            put_u64(line, &n, (u64)pid);
            put_str(line, &n, ", tick=");
            put_u64(line, &n, (u64)i);
            line[n++] = '\n';
            sys_write(1, line, n);
            sys_sleep(20);
        }
        sys_write(1, "parent exiting\n", 15);
        sys_exit(0);
    }

    return 0;
}
