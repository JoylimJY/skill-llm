#!/usr/bin/env python3
"""
Evaluation script for the claude-tmux skill task.
Checks that session_report.txt was created with correct content.
"""
import sys
import json
import re
from pathlib import Path

def find_report(workspace: Path) -> Path | None:
    matches = list(workspace.rglob("session_report.txt"))
    if matches:
        return matches[0]
    return None

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    passed_all = True

    # -----------------------------------------------------------------------
    # 1. File existence
    # -----------------------------------------------------------------------
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "session_report.txt exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File not found anywhere in workspace"
    })
    if not file_exists:
        passed_all = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # -----------------------------------------------------------------------
    # 2. Correct pane target: must reference phoenix-api session, NOT staging-db
    #    Format must be phoenix-api:<window>.<pane>  e.g. phoenix-api:0.0
    # -----------------------------------------------------------------------
    target_pattern = re.search(r'phoenix-api:\d+\.\d+', content)
    correct_session = target_pattern is not None
    # Also check it does NOT say staging-db as the target
    wrong_session = 'staging-db:' in content and not correct_session
    checks.append({
        "name": "Target pane identifies phoenix-api session with window.pane format",
        "passed": correct_session,
        "detail": (
            f"Found target: {target_pattern.group(0)}" if correct_session
            else f"No 'phoenix-api:<window>.<pane>' pattern found in report. Content snippet: {content[:300]}"
        )
    })
    if not correct_session:
        passed_all = False

    # -----------------------------------------------------------------------
    # 3. Last exchange captured: must include both ❯ and ⏺ lines
    #    The correct last exchange is about review_handler.py security issues
    # -----------------------------------------------------------------------
    has_user_marker = '❯' in content
    has_ai_marker = '⏺' in content
    has_last_exchange_user = 'review_handler.py' in content or 'security issues' in content.lower() or 'Review the review_handler' in content
    has_last_exchange_ai = 'jwt_required' in content or 'authentication' in content.lower() or 'unauthenticated' in content.lower() or 'denial-of-service' in content.lower()

    checks.append({
        "name": "Report contains ❯ user marker from captured exchange",
        "passed": has_user_marker,
        "detail": "❯ marker found in report" if has_user_marker else "Missing ❯ user prompt marker"
    })
    checks.append({
        "name": "Report contains ⏺ AI reply marker from captured exchange",
        "passed": has_ai_marker,
        "detail": "⏺ marker found in report" if has_ai_marker else "Missing ⏺ AI reply marker"
    })
    checks.append({
        "name": "Last exchange is specifically about review_handler.py security (correct last exchange)",
        "passed": has_last_exchange_user,
        "detail": (
            "Correct last exchange found (review_handler.py security)" if has_last_exchange_user
            else "Did not find evidence of the correct last exchange about review_handler.py security. "
                 "Agent may have captured wrong exchange or used wrong session."
        )
    })
    checks.append({
        "name": "Last AI reply content references authentication/security findings",
        "passed": has_last_exchange_ai,
        "detail": (
            "AI reply content correct (mentions auth/dos issues)" if has_last_exchange_ai
            else "Missing expected content from the last AI reply (jwt_required / authentication / denial-of-service)"
        )
    })
    if not (has_user_marker and has_ai_marker and has_last_exchange_user and has_last_exchange_ai):
        passed_all = False

    # -----------------------------------------------------------------------
    # 4. New response captured: answer to JWT risks question
    #    The mock responder outputs content about SECRET_KEY, revocation, RS256
    # -----------------------------------------------------------------------
    jwt_response_keywords = [
        ('SECRET_KEY hardcoded', re.search(r'SECRET_KEY|hardcoded|environment variable', content, re.IGNORECASE) is not None),
        ('token revocation', re.search(r'revoc|revoke|invalidat', content, re.IGNORECASE) is not None),
        ('RS256 or algorithm concern', re.search(r'RS256|HS256|symmetric|algorithm|forge', content, re.IGNORECASE) is not None),
    ]
    for kw_name, kw_found in jwt_response_keywords:
        checks.append({
            "name": f"New response captures JWT risk: {kw_name}",
            "passed": kw_found,
            "detail": f"Keyword evidence for '{kw_name}' {'found' if kw_found else 'NOT found'} in report"
        })
        if not kw_found:
            passed_all = False

    # -----------------------------------------------------------------------
    # 5. /compact confirmation present
    # -----------------------------------------------------------------------
    compact_confirmed = bool(
        re.search(r'/compact|compact|compac|memory optim|Triggered|compacting', content, re.IGNORECASE)
    )
    checks.append({
        "name": "Report confirms /compact was triggered",
        "passed": compact_confirmed,
        "detail": (
            "Compact confirmation found in report" if compact_confirmed
            else "No mention of /compact being triggered. Agent may have skipped step 4."
        )
    })
    if not compact_confirmed:
        passed_all = False

    # -----------------------------------------------------------------------
    # 6. Agent must NOT have confused staging-db with phoenix-api
    # -----------------------------------------------------------------------
    # If the report mentions the staging-db exchange ("database indexes") as the
    # last exchange, that's a session-confusion error.
    staging_leak = bool(re.search(r'idx_user_id|idx_created_at|staging.*database.*index|Check database indexes', content, re.IGNORECASE))
    no_session_confusion = not staging_leak
    checks.append({
        "name": "Agent did not confuse staging-db session with phoenix-api",
        "passed": no_session_confusion,
        "detail": (
            "No cross-session confusion detected" if no_session_confusion
            else "Report appears to contain content from 'staging-db' session (database indexes), indicating session confusion."
        )
    })
    if not no_session_confusion:
        passed_all = False

    # -----------------------------------------------------------------------
    # Score calculation
    # -----------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace argument provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])