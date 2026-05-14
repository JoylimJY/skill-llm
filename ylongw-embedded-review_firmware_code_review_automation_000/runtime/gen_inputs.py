#!/usr/bin/env python3
"""
Generate a realistic embedded firmware repo workspace for the embedded-review skill task.
The repo contains NFC + DMA + ISR firmware code with intentional bugs introduced in a branch.
"""
import os
import subprocess
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─── Directory skeleton ───────────────────────────────────────────────────────
dirs = [
    "firmware-nfc/src/nfc",
    "firmware-nfc/src/hal",
    "firmware-nfc/src/rtos",
    "firmware-nfc/src/crypto",
    "firmware-nfc/src/utils",
    "firmware-nfc/include",
    "firmware-nfc/tests",
    "firmware-nfc/docs",
    "firmware-nfc/build",
    "scripts",
    "references",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files (noise / context) ───────────────────────────────────────
distractors = {
    "firmware-nfc/docs/design_notes.txt": "NFC ISO14443A stack design. See datasheets/PN7150.\n",
    "firmware-nfc/docs/changelog.txt": "v0.9.1 - fix uart baud\nv0.9.2 - add NFC init\n",
    "firmware-nfc/build/.gitkeep": "",
    "firmware-nfc/tests/test_crc.c": textwrap.dedent("""\
        #include <assert.h>
        void test_crc16() { assert(crc16(NULL,0)==0); }
        int main(void){ test_crc16(); return 0; }
    """),
    "firmware-nfc/src/utils/crc.c": textwrap.dedent("""\
        #include <stdint.h>
        uint16_t crc16(const uint8_t *buf, size_t len) {
            uint16_t crc = 0xFFFF;
            for (size_t i=0;i<len;i++) {
                crc ^= buf[i];
                for(int j=0;j<8;j++) crc = (crc&1)?(crc>>1)^0xA001:(crc>>1);
            }
            return crc;
        }
    """),
    "firmware-nfc/src/utils/log.c": textwrap.dedent("""\
        #include <stdio.h>
        void log_info(const char *msg) { printf("[INFO] %s\\n", msg); }
        void log_err(const char *msg)  { printf("[ERR]  %s\\n", msg); }
    """),
    "firmware-nfc/src/crypto/aes_stub.c": textwrap.dedent("""\
        /* AES-128 stub — replace with HW accelerator */
        void aes_encrypt(uint8_t *buf, const uint8_t *key) { (void)buf; (void)key; }
    """),
    "firmware-nfc/include/nfc_config.h": textwrap.dedent("""\
        #pragma once
        #define NFC_BUF_SIZE   256
        #define NFC_MAX_RETRY  3
        #define NFC_TIMEOUT_MS 500
    """),
    "firmware-nfc/src/rtos/freertos_hooks.c": textwrap.dedent("""\
        #include "FreeRTOS.h"
        void vApplicationStackOverflowHook(TaskHandle_t t, char *name) {
            (void)t; (void)name;
            for(;;);
        }
    """),
    "firmware-nfc/src/hal/gpio.c": textwrap.dedent("""\
        #include <stdint.h>
        void gpio_set(uint8_t pin, uint8_t val) {
            volatile uint32_t *reg = (volatile uint32_t*)0x40020000;
            if(val) *reg |= (1<<pin); else *reg &= ~(1<<pin);
        }
    """),
}
for rel, content in distractors.items():
    (WORKSPACE / rel).write_text(content)

# ─── Reference files (used by the skill) ──────────────────────────────────────
(WORKSPACE / "references/memory-safety.md").write_text(textwrap.dedent("""\
    # Memory Safety Checklist
    - Check all buffer bounds (sprintf, strcpy, memcpy)
    - Verify DMA buffer alignment and cache coherence
    - Check stack usage in ISRs (must be minimal)
    - Heap fragmentation: prefer static allocation in embedded
    - Use bounded string functions: snprintf, strncpy, strlcpy
"""))

(WORKSPACE / "references/interrupt-safety.md").write_text(textwrap.dedent("""\
    # Interrupt Safety Checklist
    - Shared globals accessed from ISR must be volatile
    - Use critical sections (taskENTER_CRITICAL / __disable_irq) around shared data
    - ISRs must not call blocking OS functions (vTaskDelay, malloc)
    - Keep ISR execution time minimal
    - Check for priority inversion in FreeRTOS mutex usage
    - Re-entrant functions must not use static locals
"""))

(WORKSPACE / "references/hardware-interface.md").write_text(textwrap.dedent("""\
    # Hardware Interface Checklist
    - Peripheral init order: clock -> gpio -> peripheral -> irq enable
    - Register read-modify-write must be atomic or protected
    - DMA: verify src/dst alignment, cache flush/invalidate before/after transfer
    - NFC: frame timing (FDT), anti-collision sequence must not be interrupted
    - SPI/I2C: check timeout on busy-wait loops
    - Never enable IRQ before peripheral is fully configured
"""))

(WORKSPACE / "references/c-pitfalls.md").write_text(textwrap.dedent("""\
    # C/C++ Pitfalls Checklist
    - Signed/unsigned integer mismatch in comparisons
    - Uninitialized variables (especially in structs)
    - Implicit function declarations (C99 disallows)
    - Pointer aliasing violations (strict aliasing rule)
    - Missing volatile on hardware-mapped registers
    - Integer overflow: use uint32_t arithmetic, not int
    - Unused return values from safety-critical functions
"""))

# ─── prepare-diff.sh script ────────────────────────────────────────────────────
(WORKSPACE / "scripts/prepare-diff.sh").write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    # Usage: prepare-diff.sh <repo_path> [diff_range]
    # Outputs a review context package to stdout

    REPO="$1"
    RANGE="${2:-HEAD~1..HEAD}"

    if [ ! -d "$REPO/.git" ]; then
        echo "ERROR: $REPO is not a git repository" >&2
        exit 1
    fi

    cd "$REPO" || exit 1

    echo "=== REPO INFO ==="
    echo "Branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "Last commit: $(git log -1 --format='%h %s')"

    # Try to detect MCU/RTOS from source
    if grep -r "FreeRTOS" src/ --include="*.c" --include="*.h" -l 2>/dev/null | head -1 | grep -q .; then
        echo "RTOS: FreeRTOS"
    else
        echo "RTOS: bare-metal"
    fi

    if grep -r "STM32\\|stm32" src/ include/ --include="*.c" --include="*.h" -l 2>/dev/null | head -1 | grep -q .; then
        echo "MCU: STM32"
    else
        echo "MCU: Unknown"
    fi

    echo ""
    echo "=== DIFF STAT ==="
    git diff "$RANGE" --stat

    echo ""
    echo "=== DIFF CONTENT ==="
    git diff "$RANGE"
"""))
os.chmod(WORKSPACE / "scripts/prepare-diff.sh", 0o755)

# ─── Initialize git repo with baseline ───────────────────────────────────────
repo = WORKSPACE / "firmware-nfc"

# Baseline NFC driver (clean version)
(repo / "src/nfc/nfc_driver.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    #include <string.h>
    #include "nfc_config.h"

    static uint8_t rx_buf[NFC_BUF_SIZE];
    static volatile uint8_t nfc_rx_ready = 0;

    void nfc_init(void) {
        memset(rx_buf, 0, sizeof(rx_buf));
        nfc_rx_ready = 0;
    }

    int nfc_read(uint8_t *out, size_t len) {
        if (!nfc_rx_ready) return -1;
        if (len > NFC_BUF_SIZE) return -2;
        memcpy(out, rx_buf, len);
        nfc_rx_ready = 0;
        return (int)len;
    }

    void NFC_IRQHandler(void) {
        /* read single byte from peripheral FIFO */
        nfc_rx_ready = 1;
    }
"""))

(repo / "src/nfc/nfc_dma.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    #include "nfc_config.h"

    static uint8_t dma_buf[NFC_BUF_SIZE] __attribute__((aligned(32)));

    void dma_start_rx(uint32_t len) {
        /* configure DMA controller */
        volatile uint32_t *DMA_SRC  = (volatile uint32_t*)0x40026000;
        volatile uint32_t *DMA_DST  = (volatile uint32_t*)0x40026004;
        volatile uint32_t *DMA_LEN  = (volatile uint32_t*)0x40026008;
        volatile uint32_t *DMA_CTRL = (volatile uint32_t*)0x4002600C;

        *DMA_DST  = (uint32_t)(uintptr_t)dma_buf;
        *DMA_LEN  = len;
        *DMA_CTRL = 0x1; /* enable */
        (void)DMA_SRC;
    }
"""))

(repo / "src/hal/uart.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    void uart_init(uint32_t baud) {
        volatile uint32_t *UART_CTRL = (volatile uint32_t*)0x40011000;
        *UART_CTRL = baud;
    }
    void uart_putc(char c) {
        volatile uint32_t *UART_DR = (volatile uint32_t*)0x40011004;
        *UART_DR = (uint32_t)c;
    }
"""))

subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True, capture_output=True)
subprocess.run(["git", "commit", "-m", "Initial clean NFC firmware baseline"],
               cwd=str(repo), check=True, capture_output=True)

# ─── Introduce buggy changes (the PR under review) ───────────────────────────
# Bug 1: ISR accesses shared variable without volatile/critical section,
#         also calls vTaskDelay (RTOS blocking call in ISR — P0)
# Bug 2: DMA length unchecked — can exceed buffer (P0 buffer overflow)
# Bug 3: strcpy used instead of strncpy (P1)
# Bug 4: Missing cache flush before DMA (P1 hardware interface)
# Bug 5: IRQ enabled before peripheral fully init (P1)
# Bug 6: Signed/unsigned comparison (P2)
# Bug 7: Magic number in register access (P3)
# We need >100 lines of diff to force dual-model mode

(repo / "src/nfc/nfc_driver.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    #include <string.h>
    #include <stdio.h>
    #include "nfc_config.h"
    #include "FreeRTOS.h"
    #include "task.h"

    /* Shared state between ISR and task context */
    static uint8_t  rx_buf[NFC_BUF_SIZE];
    static uint8_t  nfc_rx_ready = 0;   /* BUG: missing volatile */
    static char     nfc_device_name[32];
    static uint8_t  rx_count = 0;
    static uint8_t  error_log[16];
    static uint32_t total_frames = 0;

    /* NFC frame structure */
    typedef struct {
        uint8_t  preamble;
        uint8_t  len;
        uint8_t  data[NFC_BUF_SIZE];
        uint16_t crc;
    } nfc_frame_t;

    static nfc_frame_t last_frame;

    void nfc_set_device_name(const char *name) {
        strcpy(nfc_device_name, name);  /* BUG: no bounds check — use strncpy */
    }

    void nfc_init(void) {
        volatile uint32_t *NFC_CTRL = (volatile uint32_t*)0x40030000;
        volatile uint32_t *NFC_IRQ  = (volatile uint32_t*)0x40030008;

        /* BUG: IRQ enabled before peripheral configured */
        *NFC_IRQ  = 0x1;  /* enable IRQ first — wrong order */
        *NFC_CTRL = 0xA5; /* magic number — configure peripheral */

        memset(rx_buf, 0, sizeof(rx_buf));
        memset(&last_frame, 0, sizeof(last_frame));
        nfc_rx_ready = 0;
        rx_count = 0;
        total_frames = 0;
    }

    int nfc_read(uint8_t *out, size_t len) {
        if (!nfc_rx_ready) return -1;
        /* BUG: signed/unsigned comparison — len is size_t, NFC_BUF_SIZE is #define int */
        if (len > NFC_BUF_SIZE) return -2;
        memcpy(out, rx_buf, len);
        nfc_rx_ready = 0;
        rx_count++;
        return (int)len;
    }

    int nfc_parse_frame(const uint8_t *raw, size_t raw_len, nfc_frame_t *out_frame) {
        if (raw == NULL || out_frame == NULL) return -1;
        if (raw_len < 3) return -2;

        out_frame->preamble = raw[0];
        out_frame->len      = raw[1];

        /* BUG: out_frame->len can be > NFC_BUF_SIZE, no bounds check before memcpy */
        memcpy(out_frame->data, &raw[2], out_frame->len);

        out_frame->crc = (uint16_t)(raw[raw_len-2] << 8 | raw[raw_len-1]);
        total_frames++;
        return 0;
    }

    void nfc_log_error(uint8_t code) {
        static uint8_t idx = 0;
        /* BUG: idx can wrap around without bounds check in fast interrupt context */
        error_log[idx % 16] = code;
        idx++;
    }

    /* ISR — must be minimal and non-blocking */
    void NFC_IRQHandler(void) {
        volatile uint32_t *NFC_FIFO = (volatile uint32_t*)0x40030004;
        uint32_t data = *NFC_FIFO;

        /* BUG P0: calling vTaskDelay inside ISR — RTOS blocking call forbidden in ISR */
        vTaskDelay(1);

        rx_buf[0] = (uint8_t)data;
        nfc_rx_ready = 1;  /* BUG: non-volatile write, compiler may optimize away */
    }

    void nfc_get_stats(uint32_t *frames, uint8_t *count) {
        /* BUG: no critical section — total_frames/rx_count modified in ISR context */
        *frames = total_frames;
        *count  = rx_count;
    }

    void nfc_print_buf(void) {
        char tmp[16];
        /* BUG: sprintf with no bounds, buf may overflow */
        sprintf(tmp, "RX count: %u, frames: %lu", rx_count, (unsigned long)total_frames);
        printf("%s\\n", tmp);
    }
"""))

(repo / "src/nfc/nfc_dma.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    #include <string.h>
    #include "nfc_config.h"

    /* DMA buffer must be cache-line aligned for Cortex-M7 */
    static uint8_t dma_buf[NFC_BUF_SIZE] __attribute__((aligned(32)));
    static uint8_t dma_shadow[NFC_BUF_SIZE];

    typedef struct {
        uint32_t src_addr;
        uint32_t dst_addr;
        uint32_t length;
        uint32_t control;
    } dma_descriptor_t;

    static dma_descriptor_t dma_desc;

    void dma_cache_flush(void *addr, size_t len) {
        /* SCB_CleanDCache_by_Addr — architecture-specific */
        (void)addr; (void)len;
        /* BUG: stub — actual cache flush not implemented, DMA will see stale data */
    }

    void dma_start_rx(uint32_t len) {
        volatile uint32_t *DMA_SRC  = (volatile uint32_t*)0x40026000;
        volatile uint32_t *DMA_DST  = (volatile uint32_t*)0x40026004;
        volatile uint32_t *DMA_LEN  = (volatile uint32_t*)0x40026008;
        volatile uint32_t *DMA_CTRL = (volatile uint32_t*)0x4002600C;

        /* BUG P0: len not validated against NFC_BUF_SIZE — allows DMA overflow */
        /* BUG P1: no cache flush before DMA — CPU cache may have stale data */

        dma_desc.dst_addr = (uint32_t)(uintptr_t)dma_buf;
        dma_desc.length   = len;
        dma_desc.control  = 0x1;

        *DMA_DST  = (uint32_t)(uintptr_t)dma_buf;
        *DMA_LEN  = len;
        *DMA_CTRL = 1;

        (void)DMA_SRC;
    }

    int dma_copy_to_shadow(uint32_t len) {
        /* BUG: len is uint32_t, NFC_BUF_SIZE is int — comparison may be problematic */
        if (len > NFC_BUF_SIZE) return -1;

        /* BUG: no cache invalidation after DMA completes before CPU reads dma_buf */
        memcpy(dma_shadow, dma_buf, len);
        return 0;
    }

    void dma_reset(void) {
        volatile uint32_t *DMA_CTRL = (volatile uint32_t*)0x4002600C;
        *DMA_CTRL = 0;
        memset(dma_buf,    0, sizeof(dma_buf));
        memset(dma_shadow, 0, sizeof(dma_shadow));
        memset(&dma_desc,  0, sizeof(dma_desc));
    }
"""))

# Add a new uart helper with a bug
(repo / "src/hal/uart.c").write_text(textwrap.dedent("""\
    #include <stdint.h>
    #include <string.h>

    static char uart_tx_buf[64];
    static uint8_t tx_pending = 0;  /* BUG: should be volatile — modified in ISR */

    void uart_init(uint32_t baud) {
        volatile uint32_t *UART_CTRL = (volatile uint32_t*)0x40011000;
        volatile uint32_t *UART_IRQ  = (volatile uint32_t*)0x40011010;

        /* BUG: IRQ enabled before UART fully configured */
        *UART_IRQ  = 0x3;
        *UART_CTRL = baud;
    }

    void uart_putc(char c) {
        volatile uint32_t *UART_DR = (volatile uint32_t*)0x40011004;
        *UART_DR = (uint32_t)c;
    }

    void uart_send_str(const char *s) {
        /* BUG: no length check — overflows uart_tx_buf for long strings */
        strcpy(uart_tx_buf, s);
        tx_pending = 1;
    }

    void UART_IRQHandler(void) {
        if (tx_pending) {
            /* send queued data */
            for (int i = 0; uart_tx_buf[i]; i++) uart_putc(uart_tx_buf[i]);
            tx_pending = 0;  /* BUG: tx_pending not volatile */
        }
    }
"""))

# Commit the changes
subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True, capture_output=True)
subprocess.run(["git", "commit", "-m", "feat: add NFC DMA receive path and frame parser (NFC-247)"],
               cwd=str(repo), check=True, capture_output=True)

# ─── Verify diff size > 100 lines ─────────────────────────────────────────────
result = subprocess.run(
    ["git", "diff", "HEAD~1..HEAD"],
    cwd=str(repo), capture_output=True, text=True
)
diff_lines = result.stdout.count('\n')
print(f"[gen_inputs] Diff line count: {diff_lines} (need >100 for dual-model trigger)")
assert diff_lines > 100, f"Diff too small: {diff_lines} lines"

print("[gen_inputs] Workspace ready.")
print(f"  Repo: {repo}")
print(f"  Diff: HEAD~1..HEAD ({diff_lines} lines)")