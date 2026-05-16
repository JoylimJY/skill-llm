import os
import random
import textwrap

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "firmware/brake_ctrl/src",
    "firmware/brake_ctrl/inc",
    "firmware/brake_ctrl/test",
    "firmware/engine_ctrl/src",
    "firmware/engine_ctrl/inc",
    "firmware/steering/src",
    "firmware/steering/inc",
    "firmware/common/utils",
    "firmware/common/hal",
    "docs/certification",
    "docs/architecture",
    "build/obj",
    "build/map",
    "scripts",
    "tools/lint",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "firmware/brake_ctrl/inc/brake_ctrl.h": textwrap.dedent("""\
        /* brake_ctrl.h - Brake Control ECU Interface */
        #ifndef BRAKE_CTRL_H
        #define BRAKE_CTRL_H
        #include <stdint.h>

        void Brake_Init(void);
        void Brake_Apply(uint8_t pressure_pct);
        uint8_t Brake_GetStatus(void);

        #endif /* BRAKE_CTRL_H */
        """),

    "firmware/brake_ctrl/test/test_brake.c": textwrap.dedent("""\
        /* Unit tests for brake controller */
        #include "brake_ctrl.h"
        #include <assert.h>

        void test_brake_init(void) {
            Brake_Init();
            assert(Brake_GetStatus() == 0U);
        }

        int main(void) {
            test_brake_init();
            return 0;
        }
        """),

    "firmware/engine_ctrl/src/engine.c": textwrap.dedent("""\
        /* Engine control module */
        #include <stdint.h>

        static uint32_t engine_rpm = 0U;

        void Engine_SetRPM(uint32_t rpm) {
            engine_rpm = rpm;
        }

        uint32_t Engine_GetRPM(void) {
            return engine_rpm;
        }
        """),

    "firmware/engine_ctrl/inc/engine.h": textwrap.dedent("""\
        #ifndef ENGINE_H
        #define ENGINE_H
        #include <stdint.h>
        void Engine_SetRPM(uint32_t rpm);
        uint32_t Engine_GetRPM(void);
        #endif
        """),

    "firmware/steering/src/steering.c": textwrap.dedent("""\
        /* Steering angle controller */
        #include <stdint.h>
        #include <stdbool.h>

        static volatile uint32_t * const STEER_REG = (volatile uint32_t *)0x40020000U;

        void Steering_SetAngle(int16_t angle_deg) {
            if (angle_deg > (int16_t)360) {
                angle_deg = (int16_t)360;
            } else if (angle_deg < (int16_t)-360) {
                angle_deg = (int16_t)-360;
            } else {
                /* in range */
            }
            *STEER_REG = (uint32_t)angle_deg;
        }
        """),

    "firmware/steering/inc/steering.h": textwrap.dedent("""\
        #ifndef STEERING_H
        #define STEERING_H
        #include <stdint.h>
        void Steering_SetAngle(int16_t angle_deg);
        #endif
        """),

    "firmware/common/utils/crc.c": textwrap.dedent("""\
        /* CRC-16 utility */
        #include <stdint.h>

        uint16_t CRC16_Compute(const uint8_t *data, uint32_t len) {
            uint16_t crc = 0xFFFFU;
            uint32_t i;
            for (i = 0U; i < len; i++) {
                crc ^= (uint16_t)data[i];
            }
            return crc;
        }
        """),

    "firmware/common/hal/gpio.c": textwrap.dedent("""\
        /* GPIO HAL */
        #include <stdint.h>
        #include <stdbool.h>

        static volatile uint32_t * const GPIO_OUT = (volatile uint32_t *)0x40010000U;
        static volatile uint32_t * const GPIO_IN  = (volatile uint32_t *)0x40010004U;

        void GPIO_SetPin(uint8_t pin) {
            *GPIO_OUT |= (uint32_t)(1U << pin);
        }

        bool GPIO_ReadPin(uint8_t pin) {
            return ((*GPIO_IN >> pin) & 1U) != 0U;
        }
        """),

    "firmware/common/hal/gpio.h": textwrap.dedent("""\
        #ifndef GPIO_H
        #define GPIO_H
        #include <stdint.h>
        #include <stdbool.h>
        void GPIO_SetPin(uint8_t pin);
        bool GPIO_ReadPin(uint8_t pin);
        #endif
        """),

    "docs/architecture/system_overview.txt": textwrap.dedent("""\
        Brake-by-Wire ECU — System Architecture Overview
        =================================================
        The BbW ECU consists of three subsystems:
         1. Brake Pressure Controller (BPC)
         2. Wheel Speed Monitor (WSM)
         3. ABS Logic Unit (ALU)

        Safety integrity targets: ASIL D for BPC, ASIL C for WSM, ASIL B for ALU.
        All firmware must comply with MISRA C:2012 prior to certification.
        """),

    "docs/certification/iso26262_checklist.txt": textwrap.dedent("""\
        ISO 26262 Pre-Certification Checklist
        ======================================
        [ ] Static analysis complete (MISRA C:2012)
        [ ] Unit test coverage >= 100% MC/DC
        [ ] Code review sign-off
        [ ] FMEA updated
        [ ] ASIL decomposition verified
        """),

    "scripts/build.sh": textwrap.dedent("""\
        #!/bin/bash
        # Build script
        set -e
        gcc -Wall -Wextra -o build/brake_fw firmware/brake_ctrl/src/brake_ctrl_core.c
        echo "Build complete."
        """),

    "tools/lint/run_lint.sh": textwrap.dedent("""\
        #!/bin/bash
        # Placeholder lint runner
        echo "Running static analysis..."
        """),

    "build/map/brake_fw.map": textwrap.dedent("""\
        Memory map — brake_fw
        .text   0x08000000  0x1200
        .data   0x20000000  0x080
        .bss    0x20000080  0x040
        """),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE PROBLEM FILE — brake_ctrl_core.c ────────────────────────────────────
# Deliberately contains 10 MISRA violations to be caught by the agent.
# Violations planted:
#  V1  Rule 21.3  — malloc() in main path         → Mandatory / SAFETY CRITICAL banner
#  V2  Rule 15.1  — goto statement                → Mandatory / ASIL D (escalation)
#  V3  Rule 4.6   — bare 'int' for numeric data   → Required
#  V4  Rule 15.7  — if-else if chain without else → Required
#  V5  Rule 16.4  — switch without default        → Required
#  V6  Rule 20.7  — unparenthesised macro param   → Required
#  V7  Rule 17.3  — implicit function declaration → Mandatory
#  V8  Rule 17.2  — recursive function            → Mandatory (escalation: trace call chain)
#  V9  memory-embedded — missing volatile on HW reg pointer → Required/memory rules
#  V10 Rule 21.3 in ISR + ISR heightened strictness          → Mandatory

brake_core_c = textwrap.dedent("""\
    /*
     * brake_ctrl_core.c
     * Brake Control ECU — Core Pressure Management Module
     * Target: Cortex-M4 (STM32G474)
     * Author: BbW Firmware Team
     * Rev: 2.4.1
     */

    #include <stdint.h>
    #include <stdbool.h>
    #include <stdlib.h>   /* needed for dynamic buffer */
    #include <string.h>

    /* ------------------------------------------------------------------ */
    /*  Hardware register mapping                                          */
    /* ------------------------------------------------------------------ */

    /* VIOLATION V9: missing 'volatile' — hardware register pointer must be volatile */
    static uint32_t * const BRAKE_PRESSURE_REG = (uint32_t *)0x40030000U;
    static volatile uint32_t * const BRAKE_STATUS_REG  = (volatile uint32_t *)0x40030004U;

    /* ------------------------------------------------------------------ */
    /*  Type definitions                                                   */
    /* ------------------------------------------------------------------ */

    typedef enum {
        BRAKE_STATE_IDLE    = 0,
        BRAKE_STATE_APPLY   = 1,
        BRAKE_STATE_RELEASE = 2,
        BRAKE_STATE_FAULT   = 3
    } BrakeState_t;

    /* ------------------------------------------------------------------ */
    /*  Macro definitions                                                  */
    /* ------------------------------------------------------------------ */

    /* VIOLATION V6: macro parameter not parenthesised — Rule 20.7 */
    #define SCALE_PRESSURE(x)   x * 4U

    #define MAX_PRESSURE_PCT   (100U)
    #define MIN_PRESSURE_PCT   (0U)

    /* ------------------------------------------------------------------ */
    /*  Module state                                                       */
    /* ------------------------------------------------------------------ */

    static BrakeState_t  s_brake_state   = BRAKE_STATE_IDLE;
    static uint8_t       s_pressure_pct  = 0U;

    /* ------------------------------------------------------------------ */
    /*  Forward declarations (intentionally incomplete to plant violation) */
    /* ------------------------------------------------------------------ */
    /* NOTE: compute_checksum is called below but NOT declared here       */
    /* VIOLATION V7 lives at the call site — implicit function declaration */

    /* ------------------------------------------------------------------ */
    /*  VIOLATION V8 — Recursive function (Rule 17.2)                     */
    /*  Recursive factorial used internally for diagnostic scaling         */
    /* ------------------------------------------------------------------ */
    static uint32_t Brake_Factorial(uint32_t n)
    {
        if (n == 0U) {
            return 1U;
        }
        return n * Brake_Factorial(n - 1U);  /* recursive self-call */
    }

    /* ------------------------------------------------------------------ */
    /*  Brake state transition logic                                       */
    /* ------------------------------------------------------------------ */
    static void Brake_UpdateState(uint8_t pressure_pct)
    {
        /* VIOLATION V5 — switch without default clause (Rule 16.4) */
        switch (s_brake_state)
        {
            case BRAKE_STATE_IDLE:
                if (pressure_pct > MIN_PRESSURE_PCT) {
                    s_brake_state = BRAKE_STATE_APPLY;
                }
                break;

            case BRAKE_STATE_APPLY:
                if (pressure_pct == MIN_PRESSURE_PCT) {
                    s_brake_state = BRAKE_STATE_RELEASE;
                }
                break;

            case BRAKE_STATE_RELEASE:
                s_brake_state = BRAKE_STATE_IDLE;
                break;

            case BRAKE_STATE_FAULT:
                /* remain in fault */
                break;
            /* NO default: clause — violation */
        }
    }

    /* ------------------------------------------------------------------ */
    /*  Pressure validation                                                */
    /* ------------------------------------------------------------------ */
    static bool Brake_ValidatePressure(uint8_t pressure_pct)
    {
        /* VIOLATION V4 — if-else if chain missing final else (Rule 15.7) */
        if (pressure_pct > MAX_PRESSURE_PCT) {
            return false;
        } else if (pressure_pct == MAX_PRESSURE_PCT) {
            return true;
        } else if (pressure_pct < MIN_PRESSURE_PCT) {
            return false;
        }
        /* missing final else — violation */
        return true;
    }

    /* ------------------------------------------------------------------ */
    /*  Core apply function                                                */
    /* ------------------------------------------------------------------ */
    void Brake_Apply(uint8_t pressure_pct)
    {
        /* VIOLATION V3 — bare 'int' used for loop counter (Rule 4.6) */
        int retry_count = 0;

        if (!Brake_ValidatePressure(pressure_pct)) {
            goto fault_handler;  /* VIOLATION V2 — goto (Rule 15.1) */
        }

        s_pressure_pct = pressure_pct;
        Brake_UpdateState(pressure_pct);

        /* VIOLATION V7 — compute_checksum called without prior declaration */
        uint8_t chk = compute_checksum(pressure_pct);
        (void)chk;

        /* VIOLATION V1 — malloc in safety-critical path (Rule 21.3) */
        uint8_t *log_buf = (uint8_t *)malloc(32U);
        if (log_buf != NULL) {
            (void)memset(log_buf, 0, 32U);
            log_buf[0] = pressure_pct;
            free(log_buf);
        }

        /* Use scaled pressure — V6 macro used here */
        *BRAKE_PRESSURE_REG = (uint32_t)SCALE_PRESSURE(pressure_pct);

        /* diagnostic: unused but demonstrates recursive call */
        (void)Brake_Factorial(5U);

        while (retry_count < 3) {
            if ((*BRAKE_STATUS_REG & 0x01U) != 0U) {
                break;
            }
            retry_count++;
        }
        return;

    fault_handler:
        s_brake_state = BRAKE_STATE_FAULT;
        *BRAKE_PRESSURE_REG = 0U;
    }

    /* ------------------------------------------------------------------ */
    /*  ISR — Brake Pressure Sensor Interrupt                             */
    /* ------------------------------------------------------------------ */
    __attribute__((interrupt)) void Brake_IRQ_Handler(void)
    {
        /* VIOLATION V10 — malloc inside ISR (Rule 21.3, heightened ISR strictness) */
        uint8_t *isr_buf = (uint8_t *)malloc(8U);
        if (isr_buf != NULL) {
            isr_buf[0] = (uint8_t)(*BRAKE_STATUS_REG & 0xFFU);
            free(isr_buf);
        }

        /* Acknowledge interrupt */
        *BRAKE_STATUS_REG = 0U;
    }
    """)

brake_core_path = os.path.join(WORKSPACE, "firmware/brake_ctrl/src/brake_ctrl_core.c")
with open(brake_core_path, "w") as f:
    f.write(brake_core_c)

print(f"Workspace generated at {WORKSPACE}")
print(f"Problem file: {brake_core_path}")
print(f"Total distractor files: {len(distractor_files)}")