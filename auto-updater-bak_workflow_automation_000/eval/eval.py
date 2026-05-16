import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    invocation_log = workspace / "mock_bin" / "invocations.log"

    # -----------------------------------------------------------------------
    # Helper: read invocation log
    # -----------------------------------------------------------------------
    log_content = ""
    try:
        log_content = invocation_log.read_text()
    except Exception as e:
        checks.append({
            "name": "invocation_log_readable",
            "passed": False,
            "detail": f"Could not read invocations.log: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 1: clawdbot cron add was called
    # -----------------------------------------------------------------------
    cron_add_called = "CRON_ADD|" in log_content or (
        "CLAWDBOT_INVOKE" in log_content and "cron add" in log_content
    )
    checks.append({
        "name": "cron_add_command_called",
        "passed": cron_add_called,
        "detail": "clawdbot cron add must have been invoked" if not cron_add_called else "clawdbot cron add was invoked"
    })
    if cron_add_called:
        total_score += 0.10

    # Extract the cron add line for detailed flag checking
    cron_add_line = ""
    for line in log_content.splitlines():
        if "CRON_ADD|" in line or ("CLAWDBOT_INVOKE" in line and "cron add" in line):
            cron_add_line = line
            break

    # -----------------------------------------------------------------------
    # CHECK 2: --name "Daily Auto-Update"
    # -----------------------------------------------------------------------
    name_correct = "Daily Auto-Update" in cron_add_line
    checks.append({
        "name": "flag_name_daily_auto_update",
        "passed": name_correct,
        "detail": f"--name 'Daily Auto-Update' required. Found line: {cron_add_line[:200]}"
    })
    if name_correct:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 3: --cron "0 4 * * *"
    # -----------------------------------------------------------------------
    cron_expr_correct = "0 4 * * *" in cron_add_line
    checks.append({
        "name": "flag_cron_expression_0_4",
        "passed": cron_expr_correct,
        "detail": f"--cron '0 4 * * *' required for 4:00 AM daily. Found: {cron_add_line[:200]}"
    })
    if cron_expr_correct:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 4: --session isolated
    # -----------------------------------------------------------------------
    session_isolated = "--session isolated" in cron_add_line or "session isolated" in cron_add_line
    checks.append({
        "name": "flag_session_isolated",
        "passed": session_isolated,
        "detail": f"--session isolated is required (proprietary flag). Found: {cron_add_line[:200]}"
    })
    if session_isolated:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 5: --wake now
    # -----------------------------------------------------------------------
    wake_now = "--wake now" in cron_add_line or "wake now" in cron_add_line
    checks.append({
        "name": "flag_wake_now",
        "passed": wake_now,
        "detail": f"--wake now is required. Found: {cron_add_line[:200]}"
    })
    if wake_now:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 6: --deliver flag present
    # -----------------------------------------------------------------------
    deliver_present = "--deliver" in cron_add_line
    checks.append({
        "name": "flag_deliver_present",
        "passed": deliver_present,
        "detail": f"--deliver flag is required. Found: {cron_add_line[:200]}"
    })
    if deliver_present:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 7: --message flag with update instructions
    # -----------------------------------------------------------------------
    message_present = "--message" in cron_add_line
    # Check the message content contains key concepts
    message_has_update_content = (
        "update" in cron_add_line.lower() and
        "skill" in cron_add_line.lower() and
        "--message" in cron_add_line
    )
    checks.append({
        "name": "flag_message_with_update_instructions",
        "passed": message_has_update_content,
        "detail": f"--message must contain update/skill instructions. Found: {cron_add_line[:300]}"
    })
    if message_has_update_content:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 8: update_summary.txt exists
    # -----------------------------------------------------------------------
    summary_files = list(workspace.rglob("update_summary.txt"))
    summary_exists = len(summary_files) > 0
    summary_path = summary_files[0] if summary_exists else None

    checks.append({
        "name": "update_summary_file_exists",
        "passed": summary_exists,
        "detail": f"update_summary.txt must be created. Found: {summary_path}"
    })
    if summary_exists:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 9: Summary contains the 🔄 emoji (per documented format)
    # -----------------------------------------------------------------------
    summary_content = ""
    if summary_path:
        try:
            summary_content = summary_path.read_text(encoding="utf-8")
        except Exception as e:
            checks.append({
                "name": "update_summary_readable",
                "passed": False,
                "detail": f"Could not read update_summary.txt: {e}"
            })

    emoji_present = "🔄" in summary_content
    checks.append({
        "name": "summary_has_rotating_arrows_emoji",
        "passed": emoji_present,
        "detail": "Summary must contain 🔄 emoji as per documented format"
    })
    if emoji_present:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 10: Summary mentions Clawdbot version update v2026.1.9 -> v2026.1.10
    # -----------------------------------------------------------------------
    clawdbot_version_in_summary = (
        "2026.1.9" in summary_content and
        "2026.1.10" in summary_content
    )
    checks.append({
        "name": "summary_clawdbot_version_update",
        "passed": clawdbot_version_in_summary,
        "detail": "Summary must show Clawdbot updated from v2026.1.9 to v2026.1.10"
    })
    if clawdbot_version_in_summary:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 11: Summary lists the 3 updated skills with correct version arrows
    # -----------------------------------------------------------------------
    # Expected: prd 2.0.3 → 2.0.4, browser 1.2.0 → 1.2.1, nano-banana-pro 3.1.0 → 3.1.2
    updated_skills_correct = all([
        "prd" in summary_content,
        "2.0.3" in summary_content and "2.0.4" in summary_content,
        "browser" in summary_content,
        "1.2.0" in summary_content and "1.2.1" in summary_content,
        "nano-banana-pro" in summary_content,
        "3.1.0" in summary_content and "3.1.2" in summary_content,
    ])
    checks.append({
        "name": "summary_lists_3_updated_skills_with_versions",
        "passed": updated_skills_correct,
        "detail": "Summary must list prd, browser, nano-banana-pro with old→new versions"
    })
    if updated_skills_correct:
        total_score += 0.10

    # -----------------------------------------------------------------------
    # CHECK 12: Summary lists already-current skills (gemini, sag)
    # -----------------------------------------------------------------------
    already_current_correct = (
        "gemini" in summary_content and
        "sag" in summary_content and
        # must be in "already current" section context
        ("Already Current" in summary_content or "already current" in summary_content.lower())
    )
    checks.append({
        "name": "summary_lists_already_current_skills",
        "passed": already_current_correct,
        "detail": "Summary must list gemini and sag as already current with 'Already Current' heading"
    })
    if already_current_correct:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 13: Summary structure matches documented format (section headers)
    # -----------------------------------------------------------------------
    has_clawdbot_section = "**Clawdbot**" in summary_content or "Clawdbot:" in summary_content
    has_skills_updated_section = (
        "**Skills Updated" in summary_content or
        "Skills Updated" in summary_content
    )
    structure_correct = has_clawdbot_section and has_skills_updated_section
    checks.append({
        "name": "summary_has_correct_section_headers",
        "passed": structure_correct,
        "detail": f"Summary must have 'Clawdbot' and 'Skills Updated' sections. clawdbot_section={has_clawdbot_section}, skills_section={has_skills_updated_section}"
    })
    if structure_correct:
        total_score += 0.05

    # -----------------------------------------------------------------------
    # CHECK 14: --tz flag present in cron add command (timezone parameter)
    # -----------------------------------------------------------------------
    tz_present = "--tz" in cron_add_line
    checks.append({
        "name": "flag_tz_present",
        "passed": tz_present,
        "detail": f"--tz flag should be present in cron add command. Line: {cron_add_line[:200]}"
    })
    if tz_present:
        total_score += 0.05

    # Clamp score
    total_score = min(round(total_score, 4), 1.0)

    passed = (
        cron_add_called and
        name_correct and
        cron_expr_correct and
        session_isolated and
        wake_now and
        deliver_present and
        summary_exists and
        updated_skills_correct and
        clawdbot_version_in_summary
    )

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))