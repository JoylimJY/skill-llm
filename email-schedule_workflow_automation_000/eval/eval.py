#!/usr/bin/env python3
"""
Evaluation script for the email-schedule task.
Checks:
1. The agent produced the required output file (email_schedule_report.txt)
2. The agent used the correct range parameter (unread)
3. The output contains the correct standard format from SKILL.md
4. The correct number of emails and reminders are reported
5. The agent correctly piped fetch_emails.sh to create_reminders.py
6. Reminder details are present and correctly formatted
"""

import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    passed_all = True

    # ─── Check 1: Required output file exists ───────────────────────────────
    report_files = list(ws.rglob("email_schedule_report.txt"))
    check1_passed = len(report_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": check1_passed,
        "detail": f"Found {len(report_files)} file(s) named 'email_schedule_report.txt'" if check1_passed
                  else "No file named 'email_schedule_report.txt' found in workspace"
    })
    if not check1_passed:
        passed_all = False
        # Can't continue without the file
        return passed_all, checks

    report_path = report_files[0]
    try:
        report_content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read report file: {e}"
        })
        return False, checks

    # ─── Check 2: Standard SKILL.md header emoji present ────────────────────
    has_header = "📧 邮件检索完成" in report_content
    checks.append({
        "name": "standard_format_header",
        "passed": has_header,
        "detail": "Report contains '📧 邮件检索完成' header" if has_header
                  else f"Missing required header '📧 邮件检索完成'. Got: {report_content[:200]!r}"
    })
    if not has_header:
        passed_all = False

    # ─── Check 3: Email count line present and correct ──────────────────────
    # "unread" range returns 5 emails from mock DB
    email_count_match = re.search(r'查看邮件数量:\s*(\d+)', report_content)
    if email_count_match:
        email_count = int(email_count_match.group(1))
        count_correct = email_count == 5
        checks.append({
            "name": "correct_email_count",
            "passed": count_correct,
            "detail": f"Email count is {email_count}, expected 5 (unread emails in mock DB)"
                      if not count_correct
                      else f"Correct email count: {email_count}"
        })
        if not count_correct:
            passed_all = False
    else:
        checks.append({
            "name": "correct_email_count",
            "passed": False,
            "detail": f"'查看邮件数量:' line not found in report. Content snippet: {report_content[:300]!r}"
        })
        passed_all = False

    # ─── Check 4: Reminder count line present and > 0 ───────────────────────
    reminder_count_match = re.search(r'创建提醒数量:\s*(\d+)', report_content)
    if reminder_count_match:
        reminder_count = int(reminder_count_match.group(1))
        has_reminders = reminder_count >= 1
        checks.append({
            "name": "reminders_created",
            "passed": has_reminders,
            "detail": f"Reminder count is {reminder_count} (>= 1 required, since unread emails have future events)"
                      if has_reminders
                      else f"Expected at least 1 reminder created, got {reminder_count}"
        })
        if not has_reminders:
            passed_all = False
    else:
        checks.append({
            "name": "reminders_created",
            "passed": False,
            "detail": "'创建提醒数量:' line not found in report"
        })
        passed_all = False

    # ─── Check 5: Reminder details section with bullet points ───────────────
    has_detail_section = "提醒详情:" in report_content
    bullet_items = re.findall(r'^• .+', report_content, re.MULTILINE)
    has_bullets = len(bullet_items) >= 1
    checks.append({
        "name": "reminder_detail_section",
        "passed": has_detail_section and has_bullets,
        "detail": f"Found '提醒详情:' section with {len(bullet_items)} bullet item(s)"
                  if (has_detail_section and has_bullets)
                  else f"Missing '提醒详情:' section or bullet points. has_section={has_detail_section}, bullets={bullet_items}"
    })
    if not (has_detail_section and has_bullets):
        passed_all = False

    # ─── Check 6: Correct range was used (unread) ───────────────────────────
    # Verify via the machine-readable result saved by create_reminders.py
    # AND by checking that only unread emails (5) were fetched, not all (8)
    result_json_path = ws / "data/processed/last_run_result.json"
    try:
        result_data = json.loads(result_json_path.read_text(encoding="utf-8"))
        used_correct_count = result_data.get("email_count") == 5
        checks.append({
            "name": "unread_range_used",
            "passed": used_correct_count,
            "detail": f"Pipeline processed {result_data.get('email_count')} emails (5 = correct for 'unread' range)"
                      if used_correct_count
                      else f"Pipeline processed {result_data.get('email_count')} emails; expected 5 for 'unread'. "
                           f"If 8 was used, agent likely used 'all' range instead of 'unread'."
        })
        if not used_correct_count:
            passed_all = False
    except FileNotFoundError:
        checks.append({
            "name": "unread_range_used",
            "passed": False,
            "detail": "last_run_result.json not found; create_reminders.py was likely not called via the pipeline"
        })
        passed_all = False
    except Exception as e:
        checks.append({
            "name": "unread_range_used",
            "passed": False,
            "detail": f"Error reading last_run_result.json: {e}"
        })
        passed_all = False

    # ─── Check 7: Pipe-based workflow (both scripts were used together) ──────
    # Verify that fetch_emails.sh was used (not direct sqlite3) by checking
    # that the output has items from the mock DB subjects
    known_subjects = [
        "高管战略会议",
        "季度业绩评审",
        "新员工入职培训",
        "客户项目启动会",
        "IT系统维护",
    ]
    subjects_found = [s for s in known_subjects if s in report_content]
    pipeline_worked = len(subjects_found) >= 1
    checks.append({
        "name": "pipeline_produced_real_events",
        "passed": pipeline_worked,
        "detail": f"Report references recognized event subjects: {subjects_found}"
                  if pipeline_worked
                  else f"No known event subjects found in report. The pipeline may not have run correctly."
    })
    if not pipeline_worked:
        passed_all = False

    # ─── Compute score ───────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 3)

    return passed_all, checks, score


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        passed, checks, score = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }))
        sys.exit(1)

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))