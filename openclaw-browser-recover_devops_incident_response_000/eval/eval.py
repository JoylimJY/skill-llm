import json
import sys
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0
    max_score = 7

    MOCK_BIN = Path("/workspace/mock_bin")
    STATE_FILE = Path("/tmp/openclaw_gateway_state")
    RESTART_COUNT_FILE = Path("/tmp/openclaw_restart_count")
    STOP_START_FILE = Path("/tmp/openclaw_stop_start_sequence")
    ACTION_LOG = Path("/tmp/openclaw_action_log")
    SS_CALL_LOG = Path("/tmp/ss_call_log")

    # -------------------------------------------------------
    # CHECK 1: recovery_report.json exists somewhere in workspace
    # -------------------------------------------------------
    report_files = list(workspace.rglob("recovery_report.json"))
    check1_passed = len(report_files) > 0
    checks.append({
        "name": "recovery_report.json_exists",
        "passed": check1_passed,
        "detail": f"Found {len(report_files)} recovery_report.json file(s): {[str(f) for f in report_files]}"
    })
    if check1_passed:
        total_score += 1.0

    # -------------------------------------------------------
    # CHECK 2: Report is valid JSON and has required top-level fields
    # -------------------------------------------------------
    report_data = None
    check2_passed = False
    check2_detail = "File not found or invalid JSON"
    if check1_passed:
        try:
            report_data = json.loads(report_files[0].read_text())
            required_keys = {"port_diagnosis", "action_taken", "user_message"}
            missing = required_keys - set(report_data.keys())
            if not missing:
                check2_passed = True
                check2_detail = f"All required keys present: {sorted(required_keys)}"
            else:
                check2_detail = f"Missing keys: {missing}"
        except Exception as e:
            check2_detail = f"Exception: {e}"
    checks.append({
        "name": "report_valid_json_with_required_keys",
        "passed": check2_passed,
        "detail": check2_detail
    })
    if check2_passed:
        total_score += 1.0

    # -------------------------------------------------------
    # CHECK 3: Port diagnosis is correct
    # port 18789: UP, port 18791: DOWN, port 9222: UP
    # Agent must correctly identify 18791 was not listening (gateway browser-control crashed)
    # and 9222 WAS listening (Chrome running)
    # -------------------------------------------------------
    check3_passed = False
    check3_detail = "Report not parsed"
    if report_data:
        try:
            diag = str(report_data.get("port_diagnosis", "")).lower()
            # Must mention 18791 as down/not listening/crashed/missing
            port_18791_issue = bool(re.search(r'18791', diag) and re.search(r'(down|not.?listen|crash|missing|unavail|dead|absent|off)', diag))
            # Must mention 9222 as up/listening/running
            port_9222_ok = bool(re.search(r'9222', diag) and re.search(r'(up|listen|running|active|present|ok|avail)', diag))
            if port_18791_issue and port_9222_ok:
                check3_passed = True
                check3_detail = "Correctly identified 18791 as down and 9222 as up"
            else:
                check3_detail = (
                    f"port_18791_issue={port_18791_issue} (18791 mentioned as down/crashed), "
                    f"port_9222_ok={port_9222_ok} (9222 mentioned as up). diag snippet: {diag[:300]}"
                )
        except Exception as e:
            check3_detail = f"Exception: {e}"
    checks.append({
        "name": "port_diagnosis_correct_18791_down_9222_up",
        "passed": check3_passed,
        "detail": check3_detail
    })
    if check3_passed:
        total_score += 1.5

    # -------------------------------------------------------
    # CHECK 4: Agent ran exactly ONE gateway restart (not zero, not >1, and not stop+start)
    # -------------------------------------------------------
    check4_passed = False
    check4_detail = "Could not verify restart behavior"
    try:
        restart_count = int(RESTART_COUNT_FILE.read_text().strip()) if RESTART_COUNT_FILE.exists() else 0
        stop_start_content = STOP_START_FILE.read_text() if STOP_START_FILE.exists() else ""
        used_stop_start = ("stop" in stop_start_content and "start" in stop_start_content)

        if restart_count == 1 and not used_stop_start:
            check4_passed = True
            check4_detail = f"Exactly 1 restart, no stop+start sequence used. stop_start_log='{stop_start_content.strip()}'"
        elif restart_count == 0:
            check4_detail = "No gateway restart was performed (required by runbook after port check)"
        elif restart_count > 1:
            check4_detail = f"Too many restarts: {restart_count} (runbook says only one)"
        elif used_stop_start:
            check4_detail = f"Used stop+start sequence instead of restart. restart_count={restart_count}, stop_start_log='{stop_start_content.strip()}'"
    except Exception as e:
        check4_detail = f"Exception reading state files: {e}"
    checks.append({
        "name": "exactly_one_restart_no_stop_start_abuse",
        "passed": check4_passed,
        "detail": check4_detail
    })
    if check4_passed:
        total_score += 1.5

    # -------------------------------------------------------
    # CHECK 5: action_taken field correctly names 'gateway restart' (not stop/start, not retry browser)
    # -------------------------------------------------------
    check5_passed = False
    check5_detail = "Report not parsed"
    if report_data:
        try:
            action = str(report_data.get("action_taken", "")).lower()
            mentions_restart = bool(re.search(r'gateway.{0,15}restart|restart.{0,15}gateway', action))
            no_stop_start = not bool(re.search(r'\bstop\b.*\bstart\b|\bstart\b.*\bstop\b', action))
            no_browser_retry = not bool(re.search(r'retry.{0,20}browser|browser.{0,20}retry', action))
            if mentions_restart and no_stop_start and no_browser_retry:
                check5_passed = True
                check5_detail = f"action_taken correctly describes gateway restart only. Value: {action[:200]}"
            else:
                check5_detail = (
                    f"mentions_restart={mentions_restart}, no_stop_start={no_stop_start}, "
                    f"no_browser_retry={no_browser_retry}. action='{action[:200]}'"
                )
        except Exception as e:
            check5_detail = f"Exception: {e}"
    checks.append({
        "name": "action_taken_describes_gateway_restart_only",
        "passed": check5_passed,
        "detail": check5_detail
    })
    if check5_passed:
        total_score += 0.5

    # -------------------------------------------------------
    # CHECK 6: user_message matches the skill's template for browser timeout scenario
    # Must tell user to run 'openclaw gateway restart' (or indicate gateway/browser-control issue)
    # NOT the Chrome message (since 9222 is UP) and NOT the connection closed message
    # -------------------------------------------------------
    check6_passed = False
    check6_detail = "Report not parsed"
    if report_data:
        try:
            msg = str(report_data.get("user_message", "")).lower()
            # The correct template: "browser-control 卡住了：请执行 openclaw gateway restart"
            # or English equivalent indicating gateway restart needed
            correct_signal = bool(
                re.search(r'openclaw\s+gateway\s+restart', msg) or
                re.search(r'gateway\s+restart', msg) or
                re.search(r'browser.control.{0,30}(stuck|hang|timeout|restart|卡住)', msg) or
                re.search(r'(restart|重启).{0,30}gateway', msg)
            )
            # Must NOT say "open Chrome with 9222" (wrong - 9222 is already up)
            wrong_chrome_msg = bool(re.search(r'(open|launch|start).{0,20}chrome.{0,20}9222|9222.{0,20}(open|launch|start)', msg))
            # Must NOT say "fully exit Chrome" (that's for connection-closed scenario)
            wrong_exit_chrome = bool(re.search(r'(exit|quit|close).{0,20}chrome|chrome.{0,20}(exit|quit|close)', msg))

            if correct_signal and not wrong_chrome_msg:
                check6_passed = True
                check6_detail = f"user_message correctly points to gateway restart. wrong_exit_chrome={wrong_exit_chrome}. msg: {msg[:300]}"
            else:
                check6_detail = (
                    f"correct_signal={correct_signal}, wrong_chrome_msg={wrong_chrome_msg}. "
                    f"msg='{msg[:300]}'"
                )
        except Exception as e:
            check6_detail = f"Exception: {e}"
    checks.append({
        "name": "user_message_correct_gateway_template",
        "passed": check6_passed,
        "detail": check6_detail
    })
    if check6_passed:
        total_score += 1.0

    # -------------------------------------------------------
    # CHECK 7: Gateway ended in healthy state after recovery
    # -------------------------------------------------------
    check7_passed = False
    check7_detail = "State file not found"
    try:
        final_state = STATE_FILE.read_text().strip() if STATE_FILE.exists() else "unknown"
        if final_state == "healthy":
            check7_passed = True
            check7_detail = f"Gateway state is 'healthy' after recovery"
        else:
            check7_detail = f"Gateway state is '{final_state}' (expected 'healthy')"
    except Exception as e:
        check7_detail = f"Exception: {e}"
    checks.append({
        "name": "gateway_state_healthy_after_recovery",
        "passed": check7_passed,
        "detail": check7_detail
    })
    if check7_passed:
        total_score += 0.5

    final_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)