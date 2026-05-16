import os
import random
import json
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ---------- Skill directory structure ----------
skill_dir = workspace / "skills" / "macos-calendar"
scripts_dir = skill_dir / "scripts"
references_dir = skill_dir / "references"
logs_dir = skill_dir / "logs"
for d in [scripts_dir, references_dir, logs_dir]:
    d.mkdir(parents=True, exist_ok=True)

# The mock calendar.sh — intercepts calls and records them
# It simulates list-calendars and create-event behavior
calendar_sh = scripts_dir / "calendar.sh"
calendar_sh.write_text(r"""#!/usr/bin/env bash
# Mock calendar.sh — records all invocations for evaluation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
LOG="$SKILL_DIR/logs/calendar.log"
CAPTURE="$SKILL_DIR/logs/capture.jsonl"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

cmd="$1"

case "$cmd" in
  list-calendars)
    echo "Work"
    echo "Personal [read-only]"
    echo "Birthdays [read-only]"
    # Log the call
    echo "{\"ts\":\"$(timestamp)\",\"cmd\":\"list-calendars\"}" >> "$CAPTURE"
    echo "{\"ts\":\"$(timestamp)\",\"cmd\":\"list-calendars\"}" >> "$LOG"
    ;;
  create-event)
    # Read JSON from stdin
    input=$(cat)
    if [ -z "$input" ]; then
      echo "ERROR: No JSON provided on stdin" >&2
      exit 1
    fi
    # Validate it's parseable JSON
    echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK')" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
      echo "ERROR: Invalid JSON" >&2
      exit 1
    fi
    # Extract summary and calendar for logging
    summary=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('summary',''))" 2>/dev/null)
    calendar=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('calendar',''))" 2>/dev/null)
    # Reject read-only calendars
    if echo "$calendar" | grep -qi "read-only\|birthdays\|Personal"; then
      echo "ERROR: Calendar '$calendar' is read-only or does not exist" >&2
      exit 1
    fi
    # Record capture
    record=$(echo "$input" | python3 -c "
import sys, json
d = json.load(sys.stdin)
import datetime
d['_captured_at'] = '$(timestamp)'
d['_cmd'] = 'create-event'
print(json.dumps(d))
")
    echo "$record" >> "$CAPTURE"
    echo "{\"ts\":\"$(timestamp)\",\"cmd\":\"create-event\",\"calendar\":\"$calendar\",\"summary\":\"$summary\"}" >> "$LOG"
    echo "Event created: $summary"
    ;;
  *)
    echo "ERROR: Unknown command: $cmd" >&2
    exit 1
    ;;
esac
""")
calendar_sh.chmod(calendar_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# Recurrence reference doc
(references_dir / "recurrence.md").write_text("""# iCal Recurrence Rules (RRULE)

Apple Calendar uses standard iCal RRULE format for recurring events.

## Common patterns

| Pattern | RRULE |
|---|---|
| Daily | `FREQ=DAILY;INTERVAL=1` |
| Every weekday | `FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR` |
| Weekly | `FREQ=WEEKLY;INTERVAL=1` |
| Biweekly | `FREQ=WEEKLY;INTERVAL=2` |
| Monthly (same date) | `FREQ=MONTHLY;INTERVAL=1` |
| Monthly (e.g. 2nd Tuesday) | `FREQ=MONTHLY;BYDAY=2TU` |
| Yearly | `FREQ=YEARLY;INTERVAL=1` |

## Limiting recurrence

- End after N occurrences: add `COUNT=10`
- End by date: add `UNTIL=20261231T000000Z`

## Examples

- Every Monday and Wednesday: `FREQ=WEEKLY;BYDAY=MO,WE`
- First Friday of every month: `FREQ=MONTHLY;BYDAY=1FR`
- Every 3 days for 5 times: `FREQ=DAILY;INTERVAL=3;COUNT=5`
""")

# ---------- Distractor files ----------
# Project management files that make the workspace feel real
(workspace / "project_charter.md").write_text("""# Project: Phoenix Platform Rebuild
## Status: Planning Phase
## Kickoff Target: Next Wednesday
## Sprint Cadence: Biweekly (every 2 weeks) starting next cycle
## Team standups: Every Friday afternoon
## Key stakeholders: Engineering, Product, Design
""")

(workspace / "team_calendar_notes.txt").write_text("""Team sync preferences:
- Engineering prefers Friday afternoon (3pm) for sprint reviews
- Sprint reviews should be 30 minutes
- Biweekly cadence confirmed by Scrum Master
- Kickoff meeting confirmed for next Wednesday 10am, will run 90 minutes
- All recurring meetings: 8 occurrences to cover Q3
- Reminder alerts: 15 min for kickoff, 5 min for recurring reviews
- Use the Work calendar only (Personal is private/read-only)
""")

(workspace / "meeting_requests.txt").write_text("""PENDING CALENDAR ITEMS
======================
1. Project Phoenix Kickoff
   - When: Next Wednesday at 10:00 AM
   - Duration: 90 minutes
   - Reminder: 15 minutes before
   - Calendar: Work
   - Notes: Initial project kickoff for Phoenix Platform Rebuild

2. Biweekly Sprint Review
   - Cadence: Every 2 weeks on Fridays
   - Time: 3:00 PM
   - Duration: 30 minutes
   - Reminder: 5 minutes before
   - Occurrences: 8 total
   - Calendar: Work
   - Notes: Sprint review and retrospective
""")

# Distractor subdirectory: old meeting notes
old_notes = workspace / "archive" / "2024" / "meeting_notes"
old_notes.mkdir(parents=True, exist_ok=True)
for i in range(1, 6):
    (old_notes / f"sprint_{i:02d}_notes.md").write_text(f"""# Sprint {i} Notes
Date: 2024-0{i}-15
Attendees: Alice, Bob, Charlie
Action items: TBD
""")

# Distractor: a broken JSON config
(workspace / "config").mkdir(exist_ok=True)
(workspace / "config" / "old_events.json").write_text("""[
  {"title": "Old standup", "date": "2024-03-01", "time": "09:00"},
  {"title": "Broken event", "date": "bad-date", "time": "25:99"},
]""")

# Distractor: some shell scripts unrelated to the task
scripts_misc = workspace / "scripts"
scripts_misc.mkdir(exist_ok=True)
(scripts_misc / "export_contacts.sh").write_text("#!/bin/bash\n# Export macOS Contacts to CSV\necho 'Not implemented'\n")
(scripts_misc / "backup_calendar.sh").write_text("#!/bin/bash\n# Backup calendar ICS files\ncp ~/Library/Calendars/*.caldav /tmp/backup/ 2>/dev/null\n")

# Distractor: requirements/planning docs
(workspace / "sprint_planning" / "q3_roadmap.csv").parent.mkdir(exist_ok=True)
(workspace / "sprint_planning" / "q3_roadmap.csv").write_text(
    "Sprint,Start,End,Goal\n1,2026-07-07,2026-07-18,Foundation\n2,2026-07-21,2026-08-01,API Layer\n"
)

# Distractor: a Python helper that does NOT solve the task
(workspace / "utils" / "date_helper.py").parent.mkdir(exist_ok=True)
(workspace / "utils" / "date_helper.py").write_text("""#!/usr/bin/env python3
# Generic date utilities - NOT specific to calendar skill
import datetime

def days_until_weekday(target_weekday):
    \"\"\"Returns days until next occurrence of weekday (0=Mon, 6=Sun).\"\"\"
    today = datetime.date.today()
    days_ahead = target_weekday - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return days_ahead

if __name__ == '__main__':
    print(f"Days until Monday: {days_until_weekday(0)}")
    print(f"Days until Friday: {days_until_weekday(4)}")
""")

# Distractor: environment notes
(workspace / "env_notes.txt").write_text("""Environment setup notes
- SKILL_DIR should point to the skill root
- Scripts live under $SKILL_DIR/scripts/
- Logs go to $SKILL_DIR/logs/
- Python3 and bash are available
""")

# Set SKILL_DIR env hint in a dotenv (agent must discover the path)
(workspace / ".env").write_text(f'SKILL_DIR="{str(skill_dir)}"\n')

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Calendar script: {calendar_sh}")