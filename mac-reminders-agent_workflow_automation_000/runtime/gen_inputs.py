import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create distractor directory structure ---
dirs = [
    "skills/mac-reminders-agent/reminders",
    "skills/mac-reminders-agent/node_modules/applescript/lib",
    "skills/mac-reminders-agent/node_modules/commander/lib",
    "projects/sprint-planning/docs",
    "projects/sprint-planning/retrospectives",
    "team/alice",
    "team/bob",
    "team/shared/templates",
    "logs/2024",
    "logs/2025",
    "config/envs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "skills/mac-reminders-agent/package.json": json.dumps({
        "name": "mac-reminders-agent",
        "version": "1.4.0",
        "description": "macOS Reminders integration",
        "main": "cli.js",
        "dependencies": {
            "applescript": "^1.0.0",
            "commander": "^11.0.0"
        }
    }, indent=2),

    "skills/mac-reminders-agent/reminders/apple-bridge.js": """
// AppleScript bridge for Reminders access
const applescript = require('applescript');
module.exports = { listReminders, addReminder, editReminder, deleteReminder, completeReminder };
function listReminders(opts, cb) { cb(null, []); }
function addReminder(opts, cb) { cb(null, { id: 'mock' }); }
function editReminder(opts, cb) { cb(null, {}); }
function deleteReminder(opts, cb) { cb(null, {}); }
function completeReminder(opts, cb) { cb(null, {}); }
""",

    "skills/mac-reminders-agent/reminders/meeting-parser.js": """
// Meeting notes parser
module.exports = { parse };
function parse(text, locale) { return { ok: true, items: [] }; }
""",

    "skills/mac-reminders-agent/locales.json": json.dumps({
        "en": {
            "triggers": {"list": ["show reminders", "what do i have"], "add": ["add reminder", "set reminder"]},
            "labels": {"incomplete": "Incomplete Reminders", "completed": "Completed"},
            "responses": {"add_success": "Added '{title}' reminder.", "edit_success": "Updated reminder.", "delete_success": "Deleted reminder."}
        },
        "ko": {
            "triggers": {"list": ["미리알림 보여줘", "할 일 뭐 있어"], "add": ["미리알림 추가", "알림 설정"]},
            "labels": {"incomplete": "미완료 미리알림", "completed": "완료됨"},
            "responses": {"add_success": "'{title}' 미리알림을 추가했어요.", "edit_success": "미리알림을 수정했어요.", "delete_success": "미리알림을 삭제했어요."}
        }
    }, indent=2),

    "skills/mac-reminders-agent/node_modules/applescript/lib/index.js": "module.exports = {};",
    "skills/mac-reminders-agent/node_modules/commander/lib/index.js": "module.exports = {};",

    "projects/sprint-planning/docs/sprint_24_goals.md": """# Sprint 24 Goals
- Improve CI/CD pipeline
- Refactor authentication module
- Write unit tests for payment service
""",

    "projects/sprint-planning/retrospectives/retro_2025_q4.md": """# Q4 2025 Retrospective
What went well: deployment automation
What to improve: test coverage
Action items: see meeting notes
""",

    "team/alice/tasks.txt": "- Review PRs\n- Update documentation\n- Check monitoring dashboards",
    "team/bob/tasks.txt": "- Fix login bug\n- Deploy hotfix\n- Update sprint board",
    "team/shared/templates/meeting_template.md": """# Meeting Notes Template
Date: [DATE]
Attendees: [NAMES]
Action Items:
- [ ] [OWNER]: [TASK] by [DATE]
""",

    "logs/2025/app.log": "[2025-01-10] INFO: Application started\n[2025-01-10] INFO: Reminders sync completed\n",
    "logs/2024/app.log": "[2024-12-31] INFO: Year-end sync\n",
    "config/envs/production.env": "NODE_ENV=production\nLOG_LEVEL=info\n",
    "config/envs/staging.env": "NODE_ENV=staging\nLOG_LEVEL=debug\n",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- THE CORE INPUT: meeting notes file ---
meeting_notes = """Sprint 25 Planning Meeting - 2026-02-03
Attendees: Alice, Bob, Carol, Dave

== Action Items ==

1. Alice: Prepare Q1 performance report by March 20 - URGENT
   This needs to go to the board. No extensions.

2. Bob: Bi-weekly engineering standup every other Monday starting Feb 10
   Team sync at 9am, bi-weekly cadence.

3. Carol: Update API documentation deadline: February 28
   Medium priority - needs to be done before the release.

4. Dave: Schedule security audit review by February 15
   Important - compliance requirement.

== Notes ==
Budget review postponed to next quarter.
Hiring freeze lifted - Dave to coordinate with HR (no deadline).
"""

(workspace / "meeting_notes.txt").write_text(meeting_notes)

# --- Reminder added log (starts empty, mock CLI will populate) ---
(workspace / "cli_calls.log").write_text("")
(workspace / "added_reminders.json").write_text("[]")

print("Workspace initialized.")
print(f"Files created: {list(workspace.rglob('*'))}")