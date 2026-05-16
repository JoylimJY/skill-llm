import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # ---- Helper to safely read a file ----
    def read_file(pattern):
        try:
            results = list(workspace.rglob(pattern))
            if not results:
                return None, f"File '{pattern}' not found anywhere in workspace."
            content = results[0].read_text(encoding="utf-8")
            return content, str(results[0])
        except Exception as e:
            return None, str(e)

    # =========================================================
    # SECTION 1: meeting_summary.md checks
    # =========================================================
    summary_content, summary_path = read_file("meeting_summary.md")

    # Check 1: File exists
    checks.append({
        "name": "meeting_summary.md exists",
        "passed": summary_content is not None,
        "detail": summary_path if summary_content is None else f"Found at {summary_path}"
    })

    if summary_content:
        # Check 2: Has correct title/topic reference in header (Q3 or roadmap or planning)
        has_title = bool(re.search(r'##\s*Meeting Summary.*?(Q3|[Rr]oadmap|[Pp]lanning)', summary_content))
        checks.append({
            "name": "Summary: correct ## Meeting Summary header with topic",
            "passed": has_title,
            "detail": f"Expected '## Meeting Summary: [Q3/Roadmap/Planning topic]'. Content snippet: {summary_content[:200]}"
        })

        # Check 3: Date field present (meeting is July something 2026, or date line present)
        has_date_field = bool(re.search(r'\*\*Date:\*\*', summary_content))
        checks.append({
            "name": "Summary: **Date:** field present",
            "passed": has_date_field,
            "detail": "Expected '**Date:**' metadata line in the summary header block."
        })

        # Check 4: Type field present
        has_type_field = bool(re.search(r'\*\*Type:\*\*', summary_content))
        checks.append({
            "name": "Summary: **Type:** field present",
            "passed": has_type_field,
            "detail": "Expected '**Type:**' metadata line."
        })

        # Check 5: 🎯 Key Outcomes section with emoji
        has_key_outcomes = bool(re.search(r'###\s*🎯\s*Key Outcomes', summary_content))
        checks.append({
            "name": "Summary: ### 🎯 Key Outcomes section present",
            "passed": has_key_outcomes,
            "detail": "Must use exact emoji header '### 🎯 Key Outcomes'"
        })

        # Check 6: 📌 Topics Discussed section with emoji
        has_topics = bool(re.search(r'###\s*📌\s*Topics Discussed', summary_content))
        checks.append({
            "name": "Summary: ### 📌 Topics Discussed section present",
            "passed": has_topics,
            "detail": "Must use exact emoji header '### 📌 Topics Discussed'"
        })

        # Check 7: ❓ Open Questions section with emoji
        has_questions = bool(re.search(r'###\s*❓\s*Open Questions', summary_content))
        checks.append({
            "name": "Summary: ### ❓ Open Questions section present",
            "passed": has_questions,
            "detail": "Must use exact emoji header '### ❓ Open Questions'"
        })

        # Check 8: Postgres upgrade question captured as open question
        has_postgres_q = bool(re.search(r'[Pp]ostgres|database.*upgrade|upgrade.*database', summary_content))
        checks.append({
            "name": "Summary: Postgres/DB upgrade captured as open question or outcome",
            "passed": has_postgres_q,
            "detail": "The Postgres 16 upgrade was an explicitly unresolved question — must appear in Open Questions or outcomes."
        })

        # Check 9: 👥 Participants section with emoji
        has_participants = bool(re.search(r'###\s*👥\s*Participants', summary_content))
        checks.append({
            "name": "Summary: ### 👥 Participants section present",
            "passed": has_participants,
            "detail": "Must use exact emoji header '### 👥 Participants'"
        })

        # Check 10: Key decisions captured — auth fix, notifications, onboarding
        has_auth_decision = bool(re.search(r'auth|[Aa]uth\s*(fix|latency|investigation)', summary_content))
        has_notif_decision = bool(re.search(r'notification', summary_content, re.IGNORECASE))
        has_onboarding_decision = bool(re.search(r'onboarding', summary_content, re.IGNORECASE))
        key_decisions_score = sum([has_auth_decision, has_notif_decision, has_onboarding_decision])
        checks.append({
            "name": "Summary: Key decisions captured (auth fix, notifications, onboarding) — at least 2 of 3",
            "passed": key_decisions_score >= 2,
            "detail": f"Auth: {has_auth_decision}, Notifications: {has_notif_decision}, Onboarding: {has_onboarding_decision}"
        })

        # =========================================================
        # SECTION 2: Action Items table in meeting_summary.md
        # =========================================================

        # Check 11: ✅ Action Items section with emoji
        has_action_items = bool(re.search(r'###\s*✅\s*Action Items', summary_content))
        checks.append({
            "name": "Summary: ### ✅ Action Items section present",
            "passed": has_action_items,
            "detail": "Must use exact emoji header '### ✅ Action Items'"
        })

        # Check 12: Action items table has all 5 required columns
        table_header = re.search(r'\|\s*Priority\s*\|.*Task.*\|.*Owner.*\|.*Deadline.*\|.*Status.*\|', summary_content)
        checks.append({
            "name": "Action Items: table has all 5 columns (Priority, Task, Owner, Deadline, Status)",
            "passed": bool(table_header),
            "detail": "The action items table must have exactly these columns: Priority | Task | Owner | Deadline | Status"
        })

        # Check 13: 🔴 HIGH for auth fix (trigger words: "blocking", "urgent", "today", "asap")
        # Marcus said "I'll have root cause done by end of day today" — "today" = HIGH
        # Aisha said "it's actively blocking" — HIGH
        has_high_priority = bool(re.search(r'🔴', summary_content))
        checks.append({
            "name": "Action Items: 🔴 HIGH priority used at least once",
            "passed": has_high_priority,
            "detail": "Auth fix was described as 'blocking' and 'end of day today' — must trigger 🔴 HIGH priority."
        })

        # Check 14: Auth fix assigned to Marcus with HIGH priority and today deadline
        # Pattern: 🔴 in same row as Marcus or auth
        auth_row = re.search(r'\|\s*🔴[^|]*\|[^|]*[Aa]uth[^|]*\|[^|]*[Mm]arcus[^|]*\|', summary_content)
        auth_row2 = re.search(r'\|\s*🔴[^|]*\|[^|]*[Mm]arcus[^|]*\|[^|]*[Aa]uth[^|]*\|', summary_content)
        # More flexible: check that Marcus + auth/root cause appears in a HIGH row
        marcus_auth_high = bool(re.search(r'🔴.*[Mm]arcus.*[Aa]uth|🔴.*[Aa]uth.*[Mm]arcus', summary_content.replace('\n', ' ')))
        checks.append({
            "name": "Action Items: Auth fix tagged 🔴 HIGH with Marcus as owner",
            "passed": bool(auth_row or auth_row2 or marcus_auth_high),
            "detail": "Marcus's auth root cause analysis (due today, blocking) must be 🔴 HIGH."
        })

        # Check 15: 🟡 MEDIUM for Aisha's notifications backend (due Friday "this week")
        aisha_medium = bool(re.search(r'🟡.*[Aa]isha|[Aa]isha.*🟡', summary_content.replace('\n', ' ')))
        checks.append({
            "name": "Action Items: Aisha's notifications backend tagged 🟡 MEDIUM",
            "passed": aisha_medium,
            "detail": "Aisha said 'this week' (July 11th) for notifications backend — trigger word 'this week' → 🟡 MEDIUM."
        })

        # Check 16: 🟢 LOW for Dev Patel's mobile bug tickets (trigger: "eventually", "next sprint", "no rush")
        dev_low = bool(re.search(r'🟢.*[Dd]ev|[Dd]ev.*🟢', summary_content.replace('\n', ' ')))
        checks.append({
            "name": "Action Items: Dev Patel's mobile bug tickets tagged 🟢 LOW",
            "passed": dev_low,
            "detail": "Dev said 'eventually' for mobile bug tickets and PM said 'no rush' — must be 🟢 LOW."
        })

        # Check 17: All action item rows have ⏳ Pending status
        pending_count = len(re.findall(r'⏳\s*Pending', summary_content))
        # We expect at least 5 action items from the transcript
        has_pending = pending_count >= 3
        checks.append({
            "name": "Action Items: Status column uses ⏳ Pending for at least 3 items",
            "passed": has_pending,
            "detail": f"Found {pending_count} '⏳ Pending' entries. All action item rows should have '⏳ Pending' in Status column."
        })

        # Check 18: @name format used for owners (@ prefix)
        has_at_owners = bool(re.search(r'@\w+', summary_content))
        checks.append({
            "name": "Action Items: @ prefix used for owner names (e.g., @marcus)",
            "passed": has_at_owners,
            "detail": "Owners in action items table should use @name format per SKILL.md spec."
        })

    # =========================================================
    # SECTION 3: followup_email.md checks
    # =========================================================
    email_content, email_path = read_file("followup_email.md")

    # Check 19: File exists
    checks.append({
        "name": "followup_email.md exists",
        "passed": email_content is not None,
        "detail": email_path if email_content is None else f"Found at {email_path}"
    })

    if email_content:
        # Check 20: Subject line has correct format with 📋 emoji
        has_subject_emoji = bool(re.search(r'Subject:\s*📋', email_content))
        checks.append({
            "name": "Email: Subject line starts with '📋' emoji",
            "passed": has_subject_emoji,
            "detail": "Subject line must follow: 'Subject: 📋 Meeting Recap: [Topic] — [Date]'"
        })

        # Check 21: Subject has "Meeting Recap" text
        has_meeting_recap = bool(re.search(r'Meeting Recap', email_content))
        checks.append({
            "name": "Email: Subject contains 'Meeting Recap'",
            "passed": has_meeting_recap,
            "detail": "Subject line must contain 'Meeting Recap' per template."
        })

        # Check 22: Subject has em dash (—) not regular hyphen
        has_em_dash = bool(re.search(r'📋.*Meeting Recap.*—', email_content))
        checks.append({
            "name": "Email: Subject uses em dash (—) between topic and date",
            "passed": has_em_dash,
            "detail": "Template requires em dash '—' in subject: 'Meeting Recap: [Topic] — [Date]'"
        })

        # Check 23: 🎯 Key Decisions section in email
        has_email_decisions = bool(re.search(r'###\s*🎯\s*Key Decisions', email_content))
        checks.append({
            "name": "Email: ### 🎯 Key Decisions section present",
            "passed": has_email_decisions,
            "detail": "Email must have '### 🎯 Key Decisions' section with exact emoji."
        })

        # Check 24: 📌 Action Items section in email
        has_email_actions = bool(re.search(r'###\s*📌\s*Action Items', email_content))
        checks.append({
            "name": "Email: ### 📌 Action Items section present",
            "passed": has_email_actions,
            "detail": "Email must have '### 📌 Action Items' section with exact emoji."
        })

        # Check 25: Email action items table has Task, Owner, Due columns
        email_table = bool(re.search(r'\|\s*Task\s*\|.*Owner.*\|.*Due.*\|', email_content))
        checks.append({
            "name": "Email: Action items table has Task | Owner | Due columns",
            "passed": bool(email_table),
            "detail": "Email template specifies a 3-column table: Task | Owner | Due"
        })

        # Check 26: 🗓 Next Steps section
        has_next_steps = bool(re.search(r'###\s*🗓\s*Next Steps', email_content))
        checks.append({
            "name": "Email: ### 🗓 Next Steps section present",
            "passed": has_next_steps,
            "detail": "Email must have '### 🗓 Next Steps' section with exact emoji."
        })

        # Check 27: Closing phrase "Questions? Reply or swing by my desk."
        has_closing = bool(re.search(r'Questions\?\s*Reply or swing by my desk', email_content))
        checks.append({
            "name": "Email: Exact closing phrase 'Questions? Reply or swing by my desk.'",
            "passed": has_closing,
            "detail": "Email must end with the exact phrase: 'Questions? Reply or swing by my desk.'"
        })

        # Check 28: Next meeting date captured (July 15)
        has_next_meeting = bool(re.search(r'July\s*15|Jul\s*15|15th|Tuesday', email_content, re.IGNORECASE))
        checks.append({
            "name": "Email: Next meeting date (July 15) or Tuesday captured in Next Steps",
            "passed": has_next_meeting,
            "detail": "The transcript explicitly set next meeting: Tuesday July 15th at 2pm."
        })

    # =========================================================
    # SCORING
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    return {
        "passed": score >= 0.75,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))