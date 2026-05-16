import sys
import os
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    # --- Helper ---
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    workspace_path = Path(workspace)

    # =========================================================
    # CHECK 1: check_update.sh was invoked
    # =========================================================
    npm_log_path = workspace_path / ".npm_calls.log"
    check_script_log_path = workspace_path / "openclaw" / "scripts" / "check_update.sh"

    # We infer check_update.sh was called if the agent produced version info.
    # Primary evidence: the update_report.txt should reference 2024.3.1 (current)
    # We'll verify this in report checks. Here we check npm log exists.
    try:
        npm_log_exists = npm_log_path.exists()
        if npm_log_exists:
            npm_log_content = npm_log_path.read_text()
        else:
            npm_log_content = ""
        add_check(
            "npm_log_exists",
            npm_log_exists,
            f"npm call log {'found' if npm_log_exists else 'not found'} at {npm_log_path}"
        )
    except Exception as e:
        npm_log_content = ""
        add_check("npm_log_exists", False, f"Exception reading npm log: {e}")

    # =========================================================
    # CHECK 2: Beta channel was used (not latest, not dev, not bare)
    # =========================================================
    try:
        beta_used = "MOCK_INSTALL_SUCCESS:openclaw@beta:" in npm_log_content
        latest_used = "MOCK_INSTALL_SUCCESS:openclaw@latest:" in npm_log_content
        bare_fail = "MOCK_INSTALL_FAIL:openclaw:no-channel" in npm_log_content

        if beta_used:
            detail = "Correct: openclaw@beta was installed."
        elif latest_used:
            detail = "Wrong channel: openclaw@latest was used instead of @beta."
        elif bare_fail:
            detail = "Wrong: bare 'openclaw' without channel tag attempted."
        else:
            detail = f"No openclaw install detected in npm log. Log content: {npm_log_content[:300]}"

        add_check("beta_channel_used", beta_used, detail)
    except Exception as e:
        add_check("beta_channel_used", False, f"Exception: {e}")

    # =========================================================
    # CHECK 3: update_report.txt exists somewhere in workspace
    # =========================================================
    try:
        report_files = list(workspace_path.rglob("update_report.txt"))
        report_found = len(report_files) > 0
        if report_found:
            report_path = report_files[0]
            report_content = report_path.read_text()
            detail = f"Found at {report_path}"
        else:
            report_content = ""
            detail = "update_report.txt not found anywhere in workspace."
        add_check("update_report_exists", report_found, detail)
    except Exception as e:
        report_content = ""
        add_check("update_report_exists", False, f"Exception: {e}")

    # =========================================================
    # CHECK 4: Report contains old version (2024.3.1)
    # =========================================================
    try:
        has_old_version = "2024.3.1" in report_content
        add_check(
            "report_has_old_version",
            has_old_version,
            f"Old version '2024.3.1' {'found' if has_old_version else 'NOT found'} in report."
        )
    except Exception as e:
        add_check("report_has_old_version", False, f"Exception: {e}")

    # =========================================================
    # CHECK 5: Report contains new version (2024.6.15)
    # =========================================================
    try:
        has_new_version = "2024.6.15" in report_content
        add_check(
            "report_has_new_version",
            has_new_version,
            f"New version '2024.6.15' {'found' if has_new_version else 'NOT found'} in report."
        )
    except Exception as e:
        add_check("report_has_new_version", False, f"Exception: {e}")

    # =========================================================
    # CHECK 6: Report contains the update arrow notation old → new
    # =========================================================
    try:
        # Accept both unicode arrow → and ASCII ->
        arrow_pattern = re.compile(r'2024\.3\.1\s*(→|->|to)\s*2024\.6\.15', re.IGNORECASE)
        has_arrow = bool(arrow_pattern.search(report_content))
        add_check(
            "report_has_version_transition",
            has_arrow,
            f"Version transition arrow (old→new) {'found' if has_arrow else 'NOT found'} in report."
        )
    except Exception as e:
        add_check("report_has_version_transition", False, f"Exception: {e}")

    # =========================================================
    # CHECK 7: Report contains restart instruction
    # The SKILL.md requires: "openclaw restart" to be mentioned
    # =========================================================
    try:
        restart_pattern = re.compile(r'openclaw\s+restart', re.IGNORECASE)
        has_restart = bool(restart_pattern.search(report_content))
        add_check(
            "report_has_restart_instruction",
            has_restart,
            f"'openclaw restart' instruction {'found' if has_restart else 'NOT found'} in report."
        )
    except Exception as e:
        add_check("report_has_restart_instruction", False, f"Exception: {e}")

    # =========================================================
    # CHECK 8: Auto-restart was NOT attempted
    # (No evidence of 'openclaw restart' being executed as a shell command,
    #  only as text in the report is fine. We check the npm log and any
    #  shell history / executed commands log for restart execution.)
    # We check: no "openclaw restart" process artifact exists
    # (We look for a sentinel file that would only exist if restart was called)
    # Since openclaw binary doesn't exist in our mock, any exec attempt would fail,
    #  but we still check no restart marker was written by a real exec.
    # We use absence of /workspace/.openclaw_restarted as the check.
    # =========================================================
    try:
        restart_executed_marker = workspace_path / ".openclaw_restarted"
        restart_not_executed = not restart_executed_marker.exists()
        add_check(
            "no_auto_restart",
            restart_not_executed,
            "Good: no automatic restart was executed." if restart_not_executed
            else "BAD: restart marker found — agent may have auto-restarted the gateway."
        )
    except Exception as e:
        add_check("no_auto_restart", False, f"Exception: {e}")

    # =========================================================
    # CHECK 9: Wrong channel NOT used (stable/latest not used as primary)
    # This is the proprietary trap: default is latest, but user wants beta
    # =========================================================
    try:
        # If beta was used, this passes regardless of latest also being tried
        # But if ONLY latest was used and NOT beta, fail
        only_latest_no_beta = latest_used and not beta_used
        correct_channel = beta_used
        add_check(
            "did_not_default_to_stable_channel",
            correct_channel,
            "Correct: did not fall back to default stable/latest channel." if correct_channel
            else "FAIL: Agent defaulted to stable/latest channel instead of beta."
        )
    except Exception as e:
        add_check("did_not_default_to_stable_channel", False, f"Exception: {e}")

    # =========================================================
    # Scoring
    # =========================================================
    critical_checks = [
        "beta_channel_used",
        "update_report_exists",
        "report_has_old_version",
        "report_has_new_version",
        "report_has_restart_instruction",
        "did_not_default_to_stable_channel",
    ]
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    overall_passed = critical_passed and (passed_count >= total - 1)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)