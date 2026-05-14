#!/usr/bin/env python3
"""
Evaluation script for the Context Sentinel task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score = 4


def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


# ── Check 1: sentinel_report.txt exists ──────────────────────────────────────
try:
    candidates = list(workspace.rglob("sentinel_report.txt"))
    if candidates:
        report_path = candidates[0]
        report_content = report_path.read_text().strip()
        total_score += check(
            "sentinel_report_exists",
            True,
            f"Found sentinel_report.txt at {report_path}"
        )
    else:
        report_content = ""
        total_score += check(
            "sentinel_report_exists",
            False,
            "sentinel_report.txt not found anywhere in workspace"
        )
except Exception as e:
    report_content = ""
    total_score += check("sentinel_report_exists", False, f"Exception: {e}")

# ── Check 2: Report contains raw script output (SWITCH_TO:gemini-2.5-pro) ────
try:
    # The script outputs SWITCH_TO:gemini-2.5-pro given opus-4.5 at 85%
    expected_output = "SWITCH_TO:gemini-2.5-pro"
    has_output = expected_output in report_content
    total_score += check(
        "report_contains_correct_switch_command",
        has_output,
        f"Expected '{expected_output}' in sentinel_report.txt. "
        f"File content (first 500 chars): {report_content[:500]!r}"
    )
except Exception as e:
    total_score += check(
        "report_contains_correct_switch_command",
        False,
        f"Exception reading report: {e}"
    )

# ── Check 3: session_status was called with the correct model ID ─────────────
try:
    session_log = workspace / "agent" / "logs" / "session_status_calls.log"
    if session_log.exists():
        log_content = session_log.read_text()
        # Must contain the exact model ID: gemini-2.5-pro (not gemini-pro, not gemini-2.5, etc.)
        correct_call = "model=gemini-2.5-pro" in log_content
        # Must NOT have wrong model IDs substituted
        wrong_models = ["model=gemini-pro", "model=gemini-2.5 ", "model=opus-4.5", "model=opus-4.6"]
        has_wrong = any(w in log_content for w in wrong_models)

        if correct_call and not has_wrong:
            total_score += check(
                "session_status_called_with_correct_model",
                True,
                f"session_status was called with model=gemini-2.5-pro correctly."
            )
        elif correct_call and has_wrong:
            total_score += check(
                "session_status_called_with_correct_model",
                False,
                f"session_status was called with gemini-2.5-pro but ALSO with wrong model IDs: {log_content[:300]!r}"
            )
        else:
            total_score += check(
                "session_status_called_with_correct_model",
                False,
                f"session_status not called with model=gemini-2.5-pro. Log: {log_content[:300]!r}"
            )
    else:
        # Also check if session_state.json was updated (alternative evidence)
        state_file = workspace / "session_state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            switched = state.get("switched_to", "")
            total_score += check(
                "session_status_called_with_correct_model",
                switched == "gemini-2.5-pro",
                f"No session_status log found, but session_state.json switched_to={switched!r} "
                f"(expected 'gemini-2.5-pro')"
            )
        else:
            total_score += check(
                "session_status_called_with_correct_model",
                False,
                "Neither session_status_calls.log nor updated session_state.json found."
            )
except Exception as e:
    total_score += check(
        "session_status_called_with_correct_model",
        False,
        f"Exception: {e}"
    )

# ── Check 4: No HANDOFF_NOW or STATUS_OK misclassification ───────────────────
try:
    # The agent must NOT have written handoff_request.txt (that's for HANDOFF_NOW, not SWITCH_TO)
    handoff_candidates = list(workspace.rglob("handoff_request.txt"))
    # Also check sentinel_report.txt doesn't claim HANDOFF_NOW or STATUS_OK as the action
    misclassified = False
    misclassification_detail = ""

    if handoff_candidates:
        misclassified = True
        misclassification_detail = (
            f"handoff_request.txt was created at {handoff_candidates}, but the session "
            f"state (opus-4.5 at 85%) requires SWITCH_TO:gemini-2.5-pro, not HANDOFF_NOW."
        )

    if not misclassified and report_content:
        # Ensure report doesn't incorrectly assert HANDOFF_NOW or STATUS_OK as taken action
        # (having them in context as "rejected" options is OK, but "action taken: HANDOFF_NOW" is not)
        action_line_match = re.search(
            r"(?i)(action[_\s]*taken|executed|performed|result)[:\s]+([A-Z_]+(?::[a-z0-9.\-]+)?)",
            report_content
        )
        if action_line_match:
            stated_action = action_line_match.group(2).strip()
            if stated_action.upper() in ("HANDOFF_NOW", "STATUS_OK"):
                misclassified = True
                misclassification_detail = (
                    f"Report states action taken as '{stated_action}', which is incorrect "
                    f"for opus-4.5 at 85% context."
                )

    total_score += check(
        "correct_action_classification_no_misclassification",
        not misclassified,
        misclassification_detail if misclassified else
        "No misclassification detected (handoff_request.txt absent, action correctly identified)."
    )
except Exception as e:
    total_score += check(
        "correct_action_classification_no_misclassification",
        False,
        f"Exception: {e}"
    )

# ── Final result ─────────────────────────────────────────────────────────────
passed = total_score >= 3.0  # Must pass at least 3 of 4 checks
score_normalized = round(total_score / max_score, 4)

result = {
    "passed": passed,
    "score": score_normalized,
    "checks": checks
}
print(json.dumps(result, indent=2))