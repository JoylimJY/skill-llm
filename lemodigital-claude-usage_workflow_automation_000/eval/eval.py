#!/usr/bin/env python3
"""
Evaluation script for the Claude usage report task.
Checks:
1. usage_report.json exists somewhere in workspace
2. JSON is valid
3. Contains exactly top-3 sessions (not more, not fewer)
4. Sessions are ranked by credits descending
5. Credit values are correct using the proprietary formula (within tolerance)
6. Gemini session has 0 credits (non-Claude rule)
7. Config was saved (so --save was used)
8. Cache reads are free (verified through correct credit totals)
"""

import json
import sys
import math
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # ─── Load ground truth ────────────────────────────────────────────────────
    gt_path = workspace / ".eval_ground_truth.json"
    try:
        with open(gt_path) as f:
            gt = json.load(f)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [check("load_ground_truth", False, str(e))]
        }))
        return

    expected_top3 = gt["top3_keys"]
    expected_credits = {k: v["expected_credits"] for k, v in gt["sessions"].items()}

    # ─── 1. Find usage_report.json ────────────────────────────────────────────
    report_files = list(workspace.rglob("usage_report.json"))
    # Also check home dir
    home_files = list(Path("/root").rglob("usage_report.json"))
    all_files = report_files + home_files

    if not all_files:
        checks.append(check("file_exists", False, "usage_report.json not found anywhere in workspace or home"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = all_files[0]
    checks.append(check("file_exists", True, f"Found at {report_path}"))

    # ─── 2. Valid JSON ────────────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append(check("valid_json", True, "JSON parsed successfully"))
    except Exception as e:
        checks.append(check("valid_json", False, f"JSON parse error: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ─── 3. Has 'sessions' list ───────────────────────────────────────────────
    sessions = report.get("sessions", None)
    if not isinstance(sessions, list):
        checks.append(check("has_sessions_list", False, f"'sessions' key missing or not a list. Keys: {list(report.keys())}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    checks.append(check("has_sessions_list", True, f"'sessions' list present with {len(sessions)} entries"))

    # ─── 4. Exactly top 3 sessions ────────────────────────────────────────────
    if len(sessions) == 3:
        checks.append(check("exactly_top3", True, "Exactly 3 sessions in report"))
    else:
        checks.append(check("exactly_top3", False, f"Expected 3 sessions, got {len(sessions)}"))

    # ─── 5. Sessions are correct top-3 by credits ─────────────────────────────
    reported_keys = []
    for s in sessions:
        key = s.get("session_key") or s.get("key") or s.get("name") or ""
        reported_keys.append(key)

    # Check that top-3 keys match (order matters for ranking check)
    top3_match = (set(reported_keys) == set(expected_top3))
    checks.append(check("correct_top3_sessions", top3_match,
        f"Expected sessions: {expected_top3}, Got: {reported_keys}"))

    # ─── 6. Sessions ordered by credits descending ────────────────────────────
    reported_credits_list = []
    for s in sessions:
        c = s.get("credits") or s.get("credits_used") or 0
        try:
            reported_credits_list.append(float(c))
        except Exception:
            reported_credits_list.append(0.0)

    is_sorted = all(reported_credits_list[i] >= reported_credits_list[i+1]
                    for i in range(len(reported_credits_list)-1))
    checks.append(check("sessions_sorted_descending", is_sorted,
        f"Credits in order: {reported_credits_list}"))

    # ─── 7. Credit values correct (proprietary formula) ───────────────────────
    TOLERANCE = 0.5  # Allow tiny floating point diff but not formula errors

    credit_check_passed = True
    credit_details = []
    for s in sessions:
        key = s.get("session_key") or s.get("key") or s.get("name") or ""
        reported_c = float(s.get("credits") or s.get("credits_used") or 0)
        if key in expected_credits:
            exp_c = expected_credits[key]
            diff = abs(reported_c - exp_c)
            ok = diff <= TOLERANCE
            if not ok:
                credit_check_passed = False
            credit_details.append(f"{key}: expected={exp_c:.4f}, got={reported_c:.4f}, diff={diff:.4f}, ok={ok}")
        else:
            credit_details.append(f"{key}: not in ground truth (unrecognized session key)")

    checks.append(check("credit_values_correct", credit_check_passed,
        "; ".join(credit_details)))

    # ─── 8. Gemini = 0 credits (non-Claude rule) ──────────────────────────────
    # If gemini-experiments is in top-3 it shouldn't be (0 credits)
    # The key check: gemini should NOT appear in top 3 (it has 0 credits)
    gemini_absent = "gemini-experiments" not in reported_keys
    checks.append(check("gemini_not_in_top3", gemini_absent,
        f"Gemini (0 Claude credits) correctly excluded from top-3: {gemini_absent}. Reported: {reported_keys}"))

    # ─── 9. Config was saved (--save was used) ────────────────────────────────
    config_path = Path("/root/.claude-usage-config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                cfg = json.load(f)
            plan_saved = cfg.get("plan") == "5x"
            reset_saved = "2026-02-09 14:00" in str(cfg.get("reset_time", ""))
            config_ok = plan_saved and reset_saved
            checks.append(check("config_saved", config_ok,
                f"Config: {cfg}. plan_ok={plan_saved}, reset_ok={reset_saved}"))
        except Exception as e:
            checks.append(check("config_saved", False, f"Config parse error: {e}"))
    else:
        checks.append(check("config_saved", False, "Config file not found at ~/.claude-usage-config.json"))

    # ─── 10. Plan is 5x in report ─────────────────────────────────────────────
    reported_plan = str(report.get("plan", "")).lower()
    plan_ok = "5x" in reported_plan or "5" in reported_plan
    checks.append(check("correct_plan_5x", plan_ok, f"Reported plan: {report.get('plan', 'NOT FOUND')}"))

    # ─── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "file_exists": 1,
        "valid_json": 1,
        "has_sessions_list": 1,
        "exactly_top3": 2,
        "correct_top3_sessions": 2,
        "sessions_sorted_descending": 1,
        "credit_values_correct": 3,
        "gemini_not_in_top3": 2,
        "config_saved": 1,
        "correct_plan_5x": 1,
    }

    total_weight = sum(weights.values())
    score_sum = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = score_sum / total_weight

    all_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()