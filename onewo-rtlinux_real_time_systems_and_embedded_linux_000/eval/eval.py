import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    candidates = list(Path(workspace).rglob("rt_servo_controller.c"))
    return candidates[0] if candidates else None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace):
    checks = []

    # --- Locate the output file ---
    output_file = find_output_file(workspace)
    if not output_file:
        checks.append(check("output_file_exists", False, "rt_servo_controller.c not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("output_file_exists", True, f"Found at {output_file}"))

    try:
        code = output_file.read_text(errors="replace")
    except Exception as e:
        checks.append(check("file_readable", False, str(e)))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, "File read successfully"))

    # --- CHECK 1: SCHED_FIFO (not SCHED_RR or SCHED_OTHER) ---
    has_sched_fifo = bool(re.search(r'\bSCHED_FIFO\b', code))
    has_sched_rr   = bool(re.search(r'\bSCHED_RR\b', code))
    checks.append(check(
        "uses_SCHED_FIFO",
        has_sched_fifo and not has_sched_rr,
        f"SCHED_FIFO={'yes' if has_sched_fifo else 'no'}, SCHED_RR={'yes (BAD)' if has_sched_rr else 'no'}"
    ))

    # --- CHECK 2: Priority in range 80-90 ---
    priorities = re.findall(r'sched_priority\s*=\s*(\d+)', code)
    priority_ok = False
    priority_detail = "No sched_priority assignment found"
    if priorities:
        vals = [int(p) for p in priorities]
        priority_ok = all(80 <= v <= 90 for v in vals)
        priority_detail = f"Found priorities: {vals}, all in 80-90: {priority_ok}"
    checks.append(check("priority_80_to_90", priority_ok, priority_detail))

    # --- CHECK 3: CPU affinity set (pthread_setaffinity_np) ---
    has_affinity = bool(re.search(r'pthread_setaffinity_np\s*\(', code))
    checks.append(check(
        "cpu_affinity_set",
        has_affinity,
        "pthread_setaffinity_np found" if has_affinity else "pthread_setaffinity_np missing"
    ))

    # --- CHECK 4: No printf/fprintf/syslog in loop body ---
    # Heuristic: no printf/fprintf anywhere in the loop-related code
    # We check for ANY printf/fprintf in the code as the loop is the main body
    has_printf = bool(re.search(r'\b(printf|fprintf|syslog)\s*\(', code))
    checks.append(check(
        "no_printf_in_code",
        not has_printf,
        "printf/fprintf/syslog absent (good)" if not has_printf else "printf/fprintf/syslog found (BAD - prohibited in RT loop)"
    ))

    # --- CHECK 5: mmap used for peripheral access, ioctl NOT used for register writes ---
    has_mmap = bool(re.search(r'\bmmap\s*\(', code))
    has_ioctl = bool(re.search(r'\bioctl\s*\(', code))
    checks.append(check(
        "uses_mmap_not_ioctl",
        has_mmap and not has_ioctl,
        f"mmap={'yes' if has_mmap else 'no'}, ioctl={'yes (BAD)' if has_ioctl else 'no'}"
    ))

    # --- CHECK 6: clock_gettime with CLOCK_MONOTONIC (no gettimeofday) ---
    has_clock_gettime_mono = bool(re.search(r'clock_gettime\s*\(\s*CLOCK_MONOTONIC', code))
    has_gettimeofday = bool(re.search(r'\bgettimeofday\b', code))
    checks.append(check(
        "uses_clock_gettime_MONOTONIC",
        has_clock_gettime_mono and not has_gettimeofday,
        f"clock_gettime(CLOCK_MONOTONIC)={'yes' if has_clock_gettime_mono else 'no'}, gettimeofday={'yes (BAD)' if has_gettimeofday else 'no'}"
    ))

    # --- CHECK 7: clock_nanosleep with TIMER_ABSTIME ---
    has_clock_nanosleep_abstime = bool(re.search(r'clock_nanosleep\s*\([^)]*TIMER_ABSTIME', code))
    checks.append(check(
        "clock_nanosleep_with_TIMER_ABSTIME",
        has_clock_nanosleep_abstime,
        "clock_nanosleep with TIMER_ABSTIME found" if has_clock_nanosleep_abstime else "clock_nanosleep(TIMER_ABSTIME) missing"
    ))

    # --- CHECK 8: clock_nanosleep at END of loop (after control work) ---
    # Strategy: find the while loop body and check that clock_nanosleep is the last meaningful statement
    # We look for the pattern: control/work code appears before clock_nanosleep in the loop
    loop_body_match = re.search(
        r'while\s*\(\s*running\s*\)\s*\{(.*?)\}',
        code, re.DOTALL
    )
    sleep_at_end = False
    sleep_position_detail = "Could not find while(running) loop body"
    if loop_body_match:
        loop_body = loop_body_match.group(1)
        # Find positions of clock_nanosleep and any non-whitespace, non-comment statements before/after it
        sleep_pos = loop_body.rfind("clock_nanosleep")
        if sleep_pos >= 0:
            after_sleep = loop_body[sleep_pos:].strip()
            # After clock_nanosleep there should be only closing braces / whitespace / nothing
            after_sleep_stripped = re.sub(r'clock_nanosleep[^;]+;', '', after_sleep).strip()
            # Remove nested braces artifacts and whitespace
            after_sleep_clean = re.sub(r'[\s\{\}]', '', after_sleep_stripped)
            sleep_at_end = len(after_sleep_clean) == 0
            sleep_position_detail = f"clock_nanosleep found; after it (cleaned): '{after_sleep_clean[:80]}'"
        else:
            sleep_position_detail = "clock_nanosleep not found inside while(running) loop"
    checks.append(check("clock_nanosleep_at_end_of_loop", sleep_at_end, sleep_position_detail))

    # --- CHECK 9: No busy-wait spin loop ---
    # Look for volatile spin counter patterns or tight while(1){} without sleep
    has_busywait = bool(re.search(r'volatile\s+int\s+spin\b', code))
    # Also check for explicit spin patterns
    has_busywait = has_busywait or bool(re.search(r'while\s*\(\s*spin\s*<', code))
    checks.append(check(
        "no_busy_wait",
        not has_busywait,
        "No busy-wait spin detected" if not has_busywait else "Busy-wait spin variable found (BAD)"
    ))

    # --- CHECK 10: request_threaded_irq (not just request_irq) ---
    has_threaded_irq = bool(re.search(r'\brequest_threaded_irq\s*\(', code))
    has_plain_request_irq = bool(re.search(r'(?<!threaded_)\brequest_irq\s*\(', code))
    checks.append(check(
        "uses_request_threaded_irq",
        has_threaded_irq,
        "request_threaded_irq found" if has_threaded_irq else "request_threaded_irq missing (must not use plain request_irq)"
    ))

    # --- CHECK 11: IRQ affinity binding to isolated core ---
    has_irq_affinity = bool(re.search(r'\birq_set_affinity\s*\(', code))
    checks.append(check(
        "irq_affinity_set",
        has_irq_affinity,
        "irq_set_affinity found" if has_irq_affinity else "irq_set_affinity missing"
    ))

    # --- CHECK 12: System environment checklist present ---
    has_isolated_check = bool(re.search(r'/sys/devices/system/cpu/isolated', code))
    has_governor_check  = bool(re.search(r'scaling_governor', code))
    has_irq_affinity_check = bool(re.search(r'/proc/irq/default_smp_affinity|/proc/cmdline.*irqaffinity|irqaffinity.*cmdline', code, re.DOTALL))
    checklist_ok = has_isolated_check and has_governor_check
    checks.append(check(
        "system_environment_checklist_present",
        checklist_ok,
        f"isolcpus check={'yes' if has_isolated_check else 'no'}, governor check={'yes' if has_governor_check else 'no'}"
    ))

    # --- CHECK 13: Build command present ---
    has_build_cmd = bool(re.search(r'gcc\s+.*-lrt.*-lpthread|gcc\s+.*-lpthread.*-lrt', code))
    checks.append(check(
        "build_command_with_lrt_lpthread",
        has_build_cmd,
        "gcc build command with -lrt -lpthread found" if has_build_cmd else "gcc -lrt -lpthread build command missing"
    ))

    # --- Scoring ---
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Must pass critical checks to be considered overall pass
    critical_checks = [
        "uses_SCHED_FIFO",
        "priority_80_to_90",
        "no_printf_in_code",
        "uses_mmap_not_ioctl",
        "clock_nanosleep_with_TIMER_ABSTIME",
        "clock_nanosleep_at_end_of_loop",
        "no_busy_wait",
        "uses_request_threaded_irq",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))