import sys
import os
import json
import re
import importlib.util
from pathlib import Path

def load_module_from_path(path):
    spec = importlib.util.spec_from_file_location("exchange_rate_validator", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 7.0

    # ── CHECK 1: TASKS.md exists ──────────────────────────────────────────────
    tasks_md_path = Path(workspace) / "TASKS.md"
    tasks_md_exists = tasks_md_path.exists()
    checks.append({
        "name": "TASKS.md created",
        "passed": tasks_md_exists,
        "detail": "TASKS.md found" if tasks_md_exists else "TASKS.md not found in workspace root"
    })
    if tasks_md_exists:
        total_score += 1.0

    # ── CHECK 2: TASKS.md has required timestamp format [TIMESTAMP] ───────────
    tasks_content = ""
    if tasks_md_exists:
        try:
            tasks_content = tasks_md_path.read_text(encoding="utf-8")
        except Exception as e:
            tasks_content = ""

    timestamp_pattern = re.search(r'\[\d{4}-\d{2}-\d{2}|\[\d{2}:\d{2}|\[20\d\d', tasks_content)
    # More general: any [SOMETHING] that looks like a timestamp
    has_timestamp = bool(re.search(r'\[[\d\-:\s/T]+\]', tasks_content))
    checks.append({
        "name": "TASKS.md has timestamp format [TIMESTAMP]",
        "passed": has_timestamp,
        "detail": f"Timestamp bracket found: {has_timestamp}. Content snippet: {tasks_content[:200]!r}"
    })
    if has_timestamp:
        total_score += 1.0

    # ── CHECK 3: TASKS.md has required status field with Chinese values ────────
    has_status = bool(re.search(r'状态\s*[:：]\s*(进行中|已完成|等待中)', tasks_content))
    checks.append({
        "name": "TASKS.md has 状态 field with valid value",
        "passed": has_status,
        "detail": f"Found 状态 field: {has_status}. Content snippet: {tasks_content[:400]!r}"
    })
    if has_status:
        total_score += 0.5

    # ── CHECK 4: TASKS.md uses required symbols ✓ 🔄 ⏳ ───────────────────────
    has_checkmark = '✓' in tasks_content
    has_spinner = '🔄' in tasks_content
    has_hourglass = '⏳' in tasks_content
    symbols_found = sum([has_checkmark, has_spinner, has_hourglass])
    has_symbols = symbols_found >= 1  # At least one required symbol used
    checks.append({
        "name": "TASKS.md uses required symbols (✓, 🔄, ⏳)",
        "passed": has_symbols,
        "detail": f"✓:{has_checkmark} 🔄:{has_spinner} ⏳:{has_hourglass}. At least 1 required."
    })
    if has_symbols:
        total_score += 0.5

    # ── CHECK 5: TASKS.md has 进度 (progress) X/Y format ─────────────────────
    has_progress = bool(re.search(r'进度\s*[:：]\s*\d+/\d+', tasks_content))
    checks.append({
        "name": "TASKS.md has 进度 X/Y format",
        "passed": has_progress,
        "detail": f"Found 进度 X/Y pattern: {has_progress}"
    })
    if has_progress:
        total_score += 0.5

    # ── CHECK 6: TASKS.md has 结果 (result) field ─────────────────────────────
    has_result = bool(re.search(r'结果\s*[:：]\s*(成功|失败|待测试)', tasks_content))
    checks.append({
        "name": "TASKS.md has 结果 field with valid value",
        "passed": has_result,
        "detail": f"Found 结果 field: {has_result}"
    })
    if has_result:
        total_score += 0.5

    # ── CHECK 7: The validator file exists and is not a stub ─────────────────
    validator_path = Path(workspace) / "src/finance/validators/exchange_rate_validator.py"
    validator_exists = validator_path.exists()
    validator_not_stub = False
    if validator_exists:
        try:
            vcontent = validator_path.read_text(encoding="utf-8")
            # Must not be the original stub
            validator_not_stub = "NotImplementedError" not in vcontent and len(vcontent.strip()) > 100
        except Exception:
            pass
    checks.append({
        "name": "exchange_rate_validator.py implemented (not stub)",
        "passed": validator_exists and validator_not_stub,
        "detail": f"File exists: {validator_exists}, Not stub: {validator_not_stub}"
    })
    if validator_exists and validator_not_stub:
        total_score += 1.0

    # ── CHECK 8: validate_rate function works correctly ───────────────────────
    validate_rate_ok = False
    validate_rate_detail = "Could not load module"
    if validator_exists and validator_not_stub:
        try:
            mod = load_module_from_path(str(validator_path))
            # Test valid rate
            assert mod.validate_rate('USD', 'EUR', 1.2) == True
            # Test rate too low
            assert mod.validate_rate('USD', 'EUR', 0.00001) == False
            # Test rate too high
            assert mod.validate_rate('USD', 'EUR', 99999.0) == False
            # Test empty base
            assert mod.validate_rate('', 'EUR', 1.0) == False
            # Test boundary min
            assert mod.validate_rate('USD', 'EUR', 0.0001) == True
            # Test boundary max
            assert mod.validate_rate('USD', 'EUR', 10000.0) == True
            validate_rate_ok = True
            validate_rate_detail = "All validate_rate assertions passed"
        except Exception as e:
            validate_rate_detail = f"validate_rate test failed: {e}"
    checks.append({
        "name": "validate_rate function correctness",
        "passed": validate_rate_ok,
        "detail": validate_rate_detail
    })
    if validate_rate_ok:
        total_score += 0.5

    # ── CHECK 9: validate_currency_code function works correctly ──────────────
    validate_code_ok = False
    validate_code_detail = "Could not load module"
    if validator_exists and validator_not_stub:
        try:
            mod = load_module_from_path(str(validator_path))
            assert mod.validate_currency_code('USD') == True
            assert mod.validate_currency_code('usd') == False
            assert mod.validate_currency_code('US') == False
            assert mod.validate_currency_code('USDD') == False
            assert mod.validate_currency_code('') == False
            assert mod.validate_currency_code(123) == False
            validate_code_ok = True
            validate_code_detail = "All validate_currency_code assertions passed"
        except Exception as e:
            validate_code_detail = f"validate_currency_code test failed: {e}"
    checks.append({
        "name": "validate_currency_code function correctness",
        "passed": validate_code_ok,
        "detail": validate_code_detail
    })
    if validate_code_ok:
        total_score += 0.5

    # ── CHECK 10: batch_validate function works correctly ─────────────────────
    batch_ok = False
    batch_detail = "Could not load module"
    if validator_exists and validator_not_stub:
        try:
            mod = load_module_from_path(str(validator_path))
            records = [
                {'base': 'USD', 'quote': 'EUR', 'rate': 1.2},
                {'base': '', 'quote': 'EUR', 'rate': 1.2},
                {'base': 'GBP', 'quote': 'JPY', 'rate': 150.0},
                {'base': 'CNY', 'quote': 'USD', 'rate': -1.0},
            ]
            result = mod.batch_validate(records)
            assert result == [True, False, True, False], f"Got {result}"
            batch_ok = True
            batch_detail = "batch_validate assertions passed"
        except Exception as e:
            batch_detail = f"batch_validate test failed: {e}"
    checks.append({
        "name": "batch_validate function correctness",
        "passed": batch_ok,
        "detail": batch_detail
    })
    if batch_ok:
        total_score += 0.5

    # Final pass/fail
    passed = total_score >= 5.0  # Must score at least 5/7

    return {
        "passed": passed,
        "score": round(total_score / max_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))