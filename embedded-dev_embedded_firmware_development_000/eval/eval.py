import sys
import os
import re
import json
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # Find the target file
    candidates = list(Path(workspace).rglob("motor_controller.c"))
    
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight
    
    # Check 1: File exists
    if not candidates:
        add_check("file_exists", False, "motor_controller.c not found anywhere in workspace", 1.0)
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    target = candidates[0]
    add_check("file_exists", True, f"Found at {target}", 1.0)
    
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        add_check("file_readable", False, f"Cannot read file: {e}", 1.0)
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return
    
    add_check("file_readable", True, "File is readable", 0.5)

    # ============================================================
    # CHECK 2: PWM Timer Configuration - ARR must be 2000-1 = 1999
    # Skill specifies: TIM_Period = 2000 - 1 => 50Hz from 100kHz tick
    # ============================================================
    arr_pattern = re.search(r'TIM_Period\s*=\s*(\d+)\s*-?\s*1?', content)
    arr_direct = re.search(r'ARR\s*=\s*1999\b', content) or re.search(r'\.TIM_Period\s*=\s*1999\b', content)
    arr_expr = re.search(r'TIM_Period\s*=\s*2000\s*-\s*1', content)
    arr_macro = re.search(r'#define\s+\w*ARR\w*\s+1999\b', content)
    
    # Also check for register-style: TIM3->ARR = 1999
    arr_reg = re.search(r'TIM3\s*->\s*ARR\s*=\s*1999\b', content)
    
    arr_ok = bool(arr_expr or arr_direct or arr_macro or arr_reg)
    add_check(
        "pwm_arr_correct",
        arr_ok,
        "TIM_Period/ARR set to 1999 (2000-1) for 50Hz PWM" if arr_ok else
        "ARR/TIM_Period not set to 1999. Skill requires 2000-1 for 50Hz from 72MHz/720 prescaler",
        2.0
    )

    # ============================================================
    # CHECK 3: PWM Prescaler - PSC must be 72-1 = 71
    # Skill: TIM_Prescaler = 72 - 1 => 72MHz/72 = 1MHz... wait
    # Actually skill says: 72MHz / 720 => 100kHz, then / 2000 => 50Hz
    # PSC = 720-1 = 719 OR the skill template literally says TIM_Prescaler = 72-1
    # Reading carefully: "72MHz / 720 => 100kHz, 100kHz / 2000 => 50Hz"
    # TIM_Prescaler = 72 - 1 means divide by 72 => 1MHz, then ARR=2000 => 500Hz? 
    # No wait, the skill code comment says "72MHz / 720 => 100kHz" but TIM_Prescaler = 72-1 = 71
    # This is an intentional ambiguity in the skill. The ACTUAL code in skill says:
    # TIM_Prescaler = 72 - 1;  and comment says 72MHz/720 which is inconsistent
    # The code takes precedence: PSC = 72-1 = 71
    # With PSC=71: tick = 72MHz/(71+1) = 1MHz, ARR=1999: freq = 1MHz/2000 = 500Hz (not 50Hz)
    # BUT the skill's own code says both PSC=72-1 AND 50Hz. The agent must copy exactly.
    # We test for what the SKILL.md literally says in code: TIM_Prescaler = 72 - 1
    # ============================================================
    psc_expr = re.search(r'TIM_Prescaler\s*=\s*72\s*-\s*1', content)
    psc_direct = re.search(r'\.TIM_Prescaler\s*=\s*71\b', content)
    psc_macro = re.search(r'#define\s+\w*PSC\w*\s+71\b', content)
    psc_reg = re.search(r'TIM3\s*->\s*PSC\s*=\s*71\b', content)
    
    psc_ok = bool(psc_expr or psc_direct or psc_macro or psc_reg)
    add_check(
        "pwm_psc_correct",
        psc_ok,
        "TIM_Prescaler set to 72-1=71 as per skill spec" if psc_ok else
        "Prescaler not matching skill spec (72-1). Generic agents use different values.",
        2.0
    )

    # ============================================================
    # CHECK 4: PWM idle pulse = 1500 (neutral position 75%)
    # Skill: TIM_Pulse = 1500  // 占空比 75%
    # ============================================================
    pulse_expr = re.search(r'TIM_Pulse\s*=\s*1500\b', content)
    pulse_ccr_init = re.search(r'CCR2\s*=\s*1500\b', content)
    
    pulse_ok = bool(pulse_expr or pulse_ccr_init)
    add_check(
        "pwm_idle_pulse_1500",
        pulse_ok,
        "Idle/neutral PWM pulse correctly set to 1500 (75% of 2000)" if pulse_ok else
        "Idle pulse not set to 1500. Skill specifies 1500 as neutral servo position.",
        2.0
    )

    # ============================================================
    # CHECK 5: Motor_SetSpeed formula: TIM3->CCR2 = speed * 20
    # Skill: void Motor_SetSpeed(uint8_t speed) { TIM3->CCR2 = (speed * 20); }
    # This is the CRITICAL proprietary trap: multiplier MUST be 20 (not 10, 15, etc.)
    # ============================================================
    speed_formula = re.search(r'CCR2\s*=\s*\(?\s*speed\s*\*\s*20\s*\)?', content)
    speed_formula2 = re.search(r'CCR2\s*=\s*\(?\s*20\s*\*\s*speed\s*\)?', content)
    
    speed_ok = bool(speed_formula or speed_formula2)
    add_check(
        "motor_setspeed_formula_x20",
        speed_ok,
        "Motor_SetSpeed uses CCR2 = speed * 20 (maps 0-100 to 0-2000)" if speed_ok else
        "CRITICAL FAIL: Motor_SetSpeed formula incorrect. Must be speed*20, not speed*10 or other.",
        3.0
    )

    # ============================================================
    # CHECK 6: UART ISR uses USART_SR_RXNE flag check
    # Skill: if (USART->SR & USART_SR_RXNE)
    # ============================================================
    uart_rxne = re.search(r'USART\w*\s*->\s*SR\s*&\s*USART_SR_RXNE', content)
    uart_rxne2 = re.search(r'USART_SR_RXNE', content)
    
    uart_ok = bool(uart_rxne or uart_rxne2)
    add_check(
        "uart_isr_rxne_flag",
        uart_ok,
        "UART ISR correctly checks USART_SR_RXNE flag" if uart_ok else
        "UART ISR missing USART_SR_RXNE check. Skill mandates this specific register flag.",
        2.0
    )

    # ============================================================
    # CHECK 7: FreeRTOS queue usage with portMAX_DELAY
    # Skill: xQueueSend(temp_queue, &temp, portMAX_DELAY)
    # ============================================================
    queue_send = re.search(r'xQueueSend\s*\(', content)
    queue_recv = re.search(r'xQueueReceive\s*\(', content)
    port_max = re.search(r'portMAX_DELAY', content)
    
    rtos_queue_ok = bool((queue_send or queue_recv) and port_max)
    add_check(
        "freertos_queue_portmax_delay",
        rtos_queue_ok,
        "FreeRTOS queue used with portMAX_DELAY blocking" if rtos_queue_ok else
        "Missing xQueueSend/Receive with portMAX_DELAY. Skill requires blocking queue IPC.",
        2.0
    )

    # ============================================================
    # CHECK 8: Two separate FreeRTOS tasks created with xTaskCreate
    # ============================================================
    task_creates = re.findall(r'xTaskCreate\s*\(', content)
    two_tasks_ok = len(task_creates) >= 2
    add_check(
        "two_freertos_tasks",
        two_tasks_ok,
        f"Found {len(task_creates)} xTaskCreate calls (need >=2 for UART and motor tasks)" if two_tasks_ok else
        f"Only {len(task_creates)} xTaskCreate calls found. Need separate UART RX and motor control tasks.",
        2.0
    )

    # ============================================================
    # CHECK 9: UART receive ISR handler named correctly
    # Must have an ISR function for USART1
    # ============================================================
    isr_name = re.search(r'USART1_IRQHandler\s*\(', content)
    isr_ok = bool(isr_name)
    add_check(
        "usart1_irqhandler_present",
        isr_ok,
        "USART1_IRQHandler defined as per skill template" if isr_ok else
        "Missing USART1_IRQHandler. Skill mandates interrupt-driven UART with this handler name.",
        1.5
    )

    # ============================================================
    # CHECK 10: rx_buf with volatile declaration (skill uses volatile uint8_t rx_len)
    # ============================================================
    volatile_check = re.search(r'volatile\s+uint8_t\s+rx_len', content)
    volatile_buf = re.search(r'volatile\s+uint8_t\s+rx_buf', content)
    rx_buf_check = re.search(r'uint8_t\s+rx_buf\s*\[', content)
    
    volatile_ok = bool(volatile_check or volatile_buf)
    rxbuf_ok = bool(rx_buf_check)
    
    add_check(
        "volatile_rx_len_or_buf",
        volatile_ok,
        "volatile qualifier correctly applied to rx_len or rx_buf" if volatile_ok else
        "Missing volatile qualifier on rx_len/rx_buf. Skill specifies: volatile uint8_t rx_len",
        1.0
    )
    
    add_check(
        "rx_buf_declared",
        rxbuf_ok,
        "rx_buf[64] or similar receive buffer declared" if rxbuf_ok else
        "No rx_buf receive buffer declared. Skill template requires uint8_t rx_buf[64].",
        0.5
    )

    # ============================================================
    # CHECK 11: Command parsing for "SPEED:" prefix
    # Business requirement from docs/requirements.txt
    # ============================================================
    speed_cmd_parse = re.search(r'SPEED\s*:', content, re.IGNORECASE)
    speed_parse_ok = bool(speed_cmd_parse)
    add_check(
        "speed_command_parsed",
        speed_parse_ok,
        "SPEED: command format parsed from UART input" if speed_parse_ok else
        "No parsing of 'SPEED:' command. Requirements specify ASCII SPEED:xx\\r\\n format.",
        1.5
    )

    # ============================================================
    # CHECK 12: TIM_OCMode_PWM1 specified (not PWM2)
    # Skill: TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;
    # ============================================================
    pwm_mode = re.search(r'TIM_OCMode_PWM1', content)
    pwm_mode_reg = re.search(r'OC2M\s*=\s*0b110', content)  # register-level PWM1 mode
    
    pwm_mode_ok = bool(pwm_mode or pwm_mode_reg)
    add_check(
        "tim_ocmode_pwm1",
        pwm_mode_ok,
        "TIM_OCMode_PWM1 correctly specified" if pwm_mode_ok else
        "TIM_OCMode_PWM1 not found. Skill specifies PWM1 mode specifically.",
        1.0
    )

    # ============================================================
    # FINAL SCORE CALCULATION
    # ============================================================
    max_score = 1.0 + 0.5 + 2.0 + 2.0 + 2.0 + 3.0 + 2.0 + 2.0 + 2.0 + 1.5 + 1.0 + 0.5 + 1.5 + 1.0
    normalized_score = min(1.0, total_score / max_score)
    
    # Must pass critical checks to overall pass
    critical_checks = ["motor_setspeed_formula_x20", "pwm_arr_correct", "freertos_queue_portmax_delay", "two_freertos_tasks"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    # Need at least 65% score AND all critical checks
    overall_passed = (normalized_score >= 0.65) and critical_passed
    
    result = {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()