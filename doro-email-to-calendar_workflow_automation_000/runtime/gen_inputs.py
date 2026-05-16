#!/usr/bin/env python3
import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

HOME = Path(os.path.expanduser("~"))

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    HOME / ".config" / "email-to-calendar",
    HOME / ".openclaw" / "workspace" / "skills" / "email-to-calendar" / "scripts",
    HOME / ".openclaw" / "workspace" / "skills" / "email-to-calendar" / "references",
    HOME / ".openclaw" / "workspace" / "memory" / "email-extractions",
    HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar",
    HOME / ".openclaw" / "workspace" / "logs",
    HOME / ".openclaw" / "workspace" / "tmp",
    HOME / "emails" / "inbox",
    HOME / "emails" / "archive",
    HOME / "projects" / "school-calendar" / "notes",
    HOME / "projects" / "school-calendar" / "exports",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── config.json ─────────────────────────────────────────────────────────────
config = {
    "provider": "gog",
    "email_mode": "direct",
    "gmail_account": "parent@familymail.com",
    "calendar_id": "family_primary",
    "attendees": {
        "enabled": True,
        "emails": ["parent@familymail.com", "spouse@familymail.com"]
    },
    "whole_day_events": {
        "style": "timed",
        "start_time": "09:00",
        "end_time": "17:00"
    },
    "multi_day_events": {
        "style": "daily_recurring"
    },
    "event_rules": {
        "ignore_patterns": ["fundraiser", "PTA meeting", "volunteer request"],
        "auto_create_patterns": ["No School", "holiday", "Staff Development Day"]
    },
    "email_handling": {
        "mark_read": True,
        "archive": True,
        "auto_dispose_calendar_replies": True
    },
    "deadline_notifications": {
        "enabled": True,
        "email_recipient": "parent@familymail.com"
    },
    "agent_name": "FamilyCalBot"
}
(HOME / ".config" / "email-to-calendar" / "config.json").write_text(
    json.dumps(config, indent=2)
)

# ── index.json (empty – email not yet processed) ─────────────────────────────
index = {"extractions": []}
(HOME / ".openclaw" / "workspace" / "memory" / "email-extractions" / "index.json").write_text(
    json.dumps(index, indent=2)
)

# ── events.json (empty tracking store) ──────────────────────────────────────
(HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar" / "events.json").write_text(
    json.dumps({"events": []}, indent=2)
)

# ── pending_invites.json ─────────────────────────────────────────────────────
(HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar" / "pending_invites.json").write_text(
    json.dumps({"pending": []}, indent=2)
)

# ── activity.json ────────────────────────────────────────────────────────────
(HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar" / "activity.json").write_text(
    json.dumps({"sessions": []}, indent=2)
)

# ── changelog.json ───────────────────────────────────────────────────────────
(HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar" / "changelog.json").write_text(
    json.dumps({"changes": []}, indent=2)
)

# ── The email the agent must process ────────────────────────────────────────
email_id = "msg_4a7f9c2b1d8e3f56"
email_content = {
    "id": email_id,
    "threadId": "thread_99xk2m",
    "subject": "Spring Showcase Concert – Reserve Your Seats!",
    "from": "events@lincolnelementary.edu",
    "to": "parent@familymail.com",
    "date": "2026-03-05T08:30:00",
    "snippet": "Join us for the Spring Showcase Concert! RSVP by March 20.",
    "body": """Dear Lincoln Elementary Families,

We are thrilled to invite you to our annual Spring Showcase Concert!

Event Details:
Date: Friday, April 11, 2026
Time: 7:00 PM – 9:00 PM
Location: Lincoln Elementary Auditorium, 500 Oak Street

Our talented students have been rehearsing all semester and cannot wait to perform for you. This is a family-friendly evening featuring choral performances, band pieces, and a special drama segment.

IMPORTANT: Seating is limited. Please RSVP by March 20, 2026 to guarantee your family's spot.

Get your free tickets here: https://lincolnelementary.edu/spring-concert-2026

Also coming up – don't forget our School Fundraiser Gala on April 5. Purchase raffle tickets at https://lincolnelementary.edu/fundraiser-gala (Note: This is a separate ticketed event for adults only.)

We hope to see you all there!

Warm regards,
The Lincoln Elementary Events Committee
events@lincolnelementary.edu
"""
}
(HOME / "emails" / "inbox" / f"{email_id}.json").write_text(
    json.dumps(email_content, indent=2)
)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = [
    (HOME / "projects" / "school-calendar" / "notes" / "old_events_2025.txt",
     "March 2025 events exported from old system.\nSpring Play - March 10 2025\nField Day - May 5 2025\n"),
    (HOME / "projects" / "school-calendar" / "exports" / "calendar_backup_2025.json",
     json.dumps({"events": [{"id": "old1", "summary": "Spring Play 2025", "date": "2025-03-10"}]}, indent=2)),
    (HOME / "emails" / "archive" / "msg_old_processed.json",
     json.dumps({"id": "msg_old_processed", "subject": "Fall Festival", "processed": True}, indent=2)),
    (HOME / ".openclaw" / "workspace" / "logs" / "session_2026_02_01.log",
     "Session started at 2026-02-01 09:00:00\nProcessed 3 emails\nCreated 2 events\nSession ended at 2026-02-01 09:05:00\n"),
    (HOME / ".openclaw" / "workspace" / "tmp" / "draft_event.json",
     json.dumps({"draft": True, "title": "DRAFT - not real", "date": "2026-01-01"}, indent=2)),
    (HOME / "emails" / "inbox" / "msg_calendar_reply.json",
     json.dumps({"id": "msg_cal_reply", "from": "calendar-notification@google.com",
                 "subject": "Accepted: Team Meeting", "body": "John accepted your event."}, indent=2)),
    (HOME / "projects" / "school-calendar" / "notes" / "rsvp_tracker.csv",
     "family,rsvp_date,attending\nSmith,2026-02-15,yes\nJones,2026-02-20,no\n"),
    (HOME / ".openclaw" / "workspace" / "memory" / "email-extractions" / "2026-02-01-extraction.json",
     json.dumps({"email_id": "msg_old_feb", "events": [], "status": "processed"}, indent=2)),
    (HOME / ".config" / "email-to-calendar" / "config.json.bak",
     json.dumps({"legacy": True, "gmail_account": "oldaccount@gmail.com"}, indent=2)),
    (HOME / ".openclaw" / "workspace" / "memory" / "email-to-calendar" / "README_DO_NOT_EDIT.txt",
     "This directory is managed by the email-to-calendar skill. Do not edit files manually.\n"),
    (HOME / "emails" / "archive" / "msg_fundraiser_old.json",
     json.dumps({"id": "msg_fundraiser_old", "subject": "Fundraiser - last year",
                 "from": "events@lincolnelementary.edu", "body": "Buy raffle tickets!"}, indent=2)),
]
for path, content in distractors:
    path.write_text(content)

# ── Mock wrapper scripts ─────────────────────────────────────────────────────
SCRIPTS_DIR = HOME / ".openclaw" / "workspace" / "skills" / "email-to-calendar" / "scripts"

# Shared state files used by mock scripts
state_dir = HOME / ".openclaw" / "workspace" / "mock_state"
state_dir.mkdir(parents=True, exist_ok=True)
(state_dir / "created_events.json").write_text(json.dumps([], indent=2))
(state_dir / "sent_emails.json").write_text(json.dumps([], indent=2))
(state_dir / "pending_log.json").write_text(json.dumps([], indent=2))
(state_dir / "activity_log.json").write_text(json.dumps([], indent=2))
(state_dir / "session_state.json").write_text(json.dumps({"active": False, "started": None}, indent=2))

EXECUTABLE = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH

def write_script(path, content):
    path.write_text(content)
    path.chmod(EXECUTABLE)

# email_read.sh
write_script(SCRIPTS_DIR / "email_read.sh", r"""#!/bin/bash
EMAIL_ID=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --email-id) EMAIL_ID="$2"; shift 2 ;;
        *) shift ;;
    esac
done
INBOX="$HOME/emails/inbox/${EMAIL_ID}.json"
if [ -f "$INBOX" ]; then
    cat "$INBOX"
else
    echo '{"error":"Email not found"}' >&2
    exit 1
fi
""")

# email_search.sh
write_script(SCRIPTS_DIR / "email_search.sh", r"""#!/bin/bash
# Returns emails from inbox
EMAILS=()
for f in "$HOME/emails/inbox/"*.json; do
    EMAILS+=("$(cat "$f")")
done
echo "[$(IFS=,; echo "${EMAILS[*]}")]"
""")

# activity_log.sh – records calls for eval
write_script(SCRIPTS_DIR / "activity_log.sh", r"""#!/bin/bash
STATE_DIR="$HOME/.openclaw/workspace/mock_state"
LOG="$STATE_DIR/activity_log.json"
SESSION="$STATE_DIR/session_state.json"

CMD="$1"; shift
ENTRY="{\"cmd\":\"$CMD\""

case "$CMD" in
    start-session)
        python3 -c "
import json, datetime
with open('$SESSION') as f: s=json.load(f)
s['active']=True; s['started']=datetime.datetime.now().isoformat()
with open('$SESSION','w') as f: json.dump(s,f)
"
        ENTRY="$ENTRY}"
        ;;
    end-session)
        python3 -c "
import json
with open('$SESSION') as f: s=json.load(f)
s['active']=False
with open('$SESSION','w') as f: json.dump(s,f)
"
        ENTRY="$ENTRY}"
        ;;
    log-skip)
        EMAIL_ID=""; SUBJECT=""; REASON=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --email-id) EMAIL_ID="$2"; shift 2 ;;
                --subject) SUBJECT="$2"; shift 2 ;;
                --reason) REASON="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        ENTRY="$ENTRY,\"email_id\":\"$EMAIL_ID\",\"subject\":\"$SUBJECT\",\"reason\":\"$REASON\"}"
        ;;
    log-event)
        EMAIL_ID=""; TITLE=""; ACTION=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --email-id) EMAIL_ID="$2"; shift 2 ;;
                --title) TITLE="$2"; shift 2 ;;
                --action) ACTION="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        ENTRY="$ENTRY,\"email_id\":\"$EMAIL_ID\",\"title\":\"$TITLE\",\"action\":\"$ACTION\"}"
        ;;
    show)
        cat "$LOG"
        exit 0
        ;;
    *)
        ENTRY="$ENTRY}"
        ;;
esac

python3 -c "
import json
with open('$LOG') as f: log=json.load(f)
log.append($ENTRY)
with open('$LOG','w') as f: json.dump(log,f,indent=2)
"
""")

# lookup_event.sh
write_script(SCRIPTS_DIR / "lookup_event.sh", r"""#!/bin/bash
STATE_DIR="$HOME/.openclaw/workspace/mock_state"
EVENTS_FILE="$STATE_DIR/created_events.json"
MODE=""
VALUE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --email-id) MODE="email_id"; VALUE="$2"; shift 2 ;;
        --summary) MODE="summary"; VALUE="$2"; shift 2 ;;
        --list) MODE="list"; shift ;;
        --validate) shift ;;
        *) shift ;;
    esac
done

case "$MODE" in
    email_id)
        python3 -c "
import json, sys
with open('$EVENTS_FILE') as f: evts=json.load(f)
res=[e for e in evts if e.get('email_id')=='$VALUE']
print(json.dumps(res))
"
        ;;
    summary)
        python3 -c "
import json
with open('$EVENTS_FILE') as f: evts=json.load(f)
val='$VALUE'.lower()
res=[e for e in evts if val in e.get('title','').lower() or e.get('title','').lower() in val]
print(json.dumps(res))
"
        ;;
    list)
        cat "$EVENTS_FILE"
        ;;
    *)
        echo "[]"
        ;;
esac
""")

# calendar_search.sh
write_script(SCRIPTS_DIR / "calendar_search.sh", r"""#!/bin/bash
# Returns empty - no pre-existing events
echo "[]"
""")

# create_event.sh – the critical mock that records all calls
write_script(SCRIPTS_DIR / "create_event.sh", r"""#!/bin/bash
CALENDAR_ID="$1"
TITLE="$2"
DATE="$3"
START_TIME="$4"
END_TIME="$5"
DESCRIPTION="$6"
ATTENDEES="$7"
EXISTING_EVENT_ID="$8"
EMAIL_ID="$9"

STATE_DIR="$HOME/.openclaw/workspace/mock_state"
EVENTS_FILE="$STATE_DIR/created_events.json"
INDEX_FILE="$HOME/.openclaw/workspace/memory/email-extractions/index.json"

EVENT_ID="evt_$(date +%s%N | md5sum | head -c 12)"

python3 -c "
import json, datetime
with open('$EVENTS_FILE') as f: evts=json.load(f)
entry={
    'event_id': '$EVENT_ID',
    'calendar_id': '$CALENDAR_ID',
    'title': '$TITLE',
    'date': '$DATE',
    'start_time': '$START_TIME',
    'end_time': '$END_TIME',
    'description': '''$DESCRIPTION''',
    'attendees': '$ATTENDEES',
    'existing_event_id': '$EXISTING_EVENT_ID',
    'email_id': '$EMAIL_ID',
    'created_at': datetime.datetime.now().isoformat()
}
evts.append(entry)
with open('$EVENTS_FILE','w') as f: json.dump(evts,f,indent=2)

# Also update index
with open('$INDEX_FILE') as f: idx=json.load(f)
# check if email already in extractions
found=any(e.get('email_id')=='$EMAIL_ID' for e in idx['extractions'])
if not found and '$EMAIL_ID':
    idx['extractions'].append({'email_id':'$EMAIL_ID','event_id':'$EVENT_ID','title':'$TITLE','status':'processed','created_at':datetime.datetime.now().isoformat()})
    with open('$INDEX_FILE','w') as f: json.dump(idx,f,indent=2)
"

echo "$EVENT_ID"
""")

# add_pending.sh
write_script(SCRIPTS_DIR / "add_pending.sh", r"""#!/bin/bash
STATE_DIR="$HOME/.openclaw/workspace/mock_state"
PENDING_LOG="$STATE_DIR/pending_log.json"
EMAIL_ID=""; EMAIL_SUBJECT=""; EVENTS_JSON=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --email-id) EMAIL_ID="$2"; shift 2 ;;
        --email-subject) EMAIL_SUBJECT="$2"; shift 2 ;;
        --events-json) EVENTS_JSON="$2"; shift 2 ;;
        *) shift ;;
    esac
done

python3 -c "
import json, datetime
with open('$PENDING_LOG') as f: log=json.load(f)
log.append({'email_id':'$EMAIL_ID','email_subject':'$EMAIL_SUBJECT','events_json':$EVENTS_JSON,'logged_at':datetime.datetime.now().isoformat()})
with open('$PENDING_LOG','w') as f: json.dump(log,f,indent=2)
"
echo "Pending invite recorded."
""")

# list_pending.sh
write_script(SCRIPTS_DIR / "list_pending.sh", r"""#!/bin/bash
cat "$HOME/.openclaw/workspace/mock_state/pending_log.json"
""")

# email_send.sh – records sent emails
write_script(SCRIPTS_DIR / "email_send.sh", r"""#!/bin/bash
STATE_DIR="$HOME/.openclaw/workspace/mock_state"
SENT_FILE="$STATE_DIR/sent_emails.json"
TO=""; SUBJECT=""; BODY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --to) TO="$2"; shift 2 ;;
        --subject) SUBJECT="$2"; shift 2 ;;
        --body) BODY="$2"; shift 2 ;;
        *) shift ;;
    esac
done

python3 -c "
import json, datetime
with open('$SENT_FILE') as f: emails=json.load(f)
emails.append({'to':'$TO','subject':'$SUBJECT','body':'''$BODY''','sent_at':datetime.datetime.now().isoformat()})
with open('$SENT_FILE','w') as f: json.dump(emails,f,indent=2)
"
echo "Email sent to $TO"
""")

# disposition_email.sh
write_script(SCRIPTS_DIR / "disposition_email.sh", r"""#!/bin/bash
echo "Email dispositioned."
""")

# process_calendar_replies.sh
write_script(SCRIPTS_DIR / "process_calendar_replies.sh", r"""#!/bin/bash
echo "Calendar replies processed."
""")

# changelog.sh
write_script(SCRIPTS_DIR / "changelog.sh", r"""#!/bin/bash
echo '{"changes":[]}'
""")

# undo.sh
write_script(SCRIPTS_DIR / "undo.sh", r"""#!/bin/bash
echo "No changes to undo."
""")

print("Sandbox workspace generated successfully.")
print(f"Email to process: msg_4a7f9c2b1d8e3f56")
print(f"Config: {HOME}/.config/email-to-calendar/config.json")
print(f"Scripts: {SCRIPTS_DIR}")