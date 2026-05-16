import sys
import json
import subprocess
import time
from pathlib import Path

def run_tmux(args):
    """Run a tmux command and return stdout."""
    try:
        result = subprocess.run(
            ["tmux"] + args,
            capture_output=True, text=True, timeout=10
        )
        return result.stdout, result.returncode
    except Exception as e:
        return "", -1

def capture_pane(target, scrollback=400):
    """Capture pane content."""
    stdout, rc = run_tmux(["capture-pane", "-p", "-J", "-t", target, "-S", f"-{scrollback}"])
    return stdout

def find_claude_pane(session_name):
    """Find the claude pane in a session using the documented method."""
    stdout, rc = run_tmux([
        "list-panes", "-a", "-F",
        "#{session_name}:#{window_index}.#{pane_index} #{pane_title}"
    ])
    lines = stdout.strip().split("\n")
    for line in lines:
        if line.startswith(session_name + ":") and "claude" in line.lower():
            target = line.split(" ")[0]
            return target
    return None

def check_report_file(workspace):
    """Find and parse the session_report.json file."""
    candidates = list(Path(workspace).rglob("session_report.json"))
    if not candidates:
        return None, "session_report.json not found anywhere in workspace"
    # Use the most recently modified one
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0]) as f:
            data = json.load(f)
        return data, str(candidates[0])
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in {candidates[0]}: {e}"
    except Exception as e:
        return None, f"Error reading {candidates[0]}: {e}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # =========================================================
    # CHECK 1: payments session - claude pane exists and has content
    # =========================================================
    payments_target = find_claude_pane("payments")
    payments_pane_found = payments_target is not None
    checks.append({
        "name": "payments_claude_pane_located",
        "passed": payments_pane_found,
        "detail": f"Found target: {payments_target}" if payments_pane_found else "No pane titled 'claude' found in payments session"
    })
    if payments_pane_found:
        total_score += 0.08

    # =========================================================
    # CHECK 2: fraud session - claude pane exists
    # =========================================================
    fraud_target = find_claude_pane("fraud")
    fraud_pane_found = fraud_target is not None
    checks.append({
        "name": "fraud_claude_pane_located",
        "passed": fraud_pane_found,
        "detail": f"Found target: {fraud_target}" if fraud_pane_found else "No pane titled 'claude' found in fraud session"
    })
    if fraud_pane_found:
        total_score += 0.08

    # =========================================================
    # CHECK 3: payments pane has ❯/⏺ exchange markers (agent read it)
    # We verify this by checking the pane actually has the history
    # =========================================================
    payments_has_exchange = False
    payments_content = ""
    if payments_pane_found:
        payments_content = capture_pane(payments_target, 400)
        has_user_marker = "❯" in payments_content
        has_claude_marker = "⏺" in payments_content
        payments_has_exchange = has_user_marker and has_claude_marker

    checks.append({
        "name": "payments_pane_has_exchange_markers",
        "passed": payments_has_exchange,
        "detail": f"❯ marker: {'found' if '❯' in payments_content else 'missing'}, ⏺ marker: {'found' if '⏺' in payments_content else 'missing'}"
    })
    if payments_has_exchange:
        total_score += 0.07

    # =========================================================
    # CHECK 4: fraud pane has ❯/⏺ exchange markers
    # =========================================================
    fraud_has_exchange = False
    fraud_content = ""
    if fraud_pane_found:
        fraud_content = capture_pane(fraud_target, 400)
        fraud_has_exchange = "❯" in fraud_content and "⏺" in fraud_content

    checks.append({
        "name": "fraud_pane_has_exchange_markers",
        "passed": fraud_has_exchange,
        "detail": f"❯ marker: {'found' if '❯' in fraud_content else 'missing'}, ⏺ marker: {'found' if '⏺' in fraud_content else 'missing'}"
    })
    if fraud_has_exchange:
        total_score += 0.07

    # =========================================================
    # CHECK 5: A follow-up prompt was sent to payments session
    # The agent should have sent a clarifying question per the task
    # We look for a new ❯ block AFTER the pre-seeded history
    # The pre-seeded history ends with "service layer handles transient failures"
    # Any new ❯ line after that indicates agent sent a prompt
    # =========================================================
    payments_prompt_sent = False
    new_exchange_in_payments = ""
    if payments_pane_found:
        content = capture_pane(payments_target, 400)
        lines = content.split("\n")
        # Find the pre-seeded last ⏺ block
        last_seeded_marker = "service layer"
        seeded_idx = -1
        for i, line in enumerate(lines):
            if "service layer" in line or "retry_limit" in line:
                seeded_idx = i
        # Check for any ❯ AFTER the seeded content
        if seeded_idx >= 0:
            post_seeded = "\n".join(lines[seeded_idx:])
            if post_seeded.count("❯") >= 1:
                payments_prompt_sent = True
                # Extract the new user prompt
                for line in lines[seeded_idx:]:
                    if "❯" in line:
                        new_exchange_in_payments = line.strip()
                        break
        else:
            # If seeded content not found (maybe cleared), just check for any ❯
            if content.count("❯") >= 1:
                payments_prompt_sent = True

    checks.append({
        "name": "new_prompt_sent_to_payments_session",
        "passed": payments_prompt_sent,
        "detail": f"New prompt detected after seeded history: '{new_exchange_in_payments}'" if payments_prompt_sent else "No new ❯ prompt found after pre-seeded content in payments pane"
    })
    if payments_prompt_sent:
        total_score += 0.12

    # =========================================================
    # CHECK 6: /compact was triggered in payments session
    # =========================================================
    payments_compact = False
    if payments_pane_found:
        content = capture_pane(payments_target, 400)
        # Look for /compact being sent OR the compact response
        payments_compact = "/compact" in content or "Compacting conversation" in content or "tokens" in content.lower()

    checks.append({
        "name": "compact_triggered_in_payments",
        "passed": payments_compact,
        "detail": "Found /compact evidence in payments pane" if payments_compact else "No /compact command or response found in payments pane"
    })
    if payments_compact:
        total_score += 0.12

    # =========================================================
    # CHECK 7: /compact was triggered in fraud session
    # =========================================================
    fraud_compact = False
    if fraud_pane_found:
        content = capture_pane(fraud_target, 400)
        fraud_compact = "/compact" in content or "Compacting conversation" in content or "tokens" in content.lower()

    checks.append({
        "name": "compact_triggered_in_fraud",
        "passed": fraud_compact,
        "detail": "Found /compact evidence in fraud pane" if fraud_compact else "No /compact command or response found in fraud pane"
    })
    if fraud_compact:
        total_score += 0.12

    # =========================================================
    # CHECK 8: session_report.json exists and is valid JSON
    # =========================================================
    report_data, report_detail = check_report_file(workspace)
    report_exists = report_data is not None
    checks.append({
        "name": "session_report_json_exists_and_valid",
        "passed": report_exists,
        "detail": report_detail
    })
    if report_exists:
        total_score += 0.08

    # =========================================================
    # CHECK 9: session_report.json contains both session names
    # =========================================================
    report_has_sessions = False
    if report_data:
        report_str = json.dumps(report_data).lower()
        has_payments = "payments" in report_str
        has_fraud = "fraud" in report_str
        report_has_sessions = has_payments and has_fraud

    checks.append({
        "name": "report_contains_both_sessions",
        "passed": report_has_sessions,
        "detail": f"Report content keys/values mention 'payments': {report_data is not None and 'payments' in json.dumps(report_data).lower()}, 'fraud': {report_data is not None and 'fraud' in json.dumps(report_data).lower()}"
    })
    if report_has_sessions:
        total_score += 0.08

    # =========================================================
    # CHECK 10: session_report.json captures the ❯/⏺ exchange content
    # from both sessions (agent actually parsed the markers)
    # =========================================================
    report_has_exchange_content = False
    if report_data:
        report_str = json.dumps(report_data)
        # The seeded content has specific phrases from the fake claude
        # Check for exchange content - partial matches acceptable
        has_payment_content = any(phrase in report_str for phrase in [
            "payment handler", "PaymentHandler", "retry", "idempotency",
            "service level", "handler level", "retry_limit"
        ])
        has_fraud_content = any(phrase in report_str for phrase in [
            "fraud", "Score", "velocity", "risk", "BLOCK", "ALLOW", "REVIEW",
            "thresholds", "model"
        ])
        # At least one session's exchange content must be captured
        report_has_exchange_content = has_payment_content or has_fraud_content

    checks.append({
        "name": "report_captures_exchange_content_from_sessions",
        "passed": report_has_exchange_content,
        "detail": "Report contains specific exchange content parsed from ❯/⏺ markers" if report_has_exchange_content else "Report does not contain parsed exchange content from either session"
    })
    if report_has_exchange_content:
        total_score += 0.10

    # =========================================================
    # CHECK 11: report contains compact confirmation messages
    # =========================================================
    report_has_compact_confirmation = False
    if report_data:
        report_str = json.dumps(report_data).lower()
        report_has_compact_confirmation = (
            "compact" in report_str or
            "triggered" in report_str or
            "memory" in report_str or
            "compacted" in report_str
        )

    checks.append({
        "name": "report_contains_compact_confirmation",
        "passed": report_has_compact_confirmation,
        "detail": "Report mentions /compact action" if report_has_compact_confirmation else "Report does not mention /compact action"
    })
    if report_has_compact_confirmation:
        total_score += 0.08

    # =========================================================
    # CHECK 12: Correct pane targets used (window 0, pane 0 for both sessions)
    # The claude pane should be session:0.0 (or the one with lowest window/pane index)
    # Verify the agent did not accidentally use the distractor shell panes
    # =========================================================
    correct_pane_used = False
    if payments_pane_found and fraud_pane_found:
        # Both should resolve to window 0, pane 0 per the SKILL.md tie-breaking rule
        payments_correct = payments_target == "payments:0.0"
        fraud_correct = fraud_target == "fraud:0.0"
        correct_pane_used = payments_correct and fraud_correct

    checks.append({
        "name": "correct_lowest_index_pane_selected",
        "passed": correct_pane_used,
        "detail": f"payments target: {payments_target} (expected payments:0.0), fraud target: {fraud_target} (expected fraud:0.0)"
    })
    if correct_pane_used:
        total_score += 0.00  # Bonus validation, score already counted in pane_found checks

    # Final score normalization
    total_score = min(1.0, total_score)
    passed = total_score >= 0.65

    output = {
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()