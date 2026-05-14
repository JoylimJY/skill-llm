import sys
import os
import json
import re
from pathlib import Path

def find_report(workspace):
    """Search for health_report.txt anywhere in workspace."""
    candidates = list(Path(workspace).rglob("health_report.txt"))
    return candidates[0] if candidates else None

def run_checks(workspace):
    checks = []
    passed_all = True
    score_parts = []

    # ── Locate the report ────────────────────────────────────────────────────
    report_path = find_report(workspace)
    check_exists = {
        "name": "health_report.txt exists",
        "passed": report_path is not None,
        "detail": str(report_path) if report_path else "File not found anywhere in workspace",
    }
    checks.append(check_exists)
    if not report_path:
        passed_all = False
        return passed_all, 0.0, checks

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report readable", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    lines = content.strip().splitlines()
    content_stripped = "\n".join(lines)

    # ── Check 1: TCP open — localhost:5432 ────────────────────────────────────
    # Must show ✅ and "open" but NOT "HTTP" (TCP-only mode)
    pattern_5432_open = re.search(r'✅\s+localhost:5432\s+—\s+open(?!\s*\(HTTP)', content)
    c1 = {
        "name": "localhost:5432 — TCP open (no HTTP flag)",
        "passed": pattern_5432_open is not None,
        "detail": f"Found: {pattern_5432_open.group(0).strip()}" if pattern_5432_open else "Missing '✅ localhost:5432 — open' (TCP-only line)",
    }
    checks.append(c1)
    if not c1["passed"]: passed_all = False
    score_parts.append(1.0 if c1["passed"] else 0.0)

    # ── Check 2: TCP closed — localhost:6379 ──────────────────────────────────
    pattern_6379_closed = re.search(r'❌\s+localhost:6379\s+—\s+closed/timeout', content)
    c2 = {
        "name": "localhost:6379 — closed/timeout",
        "passed": pattern_6379_closed is not None,
        "detail": f"Found: {pattern_6379_closed.group(0).strip()}" if pattern_6379_closed else "Missing '❌ localhost:6379 — closed/timeout'",
    }
    checks.append(c2)
    if not c2["passed"]: passed_all = False
    score_parts.append(1.0 if c2["passed"] else 0.0)

    # ── Check 3: TCP closed — localhost:9999 ──────────────────────────────────
    pattern_9999_closed = re.search(r'❌\s+localhost:9999\s+—\s+closed/timeout', content)
    c3 = {
        "name": "localhost:9999 — closed/timeout",
        "passed": pattern_9999_closed is not None,
        "detail": f"Found: {pattern_9999_closed.group(0).strip()}" if pattern_9999_closed else "Missing '❌ localhost:9999 — closed/timeout'",
    }
    checks.append(c3)
    if not c3["passed"]: passed_all = False
    score_parts.append(1.0 if c3["passed"] else 0.0)

    # ── Check 4: HTTP 200 — localhost:8080 ────────────────────────────────────
    pattern_8080_200 = re.search(r'✅\s+localhost:8080\s+—\s+open\s+\(HTTP\s+200\)', content)
    c4 = {
        "name": "localhost:8080 — open (HTTP 200)",
        "passed": pattern_8080_200 is not None,
        "detail": f"Found: {pattern_8080_200.group(0).strip()}" if pattern_8080_200 else "Missing '✅ localhost:8080 — open (HTTP 200)'",
    }
    checks.append(c4)
    if not c4["passed"]: passed_all = False
    score_parts.append(1.0 if c4["passed"] else 0.0)

    # ── Check 5: HTTP 500 — localhost:8081 (port open, bad HTTP) ─────────────
    pattern_8081_500 = re.search(r'⚠️\s+localhost:8081\s+—\s+open\s+but\s+HTTP\s+500', content)
    c5 = {
        "name": "localhost:8081 — open but HTTP 500",
        "passed": pattern_8081_500 is not None,
        "detail": f"Found: {pattern_8081_500.group(0).strip()}" if pattern_8081_500 else "Missing '⚠️ localhost:8081 — open but HTTP 500'",
    }
    checks.append(c5)
    if not c5["passed"]: passed_all = False
    score_parts.append(1.0 if c5["passed"] else 0.0)

    # ── Check 6: All 5 expected targets present (completeness) ───────────────
    all_five = all([
        pattern_5432_open,
        pattern_6379_closed,
        pattern_9999_closed,
        pattern_8080_200,
        pattern_8081_500,
    ])
    c6 = {
        "name": "All 5 targets reported in health_report.txt",
        "passed": all_five,
        "detail": "All target lines present" if all_five else "One or more target lines missing",
    }
    checks.append(c6)
    if not c6["passed"]: passed_all = False
    score_parts.append(1.0 if c6["passed"] else 0.0)

    # ── Check 7: --http flag used for HTTP targets (HTTP lines present) ───────
    # This is implicit if checks 4 and 5 passed — but we also verify
    # that 5432 does NOT have "(HTTP" appended (must be TCP-only).
    tcp_only_correct = not bool(re.search(r'localhost:5432.*HTTP', content))
    c7 = {
        "name": "TCP-only targets not polluted with HTTP flag output",
        "passed": tcp_only_correct,
        "detail": "localhost:5432 correctly shows TCP-only output" if tcp_only_correct else "localhost:5432 incorrectly shows HTTP output",
    }
    checks.append(c7)
    if not c7["passed"]: passed_all = False
    score_parts.append(1.0 if c7["passed"] else 0.0)

    score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    # Must pass all core checks (1-5) to be considered truly passing
    core_passed = all([c1["passed"], c2["passed"], c3["passed"], c4["passed"], c5["passed"]])
    passed_all = core_passed

    return passed_all, round(score, 3), checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}],
        }
        print(json.dumps(result))
        return

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()