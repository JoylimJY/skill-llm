import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── SKILL.md (the skill documentation) ──────────────────────────────────────
skill_md = """\
---
name: macos-applescript-fallback
description: Reliable macOS AppleScript fallback for creating Apple Reminders, Apple Notes, Apple Calendar events, and sending iMessage when direct tool/plugin routes are unavailable or flaky (especially on older macOS versions). Use when users ask to create reminders/notes/calendar events or send a message to their own phone via Messages, and prioritize shell+osascript execution with robust compatibility fallbacks and permission troubleshooting.
---

# macOS AppleScript Fallback

Use local shell + AppleScript for 4 tasks:
1. Create reminder (Reminders)
2. Create note (Notes)
3. Create calendar event (Calendar)
4. Send iMessage (Messages)

Prefer bundled scripts in `scripts/` over ad-hoc inline AppleScript for consistency and compatibility.

## Quick Start

Run these scripts directly:

```bash
# reminder
./scripts/create_reminder.sh "今晚8点吃晚饭" "2026-03-22 20:00:00"

# note (HTML body required)
./scripts/create_note.sh "<h1>武汉三日游</h1><p>Day1 黄鹤楼...</p>" "iCloud"

# calendar
./scripts/create_calendar_event.sh "跑步" "个人" "2026-03-23 08:00:00" "2026-03-23 08:30:00"

# iMessage
./scripts/send_imessage.sh "zhangqianyi1995@icloud.com" "武汉下周末天气：..."
```

## Workflow

### Step 1: Clarify user intent + required fields

- Reminder: title, optional datetime
- Note: title/body content (render as HTML), optional account name
- Calendar: title, calendar name, start datetime, end datetime
- iMessage: recipient (phone or Apple ID), message text

If missing required fields, ask one concise follow-up question.

### Step 2: Execute script (not plugin)

Always call the corresponding script in `scripts/`.

Why:
- avoids low-version parser differences
- centralizes fallback logic
- easier to debug and publish

### Step 3: Confirm result to user

- If script returns an object/id or `sent`, report success.
- If no output but exit code is 0, still report success and suggest user verify in app UI.

### Step 4: On failure, diagnose quickly

Use checks from `references/troubleshooting.md`.

Most frequent root causes:
- macOS Automation permission prompt not approved
- locale-dependent date parsing format
- Messages iMessage service/account not initialized
- target calendar/account name mismatch

## Compatibility Rules (important)

1. **Avoid locale-fragile date strings** where possible.
2. **Messages**: resolve service by `service type = iMessage`, not by hard-coded service name.
3. **Calendar**: if named calendar doesn't exist, fallback to first calendar.
4. **Notes**: if account `iCloud` is missing, fallback to default account.
5. **Notes body uses HTML** (`<h1>`, `<p>`) for stable rendering.

## Output style to user

Keep concise and concrete:
- what was created/sent
- key details (time/target)
- returned ID (if any)
- one-line next step if verification needed

## Bundled Resources

### scripts/

- `create_reminder.sh`
  - args: `<title> ["YYYY-MM-DD HH:MM:SS"]`
- `create_note.sh`
  - args: `<html-body> [account-name]`
- `create_calendar_event.sh`
  - args: `<title> <calendar-name> <start> <end>`
- `send_imessage.sh`
  - args: `<buddy(phone/appleid)> <message>`

### references/

- `troubleshooting.md`
  - permission/automation prompts
  - date parsing and locale issues
  - Messages service/account init
  - calendar/account fallback checks
  - diagnostic commands
"""
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── scripts/ directory with MOCK scripts that log invocations ─────────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Mock create_reminder.sh
(scripts_dir / "create_reminder.sh").write_text("""\
#!/usr/bin/env bash
# MOCK: logs args to /workspace/logs/create_reminder.log
mkdir -p /workspace/logs
echo "ARGS: $@" >> /workspace/logs/create_reminder.log
echo "ARG1: $1" >> /workspace/logs/create_reminder.log
echo "ARG2: $2" >> /workspace/logs/create_reminder.log
echo "reminder-id-$(date +%s)"
exit 0
""", encoding="utf-8")

# Mock create_note.sh
(scripts_dir / "create_note.sh").write_text("""\
#!/usr/bin/env bash
# MOCK: logs args to /workspace/logs/create_note.log
mkdir -p /workspace/logs
echo "ARGS: $@" >> /workspace/logs/create_note.log
echo "ARG1: $1" >> /workspace/logs/create_note.log
echo "ARG2: $2" >> /workspace/logs/create_note.log
echo "note-id-$(date +%s)"
exit 0
""", encoding="utf-8")

# Mock create_calendar_event.sh
(scripts_dir / "create_calendar_event.sh").write_text("""\
#!/usr/bin/env bash
# MOCK: logs args to /workspace/logs/create_calendar_event.log
mkdir -p /workspace/logs
echo "ARGS: $@" >> /workspace/logs/create_calendar_event.log
echo "ARG1: $1" >> /workspace/logs/create_calendar_event.log
echo "ARG2: $2" >> /workspace/logs/create_calendar_event.log
echo "ARG3: $3" >> /workspace/logs/create_calendar_event.log
echo "ARG4: $4" >> /workspace/logs/create_calendar_event.log
echo "event-id-$(date +%s)"
exit 0
""", encoding="utf-8")

# Mock send_imessage.sh
(scripts_dir / "send_imessage.sh").write_text("""\
#!/usr/bin/env bash
# MOCK: logs args to /workspace/logs/send_imessage.log
mkdir -p /workspace/logs
echo "ARGS: $@" >> /workspace/logs/send_imessage.log
echo "ARG1: $1" >> /workspace/logs/send_imessage.log
echo "ARG2: $2" >> /workspace/logs/send_imessage.log
echo "sent"
exit 0
""", encoding="utf-8")

# ── references/ directory ─────────────────────────────────────────────────
refs_dir = workspace / "references"
refs_dir.mkdir(exist_ok=True)

(refs_dir / "troubleshooting.md").write_text("""\
# Troubleshooting macOS AppleScript

## Permission / Automation Prompts
- Go to System Settings > Privacy & Security > Automation
- Enable access for Terminal (or your shell) to control Reminders, Notes, Calendar, Messages

## Date Parsing / Locale Issues
- Always use YYYY-MM-DD HH:MM:SS format to avoid locale-fragile parsing
- Do NOT use natural language strings like "next Monday 9am"

## Messages Service / Account Init
- Ensure Messages app is signed in with Apple ID
- Service must be resolved by type = iMessage, not hard-coded name

## Calendar / Account Fallback
- If the named calendar does not exist, the script falls back to the first available calendar
- Verify calendar name matches exactly (case-sensitive)

## Diagnostic Commands
- check automation perms: tccutil reset AppleEvents
- list calendars: osascript -e 'tell application "Calendar" to get name of every calendar'
- list Notes accounts: osascript -e 'tell application "Notes" to get name of every account'
""", encoding="utf-8")

# ── TASK BRIEF (the actual business request context) ──────────────────────
task_brief = {
    "executive": "Sarah Chen",
    "trip": "Singapore Business Summit",
    "calendar_event": {
        "title": "Singapore Business Summit – Keynote Session",
        "calendar": "Work",
        "start": "2026-07-14 09:00:00",
        "end": "2026-07-14 11:30:00"
    },
    "note": {
        "title": "Singapore Trip Prep Checklist",
        "body_plain": "Passport renewal deadline: June 30. Hotel: Marina Bay Sands. Contact: David Lim (+65-9123-4567). Agenda: Day1 Registration, Day2 Keynote, Day3 Workshops.",
        "account": "iCloud"
    },
    "imessage": {
        "recipient": "david.lim@summit2026.com",
        "message": "Hi David, Sarah Chen here. Confirmed for the Singapore Business Summit keynote on July 14. Looking forward to meeting you!"
    }
}
(workspace / "task_brief.json").write_text(json.dumps(task_brief, indent=2), encoding="utf-8")

# ── Distractor files (realistic consulting firm workspace) ─────────────────
distractors = {
    "clients/acme_corp/proposal_v3.md": "# ACME Corp Proposal\n\nObjective: Reduce operational costs by 18%...\n\n## Timeline\n- Q1: Assessment\n- Q2: Implementation",
    "clients/acme_corp/budget_2026.csv": "Category,Planned,Actual\nTravel,50000,47300\nHosting,12000,11800\nMarketing,80000,79500",
    "clients/techwave/sow_draft.txt": "Statement of Work - TechWave Digital Transformation\nScope: Cloud migration of legacy ERP systems.\nDuration: 18 months",
    "clients/techwave/contacts.json": json.dumps([
        {"name": "Alice Ng", "role": "CTO", "email": "alice.ng@techwave.io"},
        {"name": "Bob Tan", "role": "PM", "email": "bob.tan@techwave.io"}
    ], indent=2),
    "internal/hr/onboarding_checklist.md": "# New Employee Onboarding\n1. IT setup request\n2. Badge activation\n3. Benefits enrollment\n4. First-week schedule",
    "internal/hr/team_roster.csv": "Name,Department,Location\nSarah Chen,Strategy,Singapore\nMark Liu,Engineering,Taipei\nJulia Park,Design,Seoul",
    "internal/finance/expense_policy.md": "# Expense Policy 2026\n\nAll travel expenses above $500 require VP approval.\nReceipts must be submitted within 14 days of travel.",
    "internal/finance/q1_summary.json": json.dumps({"revenue": 1240000, "expenses": 890000, "net": 350000}),
    "ops/automation/legacy_cron.sh": "#!/bin/bash\n# Old cron job - deprecated\n# 0 9 * * 1 python3 /opt/reports/weekly.py",
    "ops/automation/deploy_notes.txt": "Deployment Notes - v2.3.1\nFix: Calendar sync race condition on macOS 12.\nNote: Scripts moved from /opt to ./scripts/",
    "ops/infra/server_inventory.csv": "Hostname,OS,Role\nprod-web-01,Ubuntu 22.04,Web\nprod-db-01,Ubuntu 22.04,Database\ndev-01,macOS 14,Developer",
    "ops/infra/network_diagram.txt": "Internet -> Firewall -> LB -> [web-01, web-02] -> DB cluster",
    "personal/sarah/travel_history.csv": "Date,Destination,Purpose\n2025-11-10,Tokyo,Client meeting\n2025-09-03,London,Conference\n2025-06-22,New York,Board meeting",
    "personal/sarah/preferences.json": json.dumps({"seat": "window", "meal": "vegetarian", "hotel_chain": "Marriott", "notify": "david.lim@summit2026.com"}),
    "scripts/archive/old_create_note.sh": "#!/bin/bash\n# DEPRECATED - do not use\n# osascript -e 'tell application \"Notes\" to make new note with properties {body:\"'$1'\"}'\necho 'This script is deprecated. Use scripts/create_note.sh instead.'\nexit 1",
    "scripts/utils/check_perms.sh": "#!/bin/bash\necho 'Checking Automation permissions...'\nosascript -e 'tell application \"System Events\" to get name of every process' 2>&1 | head -5",
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# ── logs/ dir pre-created empty (scripts will write here) ─────────────────
(workspace / "logs").mkdir(exist_ok=True)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")