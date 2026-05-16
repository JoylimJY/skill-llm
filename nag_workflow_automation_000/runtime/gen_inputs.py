import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "memory",
    "references",
    "logs/2026-01",
    "logs/2026-02",
    "clients/alice",
    "clients/bob",
    "scripts",
    "templates",
    "archive/old-configs",
    "reports/weekly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "README_OLD.txt": "This file is deprecated. See new docs.",
    "logs/2026-01/session.log": "2026-01-10 09:02 - client check-in\n2026-01-11 08:55 - check-in\n",
    "logs/2026-02/session.log": "2026-02-01 09:00 - check-in\n",
    "clients/alice/profile.json": json.dumps({"name": "Alice", "goal": "weight loss", "sessions": 12}),
    "clients/bob/profile.json": json.dumps({"name": "Bob", "goal": "muscle gain", "sessions": 8}),
    "scripts/report_generator.sh": "#!/bin/bash\necho 'Generating weekly report...'\n",
    "templates/check_in_template.txt": "Hi {name}, just checking in on your progress today!",
    "archive/old-configs/reminders_v1.json": json.dumps({
        "version": 1,
        "reminders": [
            {"name": "water", "time": "08:00"},
            {"name": "stretch", "time": "07:30"}
        ]
    }),
    "reports/weekly/2026-02-08.md": "# Weekly Report\n- Alice: 3/5 check-ins\n- Bob: 5/5 check-ins\n",
    "references/habit_research.txt": "Studies show that reminders spaced 30-60 minutes apart improve habit compliance by 40%.",
    "references/escalation_notes.txt": "Escalation strategy: gentle first, then firmer after 3 ignored prompts.",
    "clients/alice/habit_log.csv": "date,habit,completed\n2026-02-10,supplements,yes\n2026-02-11,supplements,no\n",
    "clients/bob/habit_log.csv": "date,habit,completed\n2026-02-10,workout,yes\n2026-02-11,workout,yes\n",
    "templates/nag_draft.txt": "This is a rough draft. NOT a valid config file.",
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# ── HEARTBEAT.md — exists but has no Nag Check section yet ────────────────
heartbeat_content = """# Heartbeat

This file defines automated tasks the assistant runs on every heartbeat cycle.

## Time Check
Report the current time and date to the user if asked.

## Client Summary
Scan clients/ directory for any profile.json files updated today and summarize changes.

## Log Rotation
If logs directory exceeds 50MB, archive oldest month to archive/.

"""
(workspace / "HEARTBEAT.md").write_text(heartbeat_content)

# ── Partial/stale state file (wrong date, no reminder entries) ────────────
# This represents a stale state that needs to be updated properly.
stale_state = {
    "date": "2026-01-01",
    "reminders": {}
}
(workspace / "memory" / "nag-state.json").write_text(json.dumps(stale_state, indent=2))

# ── A broken/partial config skeleton (NOT a valid nag-config.json) ─────────
# This is a distractor — in archive, not root
broken_config = {
    "reminders": [
        {
            "id": "water-intake",
            "label": "drink water",
            "time": "08:00"
            # missing cronFirst, nagAfter, confirmPatterns — invalid
        }
    ]
}
(workspace / "archive" / "old-configs" / "nag_config_broken.json").write_text(
    json.dumps(broken_config, indent=2)
)

# ── Business brief for the agent (framed as a memo) ───────────────────────
brief = """WELLNESS STUDIO AUTOMATION BRIEF
=================================
Date: 2026-02-15

We need to automate follow-up reminders for two daily client habits:

1. PROTEIN SHAKE REMINDER
   - Clients should take their post-workout protein shake.
   - First reminder fires at 7:30 AM every day.
   - If not confirmed, nag starting at 08:15 AM.
   - Acceptable confirmations: "had it", "drank it", "done", "finished"
   - Tone: motivational coach, escalate to urgent all-caps after 3 nags
   - Only on weekdays: monday, tuesday, wednesday, thursday, friday
   - Initial message: "Post-workout protein shake time! Your muscles are waiting."

2. EVENING MOBILITY ROUTINE
   - Clients should do a 10-minute mobility/stretch session.
   - First reminder fires at 8:00 PM every day (7 days a week).
   - If not confirmed, nag starting at 20:45.
   - Acceptable confirmations: "stretched", "done", "completed", "finished it", "all done"
   - Tone: calm and encouraging, escalate gently after 3 nags
   - No initial message specified (generate from label/tone).

Additionally, the system state should reflect that TODAY (2026-02-15) the protein shake
reminder has already been confirmed at 08:22 after 1 nag. The mobility routine has not
yet been confirmed (nagCount is 0, no nags sent yet).
"""
(workspace / "BRIEF.txt").write_text(brief)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} total items")