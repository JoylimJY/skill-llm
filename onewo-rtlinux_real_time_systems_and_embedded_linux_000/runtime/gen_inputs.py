import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create deeply nested distractor structure ---
dirs = [
    "servo_project/docs",
    "servo_project/legacy/v1",
    "servo_project/legacy/v2",
    "servo_project/tests/unit",
    "servo_project/tests/integration",
    "servo_project/build/obj",
    "servo_project/build/bin",
    "servo_project/configs",
    "servo_project/scripts",
    "servo_project/firmware/src",
    "servo_project/firmware/include",
    "servo_project/hal",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "servo_project/docs/architecture.md": "# Servo Controller Architecture\n\nThis document describes the high-level architecture of the servo controller.\n\n## Components\n- Control loop\n- HAL layer\n- Communication interface\n",
    "servo_project/docs/requirements.md": "# Requirements\n\n1. Periodic control at 1kHz\n2. Sub-millisecond jitter\n3. Hardware interrupt handling for encoder feedback\n",
    "servo_project/legacy/v1/servo_old.c": """\
#include <stdio.h>
#include <unistd.h>
int main() {
    while(1) {
        printf("old servo loop\\n");
        usleep(1000);
    }
    return 0;
}
""",
    "servo_project/legacy/v2/servo_v2.c": """\
#include <stdio.h>
#include <time.h>
int main() {
    struct timeval tv;
    while(1) {
        gettimeofday(&tv, NULL);
        printf("tick %ld\\n", tv.tv_sec);
    }
    return 0;
}
""",
    "servo_project/tests/unit/test_pid.c": """\
#include <assert.h>
void test_pid() { assert(1 == 1); }
int main() { test_pid(); return 0; }
""",
    "servo_project/tests/integration/test_loop.sh": "#!/bin/bash\necho 'Integration test placeholder'\n",
    "servo_project/configs/servo.conf": "[servo]\nperiod_us=1000\ncpu_core=2\npriority=90\n",
    "servo_project/scripts/deploy.sh": "#!/bin/bash\necho 'Deploy script placeholder'\n",
    "servo_project/build/obj/.gitkeep": "",
    "servo_project/build/bin/.gitkeep": "",
    "servo_project/firmware/include/servo_hal.h": """\
#ifndef SERVO_HAL_H
#define SERVO_HAL_H
#include <stdint.h>
#define REG_BASE  0xF0000000
#define REG_SIZE  0x1000
#define CTRL_OFF  0x00
#define STATUS_OFF 0x04
#endif
""",
    "servo_project/hal/hal_notes.txt": "HAL must use memory-mapped I/O for register access. ioctl is not permitted for performance-critical paths.\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM FILE: broken, non-compliant RT C code ---
broken_code = """\
/*
 * servo_controller_draft.c
 * Contractor draft - periodic servo control loop with encoder IRQ
 * DO NOT USE IN PRODUCTION - needs review
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <time.h>
#include <pthread.h>
#include <sched.h>
#include <signal.h>
#include <linux/interrupt.h>

/* Hardware register definitions */
#define REG_BASE    0xF0000000UL
#define REG_SIZE    0x1000
#define CTRL_OFFSET 0x00
#define STATUS_OFFSET 0x04

/* Control period: 1ms = 1,000,000 ns */
#define PERIOD_NS   1000000L

/* Encoder IRQ number (platform-specific) */
#define ENCODER_IRQ 47

static volatile int running = 1;
static int mem_fd = -1;

/* --- VIOLATION 1: uses ioctl for peripheral register writes --- */
static int ctrl_fd = -1;
#define SERVO_SET_TORQUE _IOW('S', 1, uint32_t)

static void write_servo_register(uint32_t value) {
    /* BAD: should use mmap, not ioctl */
    ioctl(ctrl_fd, SERVO_SET_TORQUE, &value);
}

/* --- VIOLATION 2: printf inside RT loop --- */
/* --- VIOLATION 3: gettimeofday for timing --- */
/* --- VIOLATION 4: busy-wait instead of clock_nanosleep --- */
/* --- VIOLATION 5: wrong scheduler priority (50, not 80-90) --- */
/* --- VIOLATION 6: clock_nanosleep at beginning of loop, not end --- */
/* --- VIOLATION 7: SCHED_RR instead of SCHED_FIFO --- */

static void* control_thread(void* arg) {
    /* Wrong scheduler policy: SCHED_RR instead of SCHED_FIFO */
    struct sched_param param;
    param.sched_priority = 50;  /* Wrong: should be 80-90 */
    pthread_setschedparam(pthread_self(), SCHED_RR, &param);

    /* Missing CPU affinity pinning */

    struct timeval tv_start;
    gettimeofday(&tv_start, NULL);  /* Wrong: should use clock_gettime(CLOCK_MONOTONIC) */

    struct timespec next;
    clock_gettime(CLOCK_MONOTONIC, &next);

    while (running) {
        /* sleep at the BEGINNING - WRONG: must be at the END */
        next.tv_nsec += PERIOD_NS;
        if (next.tv_nsec >= 1000000000L) {
            next.tv_nsec -= 1000000000L;
            next.tv_sec++;
        }
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next, NULL);

        /* BAD: printf inside loop */
        printf("Servo tick: pos=%d\\n", 0);

        /* BAD: ioctl peripheral access */
        write_servo_register(0xDEADBEEF);

        /* BAD: busy-wait spin */
        volatile int spin = 0;
        while (spin < 1000) spin++;
    }

    return NULL;
}

/* --- VIOLATION 8: hard IRQ handler uses printk (kernel-style bad practice shown in userspace comment) --- */
/* --- VIOLATION 9: request_irq instead of request_threaded_irq --- */

/*
 * NOTE for kernel module part (to be integrated):
 *
 * BAD kernel IRQ registration:
 *   request_irq(ENCODER_IRQ, encoder_hard_handler, IRQF_SHARED, "encoder", dev);
 *
 * BAD hard handler:
 *   irqreturn_t encoder_hard_handler(int irq, void *dev) {
 *       printk(KERN_INFO "encoder IRQ fired\\n");   <- prohibited in hard handler
 *       return IRQ_HANDLED;
 *   }
 *
 * Missing: irq_set_affinity to bind encoder IRQ to isolated core
 */

static void signal_handler(int sig) {
    running = 0;
}

int main(int argc, char *argv[]) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    /* Open /dev/mem for mmap (not actually used - ioctl used instead) */
    mem_fd = open("/dev/mem", O_RDWR | O_SYNC);

    ctrl_fd = open("/dev/servo_ctrl", O_RDWR);

    pthread_t ctrl_tid;
    pthread_create(&ctrl_tid, NULL, control_thread, NULL);
    pthread_join(ctrl_tid, NULL);

    if (mem_fd >= 0) close(mem_fd);
    if (ctrl_fd >= 0) close(ctrl_fd);
    return 0;
}
"""

problem_file_path = os.path.join(WORKSPACE, "servo_project/firmware/src/servo_controller_draft.c")
with open(problem_file_path, "w") as f:
    f.write(broken_code)

print(f"Workspace created at {WORKSPACE}")
print(f"Problem file: {problem_file_path}")
print(f"Total distractor files: {len(distractors)}")