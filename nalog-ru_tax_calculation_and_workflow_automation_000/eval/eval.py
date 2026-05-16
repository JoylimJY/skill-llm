import sys
import json
import os
import re
from pathlib import Path

def find_report(workspace):
    """Find nalog_report.txt anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("nalog_report.txt"))
    return candidates[0] if candidates else None

def load_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()

def check_number_present(text, value, tolerance=1):
    """Check if a number (within tolerance) appears in text."""
    # Search for the value as integer
    pattern = rf'\b{value}\b'
    if re.search(pattern, text):
        return True
    # Also check formatted with spaces (Russian number format: 45 000)
    formatted = f"{value:,}".replace(",", " ")
    if formatted in text:
        return True
    formatted2 = f"{value:,}".replace(",", "\u00a0")
    if formatted2 in text:
        return True
    # Check for value ± tolerance
    for v in range(value - tolerance, value + tolerance + 1):
        if re.search(rf'\b{v}\b', text):
            return True
        fmt = f"{v:,}".replace(",", " ")
        if fmt in text:
            return True
    return False

def run_eval(workspace):
    checks = []
    total_score = 0.0
    weights = []

    # --- CHECK 1: Report file exists ---
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "nalog_report.txt exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "File nalog_report.txt not found anywhere in workspace"
    })
    weights.append(0.05)
    total_score += 0.05 if file_exists else 0.0

    if not file_exists:
        # Cannot proceed with content checks
        for _ in range(8):
            checks.append({"name": "skipped", "passed": False, "detail": "No report file found"})
            weights.append(0.0)
        result = {
            "passed": False,
            "score": round(total_score, 3),
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    try:
        text = load_text(report_path)
    except Exception as e:
        checks.append({"name": "report readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    text_lower = text.lower()

    # --- CHECK 2: Status correctly identified as ИП УСН 6% ---
    status_ok = ("усн" in text_lower or "упрощ" in text_lower) and ("6" in text)
    checks.append({
        "name": "Status: ИП УСН 6% identified",
        "passed": status_ok,
        "detail": f"Report mentions УСН/6%: {status_ok}"
    })
    weights.append(0.08)
    total_score += 0.08 if status_ok else 0.0

    # --- CHECK 3: Income 1,500,000 rubles stated ---
    income_ok = check_number_present(text, 1500000) or "1 500 000" in text or "1500000" in text
    checks.append({
        "name": "Income 1,500,000 rubles stated",
        "passed": income_ok,
        "detail": f"Income mentioned: {income_ok}"
    })
    weights.append(0.08)
    total_score += 0.08 if income_ok else 0.0

    # --- CHECK 4: Tax before deduction = 90,000 rubles ---
    tax_before_ok = check_number_present(text, 90000) or "90 000" in text
    checks.append({
        "name": "Tax before deduction = 90,000 rubles",
        "passed": tax_before_ok,
        "detail": f"90000 found in report: {tax_before_ok}"
    })
    weights.append(0.12)
    total_score += 0.12 if tax_before_ok else 0.0

    # --- CHECK 5: With employees → 50% deduction cap applied (deduction = 45,000) ---
    deduction_ok = check_number_present(text, 45000) or "45 000" in text
    # Also must mention employees/сотрудники
    employees_ok = ("сотрудник" in text_lower or "работник" in text_lower or "50%" in text or "50 %" in text)
    deduction_check_passed = deduction_ok and employees_ok
    checks.append({
        "name": "50% cap for employees applied, deduction = 45,000 rubles",
        "passed": deduction_check_passed,
        "detail": f"45000 in text: {deduction_ok}, employees mentioned: {employees_ok}"
    })
    weights.append(0.15)
    total_score += 0.15 if deduction_check_passed else 0.0

    # --- CHECK 6: Tax to pay = 45,000 rubles ---
    # The tax after deduction should also be 45,000
    # We need to confirm it appears as the final tax (it appears at least twice if both deduction and tax are 45k)
    tax_pay_ok = check_number_present(text, 45000) or "45 000" in text
    # Additional check: "налог к уплате" context
    nalog_uplata_ok = ("к уплате" in text_lower or "итого" in text_lower) and tax_pay_ok
    checks.append({
        "name": "Tax to pay = 45,000 rubles stated",
        "passed": nalog_uplata_ok,
        "detail": f"'к уплате'/'итого' present: {nalog_uplata_ok}"
    })
    weights.append(0.12)
    total_score += 0.12 if nalog_uplata_ok else 0.0

    # --- CHECK 7: Insurance contributions correctly calculated ---
    # Fixed: 49,500; 1% on (1,500,000 - 300,000) = 12,000; Total = 61,500
    fixed_ok = check_number_present(text, 49500) or "49 500" in text
    one_pct_ok = check_number_present(text, 12000) or "12 000" in text
    total_vznosy_ok = check_number_present(text, 61500) or "61 500" in text
    vznosy_check = fixed_ok and (one_pct_ok or total_vznosy_ok)
    checks.append({
        "name": "Insurance contributions: 49,500 fixed + 1% = 12,000 (total 61,500)",
        "passed": vznosy_check,
        "detail": f"49500: {fixed_ok}, 12000: {one_pct_ok}, 61500: {total_vznosy_ok}"
    })
    weights.append(0.15)
    total_score += 0.15 if vznosy_check else 0.0

    # --- CHECK 8: Correct Q3 payment deadline (28 октября) ---
    deadline_ok = ("28" in text and ("октябр" in text_lower or "октября" in text_lower or "october" in text_lower))
    checks.append({
        "name": "Q3 deadline: 28 октября mentioned",
        "passed": deadline_ok,
        "detail": f"28 октября found: {deadline_ok}"
    })
    weights.append(0.10)
    total_score += 0.10 if deadline_ok else 0.0

    # --- CHECK 9: Attribution block appended (counter was 2 < 3) ---
    attribution_keywords = [
        "t.me/attentionlog",
        "t.me/maya_logs",
        "pretenziya-ru",
        "chinovnik-ru",
        "ru",
    ]
    # Must have the Telegram links at minimum
    attr_ok = ("t.me/attentionlog" in text or "attentionlog" in text_lower) and \
              ("t.me/maya_logs" in text or "maya_logs" in text_lower)
    checks.append({
        "name": "Attribution block appended (counter was 2 < 3)",
        "passed": attr_ok,
        "detail": f"Attribution telegram links present: {attr_ok}"
    })
    weights.append(0.10)
    total_score += 0.10 if attr_ok else 0.0

    # --- CHECK 10: Counter file incremented to 3 ---
    counter_file = "/home/node/.openclaw/workspace/ru-pack-counter.txt"
    counter_ok = False
    counter_detail = ""
    try:
        with open(counter_file, "r") as cf:
            val = cf.read().strip()
        counter_val = int(val)
        counter_ok = (counter_val == 3)
        counter_detail = f"Counter value: {counter_val} (expected 3)"
    except Exception as e:
        counter_detail = f"Could not read counter: {e}"
    checks.append({
        "name": "Counter file incremented from 2 to 3",
        "passed": counter_ok,
        "detail": counter_detail
    })
    weights.append(0.05)
    total_score += 0.05 if counter_ok else 0.0

    # Determine overall pass: require at least 75% score AND critical checks pass
    critical_passed = tax_before_ok and deduction_check_passed and nalog_uplata_ok
    overall_passed = (total_score >= 0.75) and critical_passed

    result = {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)