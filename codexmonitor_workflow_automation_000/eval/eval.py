#!/usr/bin/env python3
"""
Evaluation script for the codexmonitor audit task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    
    checks = []
    
    # ── Load ground truth ────────────────────────────────────────────────
    try:
        with open(workspace / ".mock_codexmonitor_data.json") as f:
            truth = json.load(f)
        SESSION_A_ID = truth["session_a"]["id"]
        SESSION_B_ID = truth["session_b"]["id"]
        EXPECTED_SESSIONS_DIR = truth["sessions_root"]
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "load_truth", "passed": False, "detail": str(e)}]
        }))
        return

    # ── Load invocation log ───────────────────────────────────────────────
    invocations = []
    try:
        log_file = workspace / ".mock_codexmonitor_invocations.jsonl"
        with open(log_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    invocations.append(json.loads(line))
    except Exception as e:
        invocations = []

    # ── CHECK 1: CODEX_SESSIONS_DIR was set correctly ─────────────────────
    check1_passed = False
    check1_detail = "No invocations found with correct CODEX_SESSIONS_DIR"
    for inv in invocations:
        env = inv.get("env", {})
        set_dir = env.get("CODEX_SESSIONS_DIR", "")
        set_home = env.get("CODEX_HOME", "")
        # Check CODEX_SESSIONS_DIR points to the sessions root
        if set_dir and (set_dir.rstrip("/") == EXPECTED_SESSIONS_DIR.rstrip("/")):
            check1_passed = True
            check1_detail = f"CODEX_SESSIONS_DIR correctly set to {set_dir}"
            break
        # Also accept CODEX_HOME=/workspace/codex_archive (sessions subdir)
        if set_home:
            derived = (Path(set_home) / "sessions")
            if str(derived).rstrip("/") == EXPECTED_SESSIONS_DIR.rstrip("/"):
                check1_passed = True
                check1_detail = f"CODEX_HOME correctly set to {set_home} (sessions={derived})"
                break

    checks.append({"name": "correct_sessions_dir_env", "passed": check1_passed, "detail": check1_detail})

    # ── CHECK 2: list --json used with correct date format ────────────────
    check2_passed = False
    check2_detail = "No 'list --json 2025/03/15' invocation found"
    for inv in invocations:
        args = inv.get("args", [])
        if args and args[0] == "list" and "--json" in args:
            # Check date arg in YYYY/MM/DD format
            for a in args:
                if re.match(r"^\d{4}/\d{2}/\d{2}$", a) and a == "2025/03/15":
                    check2_passed = True
                    check2_detail = f"Found: codexmonitor list --json 2025/03/15"
                    break
        if check2_passed:
            break
    checks.append({"name": "list_json_correct_date_format", "passed": check2_passed, "detail": check2_detail})

    # ── CHECK 3: show called with SESSION_A (most turns = 30) ─────────────
    check3_passed = False
    check3_detail = f"No 'show {SESSION_A_ID}' invocation found (should pick session with 30 turns)"
    for inv in invocations:
        args = inv.get("args", [])
        if args and args[0] == "show" and SESSION_A_ID in args:
            check3_passed = True
            check3_detail = f"Correctly targeted session A ({SESSION_A_ID}) with 30 turns"
            break
    checks.append({"name": "show_correct_session_most_turns", "passed": check3_passed, "detail": check3_detail})

    # ── CHECK 4: --ranges used with TRIPLE-DOT notation ───────────────────
    check4_passed = False
    check4_detail = "No --ranges invocation with triple-dot notation found"
    triple_dot_pattern = re.compile(r"\d+\.\.\.\d+")
    for inv in invocations:
        args = inv.get("args", [])
        if args and args[0] == "show" and "--ranges" in args:
            idx = args.index("--ranges")
            if idx + 1 < len(args):
                rng_val = args[idx + 1]
                # Must use triple dots (...)
                if triple_dot_pattern.search(rng_val) and "..." in rng_val:
                    # Must NOT use double-dot or dash as primary separator
                    # Ensure we have triple dots (3 dots, not 2)
                    parts = rng_val.split(",")
                    all_triple = all(re.match(r"^\d+\.\.\.\d+$", p.strip()) for p in parts)
                    if all_triple:
                        check4_passed = True
                        check4_detail = f"Correct triple-dot range syntax used: '{rng_val}'"
                        break
    checks.append({"name": "ranges_triple_dot_notation", "passed": check4_passed, "detail": check4_detail})

    # ── CHECK 5: ranges cover first 3 AND last 3 turns (1...3 and 28...30) ──
    check5_passed = False
    check5_detail = "Ranges did not cover turns 1-3 and 28-30"
    for inv in invocations:
        args = inv.get("args", [])
        if args and args[0] == "show" and "--ranges" in args:
            idx = args.index("--ranges")
            if idx + 1 < len(args):
                rng_val = args[idx + 1]
                parts = [p.strip() for p in rng_val.split(",")]
                covered_start = set()
                covered_end = set()
                for p in parts:
                    m = re.match(r"^(\d+)\.\.\.(\d+)$", p)
                    if m:
                        s, e = int(m.group(1)), int(m.group(2))
                        for n in range(s, e+1):
                            if 1 <= n <= 3:
                                covered_start.add(n)
                            if 28 <= n <= 30:
                                covered_end.add(n)
                if covered_start >= {1,2,3} and covered_end >= {28,29,30}:
                    check5_passed = True
                    check5_detail = f"Ranges cover turns 1-3 and 28-30 correctly: '{rng_val}'"
                    break
    checks.append({"name": "ranges_cover_first_and_last_three_turns", "passed": check5_passed, "detail": check5_detail})

    # ── CHECK 6: audit_report.json exists and is valid ────────────────────
    check6_passed = False
    check6_detail = "audit_report.json not found"
    report_data = None
    try:
        matches = list(workspace.rglob("audit_report.json"))
        if not matches:
            check6_detail = "audit_report.json not found anywhere in workspace"
        else:
            report_path = matches[0]
            with open(report_path) as f:
                report_data = json.load(f)
            check6_passed = True
            check6_detail = f"Found audit_report.json at {report_path}"
    except json.JSONDecodeError as e:
        check6_detail = f"audit_report.json is not valid JSON: {e}"
    except Exception as e:
        check6_detail = f"Error reading audit_report.json: {e}"
    checks.append({"name": "audit_report_exists_valid_json", "passed": check6_passed, "detail": check6_detail})

    # ── CHECK 7: report contains session_id of session A ─────────────────
    check7_passed = False
    check7_detail = "Report missing session_id of the longest session"
    if report_data:
        report_str = json.dumps(report_data)
        if SESSION_A_ID in report_str:
            check7_passed = True
            check7_detail = f"Report references correct session ID: {SESSION_A_ID}"
        else:
            check7_detail = f"Session A ID ({SESSION_A_ID}) not found in report"
    checks.append({"name": "report_contains_session_a_id", "passed": check7_passed, "detail": check7_detail})

    # ── CHECK 8: report contains content from first 3 turns ───────────────
    check8_passed = False
    check8_detail = "Report missing content from first 3 turns"
    if report_data:
        report_str = json.dumps(report_data)
        first_3_contents = [truth["session_a"]["turns_data"][i]["content"][:30] for i in range(3)]
        found_count = sum(1 for c in first_3_contents if c in report_str)
        if found_count >= 2:
            check8_passed = True
            check8_detail = f"Report contains content from {found_count}/3 opening turns"
        else:
            check8_detail = f"Report contains content from only {found_count}/3 opening turns"
    checks.append({"name": "report_contains_opening_turns", "passed": check8_passed, "detail": check8_detail})

    # ── CHECK 9: report contains content from last 3 turns ────────────────
    check9_passed = False
    check9_detail = "Report missing content from last 3 turns"
    if report_data:
        report_str = json.dumps(report_data)
        last_3_contents = [truth["session_a"]["turns_data"][i]["content"][:30] for i in [27, 28, 29]]
        found_count = sum(1 for c in last_3_contents if c in report_str)
        if found_count >= 2:
            check9_passed = True
            check9_detail = f"Report contains content from {found_count}/3 closing turns"
        else:
            check9_detail = f"Report contains content from only {found_count}/3 closing turns"
    checks.append({"name": "report_contains_closing_turns", "passed": check9_passed, "detail": check9_detail})

    # ── CHECK 10: report includes date 2025/03/15 or 2025-03-15 ──────────
    check10_passed = False
    check10_detail = "Report missing target date"
    if report_data:
        report_str = json.dumps(report_data)
        if "2025/03/15" in report_str or "2025-03-15" in report_str:
            check10_passed = True
            check10_detail = "Report includes target date 2025/03/15 or 2025-03-15"
    checks.append({"name": "report_includes_target_date", "passed": check10_passed, "detail": check10_detail})

    # ── Scoring ───────────────────────────────────────────────────────────
    critical_checks = [0, 1, 2, 3, 4, 5, 6]  # indices of critical checks
    all_passed = all(c["passed"] for c in checks)
    critical_passed = all(checks[i]["passed"] for i in critical_checks)
    score = sum(c["passed"] for c in checks) / len(checks)

    result = {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()