import sys
import json
import os
from pathlib import Path

def find_report(workspace):
    """Search for validation_audit_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("validation_audit_report.json"))
    return matches[0] if matches else None

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def check_passed(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    total_weight = 0
    passed_weight = 0

    # ── Check 0: Report file exists ──────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check_passed(
            "report_file_exists", False,
            "validation_audit_report.json not found anywhere in workspace"
        ))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check_passed("report_file_exists", True, f"Found at {report_path}"))

    try:
        report = load_json(report_path)
    except Exception as e:
        checks.append(check_passed("report_parseable", False, f"JSON parse error: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check_passed("report_parseable", True, "Valid JSON"))

    # ── Check 1: Report covers all 6 capsules ────────────────────────────────
    # Accept report as list or dict with a key containing results
    results_list = None
    if isinstance(report, list):
        results_list = report
    elif isinstance(report, dict):
        # Try common keys
        for key in ["results", "capsules", "audit", "findings", "skills"]:
            if key in report and isinstance(report[key], list):
                results_list = report[key]
                break
        if results_list is None:
            # Maybe the report IS a dict keyed by capsule id
            # Check if values are dicts with quality ratings
            vals = list(report.values())
            if all(isinstance(v, dict) for v in vals):
                results_list = vals

    if results_list is None or len(results_list) == 0:
        checks.append(check_passed(
            "covers_all_capsules", False,
            f"Could not extract a list of capsule results from report. Top-level type: {type(report)}, keys: {list(report.keys()) if isinstance(report, dict) else 'N/A'}"
        ))
        return {"passed": False, "score": 0.05, "checks": checks}

    checks.append(check_passed(
        "covers_all_capsules",
        len(results_list) >= 6,
        f"Found {len(results_list)} capsule entries (expected 6)"
    ))

    # ── Helper: find entry by capsule id or name ──────────────────────────────
    def find_entry(cap_id, name_fragment):
        for entry in results_list:
            if not isinstance(entry, dict):
                continue
            entry_str = json.dumps(entry).lower()
            if cap_id.lower() in entry_str or name_fragment.lower() in entry_str:
                return entry
        return None

    def get_quality(entry):
        """Extract quality rating from entry, case-insensitive."""
        if entry is None:
            return None
        entry_str = json.dumps(entry).upper()
        for rating in ["SUBSTANTIVE", "HOLLOW", "WEAK"]:
            if rating in entry_str:
                return rating
        return None

    def has_finding_keyword(entry, *keywords):
        """Check if entry mentions specific finding keywords."""
        if entry is None:
            return False
        entry_str = json.dumps(entry).lower()
        return any(kw.lower() in entry_str for kw in keywords)

    # Expected ratings per capsule:
    # cap-001: HOLLOW (echo-only, hardcoded success string)
    # cap-002: HOLLOW (tautological assertions: assert True, 1==1, 'hello'=='hello')
    # cap-003: HOLLOW (exit code gaming: || true, no real assertions)
    # cap-004: HOLLOW (commented-out real tests, only print('passed'))
    # cap-005: SUBSTANTIVE (real assertions with actual values)
    # cap-006: WEAK (has one real assertion but also || true exit code gaming)

    expected = [
        ("cap-001", "postgres", "HOLLOW",
         ["echo", "hardcoded", "echo-only", "hollow", "static", "print", "no actual"],
         "cap-001 should be HOLLOW (echo-only / hardcoded success string)"),
        ("cap-002", "json-schema", "HOLLOW",
         ["tautological", "assert true", "1 == 1", "always-true", "hollow"],
         "cap-002 should be HOLLOW (tautological assertions)"),
        ("cap-003", "api-rate", "HOLLOW",
         ["exit code", "|| true", "gaming", "suppress", "hollow"],
         "cap-003 should be HOLLOW (exit code gaming with || true, no assertions)"),
        ("cap-004", "encryption", "HOLLOW",
         ["commented", "commented-out", "hollow"],
         "cap-004 should be HOLLOW (commented-out real tests)"),
        ("cap-005", "csv", "SUBSTANTIVE",
         ["substantive", "real assert", "assert", "genuine"],
         "cap-005 should be SUBSTANTIVE (real assertions verifying actual behavior)"),
        ("cap-006", "markdown", "WEAK",
         ["weak", "mixed", "|| true", "exit code", "one real"],
         "cap-006 should be WEAK (mix of real assertion + || true gaming)"),
    ]

    rating_checks_passed = 0
    for cap_id, name_frag, expected_rating, evidence_kws, explanation in expected:
        entry = find_entry(cap_id, name_frag)
        actual_rating = get_quality(entry)
        rating_correct = (actual_rating == expected_rating)
        # For WEAK, also accept if HOLLOW (it's defensible given || true) but prefer WEAK
        if not rating_correct and expected_rating == "WEAK" and actual_rating == "HOLLOW":
            # Partial credit — the || true detection is correct, even if WEAK vs HOLLOW differs
            rating_correct = True  # accept HOLLOW for cap-006 since it does have || true
        if rating_correct:
            rating_checks_passed += 1
        checks.append(check_passed(
            f"rating_{cap_id}",
            rating_correct,
            f"{explanation} | Found entry: {entry is not None} | Detected rating: {actual_rating}"
        ))

    # ── Check 2: Assertion inventory present ─────────────────────────────────
    inventory_present = 0
    for entry in results_list:
        if not isinstance(entry, dict):
            continue
        entry_str = json.dumps(entry).lower()
        if ("real assertion" in entry_str or "hollow output" in entry_str or
                "commented" in entry_str or "assertion inventory" in entry_str or
                "real_assertions" in entry_str or "hollow_outputs" in entry_str):
            inventory_present += 1

    checks.append(check_passed(
        "assertion_inventory_present",
        inventory_present >= 3,
        f"{inventory_present}/6 entries contain assertion inventory data"
    ))

    # ── Check 3: cap-005 has real assertions > 0 ────────────────────────────
    cap005_entry = find_entry("cap-005", "csv")
    real_assertions_nonzero = False
    if cap005_entry:
        entry_str = json.dumps(cap005_entry).lower()
        import re
        # Look for real_assertions: N where N > 0
        nums = re.findall(r'real[_\s]assertions["\s:]+(\d+)', entry_str)
        if nums and any(int(n) > 0 for n in nums):
            real_assertions_nonzero = True
        # Also check if the word 'real' appears near a number > 0 near 'assert'
        if not real_assertions_nonzero and "3" in entry_str and "assert" in entry_str:
            real_assertions_nonzero = True  # cap-005 has 3 real assertions

    checks.append(check_passed(
        "cap005_real_assertions_counted",
        real_assertions_nonzero,
        f"cap-005 should show real assertion count > 0 | Entry found: {cap005_entry is not None}"
    ))

    # ── Check 4: cap-001 hollow outputs counted ──────────────────────────────
    cap001_entry = find_entry("cap-001", "postgres")
    hollow_counted = False
    if cap001_entry:
        entry_str = json.dumps(cap001_entry).lower()
        import re
        nums = re.findall(r'hollow[_\s]outputs?["\s:]+(\d+)', entry_str)
        if nums and any(int(n) >= 2 for n in nums):
            hollow_counted = True
        # Fallback: if hollow is mentioned with 2 commands noted
        if not hollow_counted and ("2" in entry_str and "hollow" in entry_str):
            hollow_counted = True

    checks.append(check_passed(
        "cap001_hollow_outputs_counted",
        hollow_counted,
        f"cap-001 should show >= 2 hollow outputs (echo + print hardcoded) | Entry found: {cap001_entry is not None}"
    ))

    # ── Check 5: cap-004 commented-out tests detected ────────────────────────
    cap004_entry = find_entry("cap-004", "encryption")
    commented_detected = has_finding_keyword(cap004_entry, "comment", "commented", "commented-out")
    checks.append(check_passed(
        "cap004_commented_tests_detected",
        commented_detected,
        f"cap-004 should mention commented-out tests | Entry found: {cap004_entry is not None}"
    ))

    # ── Check 6: cap-003 exit code gaming detected ────────────────────────────
    cap003_entry = find_entry("cap-003", "api-rate")
    exit_gaming_detected = has_finding_keyword(
        cap003_entry, "|| true", "exit code", "gaming", "suppress", "or true"
    )
    checks.append(check_passed(
        "cap003_exit_code_gaming_detected",
        exit_gaming_detected,
        f"cap-003 should flag '|| true' exit code gaming | Entry found: {cap003_entry is not None}"
      ))

    # ── Check 7: cap-002 tautological assertions detected ────────────────────
    cap002_entry = find_entry("cap-002", "json-schema")
    tautological_detected = has_finding_keyword(
        cap002_entry, "tautological", "assert true", "always-true", "trivial", "1 == 1", "1==1"
    )
    checks.append(check_passed(
        "cap002_tautological_detected",
        tautological_detected,
        f"cap-002 should flag tautological assertions | Entry found: {cap002_entry is not None}"
    ))

    # ── Check 8: cap-006 WEAK correctly handled ──────────────────────────────
    cap006_entry = find_entry("cap-006", "markdown")
    cap006_rating = get_quality(cap006_entry)
    cap006_ok = cap006_rating in ("WEAK", "HOLLOW")  # both defensible; WEAK preferred
    checks.append(check_passed(
        "cap006_weak_or_hollow",
        cap006_ok,
        f"cap-006 should be WEAK (or HOLLOW as fallback) due to mixed real assertion + || true | Detected: {cap006_rating}"
    ))

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 5,
        "report_parseable": 5,
        "covers_all_capsules": 5,
        "rating_cap-001": 10,
        "rating_cap-002": 10,
        "rating_cap-003": 10,
        "rating_cap-004": 10,
        "rating_cap-005": 10,
        "rating_cap-006": 5,
        "assertion_inventory_present": 5,
        "cap005_real_assertions_counted": 5,
        "cap001_hollow_outputs_counted": 5,
        "cap004_commented_tests_detected": 5,
        "cap003_exit_code_gaming_detected": 5,
        "cap002_tautological_detected": 5,
        "cap006_weak_or_hollow": 0,  # already counted in rating check
    }

    total = sum(weights.values())
    earned = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round(earned / total, 3)

    # Overall pass: must get ratings right on 5/6 capsules AND file exists AND parseable
    rating_check_names = [f"rating_cap-00{i}" for i in range(1, 7)]
    rating_passed = sum(1 for c in checks if c["name"] in rating_check_names and c["passed"])

    overall_passed = (
        any(c["name"] == "report_file_exists" and c["passed"] for c in checks) and
        any(c["name"] == "report_parseable" and c["passed"] for c in checks) and
        rating_passed >= 5 and
        score >= 0.65
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))