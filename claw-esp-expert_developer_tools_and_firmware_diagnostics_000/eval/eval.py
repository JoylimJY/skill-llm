#!/usr/bin/env python3
"""
Evaluation script for the ESP-IDF GPIO audit + partition overflow task.
Checks that the agent produced a correct audit_report.json with:
1. explore_demo results for GPIO (demo summary + hardware requirements)
2. safe_build audit result showing FATAL GPIO pin conflicts on esp32c6
3. analyze_partitions patch (before/after CSV recommendation)
"""
import sys
import json
import re
from pathlib import Path

def load_json_file(path: Path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_report(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob('audit_report.json'))
    if candidates:
        return candidates[0]
    return None

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/workspace')
    checks = []
    total_score = 0.0

    # ── Find the report ──────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False,
                        "detail": "audit_report.json not found anywhere in workspace"}]
        }))
        return

    try:
        report = load_json_file(report_path)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_parseable", "passed": False,
                        "detail": f"Could not parse audit_report.json: {e}"}]
        }))
        return

    report_str = json.dumps(report).lower()

    # ── CHECK 1: explore_demo was invoked and results captured ───────────────
    check1_passed = False
    check1_detail = ""
    try:
        # Look for demo-related content: gpio keyword, hardware requirements, path info
        has_gpio_demo = (
            'gpio' in report_str and
            ('explore_demo' in report_str or 'demo' in report_str or 'example' in report_str)
        )
        has_hw_requirements = any(kw in report_str for kw in [
            'hardware', 'led', 'button', 'devkit', 'resistor', 'hardware_requirements'
        ])
        has_demo_path = any(kw in report_str for kw in [
            'peripherals/gpio', 'generic_gpio', 'examples'
        ])
        check1_passed = has_gpio_demo and has_hw_requirements and has_demo_path
        check1_detail = (
            f"gpio_demo={has_gpio_demo}, hw_reqs={has_hw_requirements}, demo_path={has_demo_path}"
        )
    except Exception as e:
        check1_detail = f"Exception: {e}"

    checks.append({
        "name": "explore_demo_gpio_results_captured",
        "passed": check1_passed,
        "detail": check1_detail
    })
    if check1_passed:
        total_score += 0.25

    # ── CHECK 2: safe_build used normalized chip 'esp32c6' (not SKU) ─────────
    check2_passed = False
    check2_detail = ""
    try:
        # Must contain 'esp32c6' as the chip identifier (normalized)
        has_normalized_chip = 'esp32c6' in report_str
        # Must NOT only contain the raw SKU without normalization evidence
        has_audit = any(kw in report_str for kw in ['safe_build', 'audit', 'build'])
        check2_passed = has_normalized_chip and has_audit
        check2_detail = f"normalized_chip_esp32c6={has_normalized_chip}, audit_present={has_audit}"
    except Exception as e:
        check2_detail = f"Exception: {e}"

    checks.append({
        "name": "safe_build_uses_normalized_chip_esp32c6",
        "passed": check2_passed,
        "detail": check2_detail
    })
    if check2_passed:
        total_score += 0.20

    # ── CHECK 3: FATAL GPIO pin conflicts detected for strapping pins ─────────
    check3_passed = False
    check3_detail = ""
    try:
        # GPIO 8 and/or GPIO 9 must be flagged as FATAL strapping pin conflicts
        has_fatal = 'fatal' in report_str
        has_strapping = 'strapping' in report_str
        has_pin8_or_9 = ('gpio 8' in report_str or '"pin": 8' in report_str or
                         'gpio_num_8' in report_str.lower() or
                         'gpio 9' in report_str or '"pin": 9' in report_str or
                         'status_led_pin' in report_str or 'trigger_pin' in report_str)
        has_audit_failed = any(kw in report_str for kw in [
            'audit_rejected', 'audit failed', '"status": "failed"',
            'fatal_count', 'findings'
        ])
        check3_passed = has_fatal and has_strapping and has_pin8_or_9
        check3_detail = (
            f"fatal={has_fatal}, strapping={has_strapping}, "
            f"pin8_or_9={has_pin8_or_9}, audit_failed={has_audit_failed}"
        )
    except Exception as e:
        check3_detail = f"Exception: {e}"

    checks.append({
        "name": "fatal_gpio_strapping_pin_conflicts_reported",
        "passed": check3_passed,
        "detail": check3_detail
    })
    if check3_passed:
        total_score += 0.25

    # ── CHECK 4: analyze_partitions patch captured (before/after CSV) ─────────
    check4_passed = False
    check4_detail = ""
    try:
        # Must include partition overflow info and the patch (before/after)
        has_overflow = any(kw in report_str for kw in [
            'overflow', 'partition_overflow', 'analyze_partitions'
        ])
        has_patch = any(kw in report_str for kw in [
            'patch', 'before', 'after', 'csv_draft', 'recommended_size'
        ])
        has_factory = 'factory' in report_str
        # Recommended size must be larger than 0x1a0000
        # Look for any hex value > 0x1a0000 = 1703936
        hex_values = re.findall(r'0x([0-9a-fA-F]+)', json.dumps(report))
        has_larger_size = any(
            int(h, 16) > 0x1A0000 for h in hex_values
            if len(h) <= 8
        )
        check4_passed = has_overflow and has_patch and has_factory and has_larger_size
        check4_detail = (
            f"overflow={has_overflow}, patch={has_patch}, "
            f"factory={has_factory}, larger_recommended_size={has_larger_size}"
        )
    except Exception as e:
        check4_detail = f"Exception: {e}"

    checks.append({
        "name": "analyze_partitions_patch_captured",
        "passed": check4_passed,
        "detail": check4_detail
    })
    if check4_passed:
        total_score += 0.20

    # ── CHECK 5: Report is a structured JSON (not just raw logs) ─────────────
    check5_passed = False
    check5_detail = ""
    try:
        # Must be a dict or list, not just a string blob
        is_structured = isinstance(report, (dict, list))
        # Must have at least 2 top-level sections
        if isinstance(report, dict):
            has_multiple_sections = len(report.keys()) >= 2
        elif isinstance(report, list):
            has_multiple_sections = len(report) >= 2
        else:
            has_multiple_sections = False
        check5_passed = is_structured and has_multiple_sections
        check5_detail = (
            f"is_structured={is_structured}, "
            f"top_level_keys={list(report.keys()) if isinstance(report, dict) else len(report)}"
        )
    except Exception as e:
        check5_detail = f"Exception: {e}"

    checks.append({
        "name": "report_is_structured_json",
        "passed": check5_passed,
        "detail": check5_detail
    })
    if check5_passed:
        total_score += 0.10

    # ── Final verdict ─────────────────────────────────────────────────────────
    # Must pass checks 1, 3, and 4 as a minimum (the proprietary traps)
    critical_checks = [check1_passed, check3_passed, check4_passed]
    overall_passed = all(critical_checks) and total_score >= 0.60

    print(json.dumps({
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }, indent=2))


if __name__ == '__main__':
    main()