#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def find_lifecycle_report(workspace: Path):
    """Find the lifecycle report JSON file, excluding the known distractor."""
    candidates = []
    for f in workspace.rglob("*.json"):
        # Skip known distractor files
        if "old_lifecycle_report" in f.name:
            continue
        if "lifecycle_tracker_partial" in f.name:
            continue
        if "db.json" in f.name or "feature_flags" in f.name:
            continue
        if "grafana_export" in f.name or "openapi_draft" in f.name:
            continue
        if "strategy_spec" in f.name:
            continue
        if "positions_old" in f.name:
            continue
        try:
            data = json.loads(f.read_text())
            if isinstance(data, dict) and "conversationId" in data and "strategyId" in data:
                candidates.append(f)
        except Exception:
            continue
    return candidates

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    passed_all = True

    # ── Check 1: Lifecycle report file exists ──────────────────────────────────
    report_files = find_lifecycle_report(workspace)
    check1_passed = len(report_files) >= 1
    checks.append({
        "name": "lifecycle_report_exists",
        "passed": check1_passed,
        "detail": f"Found {len(report_files)} lifecycle report file(s): {[str(f) for f in report_files]}"
    })
    if not check1_passed:
        passed_all = False

    report = {}
    if check1_passed:
        try:
            report = json.loads(report_files[0].read_text())
        except Exception as e:
            checks.append({
                "name": "lifecycle_report_parseable",
                "passed": False,
                "detail": f"Could not parse lifecycle report: {e}"
            })
            passed_all = False
            print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
            return

    # ── Check 2: conversationId present and non-null ───────────────────────────
    conv_id = report.get("conversationId")
    check2_passed = bool(conv_id) and conv_id != "conv_FAKE_DO_NOT_USE" and conv_id.startswith("conv_")
    checks.append({
        "name": "conversationId_valid",
        "passed": check2_passed,
        "detail": f"conversationId={conv_id!r} (must be non-null, start with 'conv_', not fake)"
    })
    if not check2_passed:
        passed_all = False

    # ── Check 3: strategyId present and non-null ──────────────────────────────
    strat_id = report.get("strategyId")
    check3_passed = bool(strat_id) and strat_id != "strat_FAKE_001" and strat_id.startswith("strat_")
    checks.append({
        "name": "strategyId_valid",
        "passed": check3_passed,
        "detail": f"strategyId={strat_id!r} (must be non-null, start with 'strat_', not fake)"
    })
    if not check3_passed:
        passed_all = False

    # ── Check 4: run_mode is paper (not live) ─────────────────────────────────
    run_mode = report.get("run_mode", "")
    check4_passed = str(run_mode).lower() == "paper"
    checks.append({
        "name": "run_mode_is_paper",
        "passed": check4_passed,
        "detail": f"run_mode={run_mode!r} (spec says paper-only, must be 'paper')"
    })
    if not check4_passed:
        passed_all = False

    # ── Check 5: monitoring_summary is present and non-trivial ────────────────
    monitoring = report.get("monitoring_summary")
    check5_passed = bool(monitoring) and isinstance(monitoring, (str, dict)) and len(str(monitoring)) > 20
    checks.append({
        "name": "monitoring_summary_present",
        "passed": check5_passed,
        "detail": f"monitoring_summary present and non-trivial: {str(monitoring)[:120]!r}"
    })
    if not check5_passed:
        passed_all = False

    # ── Check 6: last_command is a dawn run stop command ─────────────────────
    last_cmd = report.get("last_command", "")
    check6_passed = bool(last_cmd) and "dawn run stop" in str(last_cmd)
    checks.append({
        "name": "last_command_is_stop",
        "passed": check6_passed,
        "detail": f"last_command={last_cmd!r} (must contain 'dawn run stop')"
    })
    if not check6_passed:
        passed_all = False

    # ── Check 7: Dawn state - run actually stopped ────────────────────────────
    # Verify via the mock state files
    check7_passed = False
    check7_detail = "Cannot verify dawn mock state"
    try:
        state_dir = Path("/tmp/dawn_state")
        auth_ok = (state_dir / "auth_status").exists() and \
                  (state_dir / "auth_status").read_text().strip() == "authenticated"

        # Find the conversation ID from state
        state_conv_id = None
        if (state_dir / "conversation_id").exists():
            state_conv_id = (state_dir / "conversation_id").read_text().strip()

        if state_conv_id and conv_id:
            running_file = state_dir / f"conv_{state_conv_id}_running"
            if running_file.exists():
                running_val = running_file.read_text().strip()
                check7_passed = (running_val == "false")
                check7_detail = (
                    f"Dawn state: conv={state_conv_id}, running={running_val!r}. "
                    f"Report conv={conv_id!r}. Auth: {auth_ok}"
                )
            else:
                check7_detail = f"No running state found for conv={state_conv_id}"
        else:
            check7_detail = f"state_conv_id={state_conv_id!r}, report_conv_id={conv_id!r}"
    except Exception as e:
        check7_detail = f"Exception reading dawn state: {e}"

    checks.append({
        "name": "dawn_run_actually_stopped",
        "passed": check7_passed,
        "detail": check7_detail
    })
    if not check7_passed:
        passed_all = False

    # ── Check 8: Rules were approved (state check) ───────────────────────────
    check8_passed = False
    check8_detail = "Cannot verify rules approval state"
    try:
        state_dir = Path("/tmp/dawn_state")
        if state_conv_id:
            rules_file = state_dir / f"conv_{state_conv_id}_rules_approved"
            if rules_file.exists():
                rules_val = rules_file.read_text().strip()
                check8_passed = (rules_val == "true")
                check8_detail = f"rules_approved={rules_val!r} for conv={state_conv_id}"
            else:
                check8_detail = f"No rules_approved state for conv={state_conv_id}"
    except Exception as e:
        check8_detail = f"Exception: {e}"

    checks.append({
        "name": "strategy_rules_were_approved",
        "passed": check8_passed,
        "detail": check8_detail
    })
    if not check8_passed:
        passed_all = False

    # ── Check 9: Code was generated ───────────────────────────────────────────
    check9_passed = False
    check9_detail = "Cannot verify code generation state"
    try:
        state_dir = Path("/tmp/dawn_state")
        if state_conv_id:
            code_file = state_dir / f"conv_{state_conv_id}_code_generated"
            if code_file.exists():
                code_val = code_file.read_text().strip()
                check9_passed = (code_val == "true")
                check9_detail = f"code_generated={code_val!r} for conv={state_conv_id}"
            else:
                check9_detail = f"No code_generated state for conv={state_conv_id}"
    except Exception as e:
        check9_detail = f"Exception: {e}"

    checks.append({
        "name": "strategy_code_was_generated",
        "passed": check9_passed,
        "detail": check9_detail
    })
    if not check9_passed:
        passed_all = False

    # ── Check 10: Budget and hours in report or launch used correct values ────
    # The spec says budget=75, hours=6
    check10_passed = False
    check10_detail = "Cannot verify launch params"
    try:
        state_dir = Path("/tmp/dawn_state")
        if state_conv_id:
            budget_file = state_dir / f"conv_{state_conv_id}_budget"
            hours_file = state_dir / f"conv_{state_conv_id}_hours"
            budget_val = budget_file.read_text().strip() if budget_file.exists() else None
            hours_val = hours_file.read_text().strip() if hours_file.exists() else None
            budget_ok = str(budget_val) == "75"
            hours_ok = str(hours_val) == "6"
            check10_passed = budget_ok and hours_ok
            check10_detail = (
                f"budget={budget_val!r} (expected '75'), hours={hours_val!r} (expected '6')"
            )
    except Exception as e:
        check10_detail = f"Exception: {e}"

    checks.append({
        "name": "launch_params_correct_budget75_hours6",
        "passed": check10_passed,
        "detail": check10_detail
    })
    if not check10_passed:
        passed_all = False

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    print(json.dumps({
        "passed": passed_all,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()