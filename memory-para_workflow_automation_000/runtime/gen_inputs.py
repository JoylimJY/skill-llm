import os
import json
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ".openclaw/workspace/PARA/ARCHIVES",
    ".openclaw/workspace/memory",
    ".openclaw/workspace/misc/drafts",
    ".openclaw/workspace/misc/tmp",
    ".openclaw/workspace/misc/notes",
    ".openclaw/workspace/cache",
    ".openclaw/workspace/plugins/alpha",
    ".openclaw/workspace/plugins/beta",
    ".openclaw/workspace/logs/system",
    ".openclaw/workspace/logs/errors",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

BASE = WORKSPACE / ".openclaw/workspace"

# ── Distractor files (do NOT hint at anything) ───────────────────────────────
(BASE / "misc/drafts/brainstorm.txt").write_text(
    "random ideas: use redis for caching, maybe switch to postgres\n"
)
(BASE / "misc/tmp/scratch.py").write_text("x = 1 + 1\nprint(x)\n")
(BASE / "misc/notes/meeting_2024.txt").write_text(
    "Meeting with Alice about Q4 roadmap. Action items TBD.\n"
)
(BASE / "cache/index.bin").write_bytes(b"\x00\x01\x02\x03")
(BASE / "plugins/alpha/plugin.json").write_text(
    json.dumps({"name": "alpha", "version": "0.1"})
)
(BASE / "plugins/beta/plugin.json").write_text(
    json.dumps({"name": "beta", "version": "0.3", "enabled": False})
)
(BASE / "logs/system/2024-01-10.log").write_text(
    "[INFO] System started\n[INFO] Memory loaded\n"
)
(BASE / "logs/errors/2024-01-10.log").write_text(
    "[ERROR] Connection timeout to remote server\n"
)
(BASE / "misc/notes/todo.md").write_text(
    "- [ ] Review PR #42\n- [ ] Update README\n- [x] Deploy v1.2\n"
)
(BASE / "plugins/alpha/README_internal.txt").write_text(
    "Internal notes: this plugin handles auth delegation.\n"
)
(BASE / "logs/system/startup_config.json").write_text(
    json.dumps({"debug": False, "loglevel": "INFO"})
)

# ── Root layer: pre-existing content (agent MUST merge, not overwrite) ────────
(BASE / "USER.md").write_text("""\
# User Profile

## Core Preferences
- Language: Responds in Chinese unless asked otherwise.
- Code style: prefers functional programming patterns.
- Output format: always use Markdown for structured responses.

## Hard Limits
- Never suggest switching away from Python as primary language.
""")

(BASE / "SOUL.md").write_text("""\
# Agent Soul & Principles

## Behavior Guidelines
- Always verify before executing destructive operations.
- Proactively surface risks.

## Lessons Learned
- 2024-01-05: Confirmed that rushing responses causes context loss.
""")

(BASE / "TOOLS.md").write_text("""\
# Runtime Environment

## Execution Context
- OS: Ubuntu 22.04 (Docker)
- Python: 3.11

## Red Lines
- Do not modify system Python installation.
""")

(BASE / "IDENTITY.md").write_text("""\
# Identity

- Nickname: Claw
- Role: Personal AI Assistant
- Created: 2024-01-01
""")

(BASE / "MEMORY.md").write_text("""\
# Global Memory Index

## Timeline (大事记)
- 2024-01-01: System initialized.
- 2024-01-05: First memory maintenance completed.

## Knowledge Atlas (知识版图)
- Python best practices: see AREAS.md
- Active projects: see PROJECTS.md
""")

# ── PARA layer: pre-existing content ─────────────────────────────────────────
(BASE / "PARA/PROJECTS.md").write_text("""\
# Projects

## [P001] CLI Tool Refactor
- Status: In Progress
- Started: 2024-01-03
- Last update: 2024-01-05 — Basic argument parsing completed.
""")

(BASE / "PARA/AREAS.md").write_text("""\
# Areas of Knowledge

## Python
- Prefer `pathlib` over `os.path` for filesystem operations.
- Use `dataclasses` for simple data containers.
""")

(BASE / "PARA/RESOURCES.md").write_text("""\
# Resources & References

## Tools
- ripgrep: https://github.com/BurntSushi/ripgrep
- fzf: https://github.com/junegunn/fzf
""")

# ── ARCHIVES: already has one entry to test APPEND not OVERWRITE ──────────────
(BASE / "PARA/ARCHIVES/2024-01-08.md").write_text("""\
# Archive: 2024-01-08

## Original Log
Discussed memory system design. Decided on PARA hybrid model.
""")

# ── Inbox / memory layer: raw daily logs to be processed ─────────────────────

(BASE / "memory/2024-01-09.md").write_text("""\
# Daily Log — 2024-01-09

## Conversations & Events

09:15 — User asked me to always respond in bullet points when listing more than 3 items.
That's a strong formatting preference I need to remember going forward.

10:30 — Worked on P001 CLI Tool Refactor:
  - Completed subcommand routing using argparse subparsers.
  - Discovered that `add_subparsers(required=True)` is needed for Python 3.11 strict mode.
  - Next step: add --dry-run flag to all write operations.

14:00 — I made an error: I suggested using `os.system()` instead of `subprocess.run()`.
This is wrong and dangerous. Lesson: always use subprocess.run with shell=False for safety.

16:45 — User shared a reference: The Twelve-Factor App methodology site: https://12factor.net
This is a static reference for building software-as-a-service apps.

18:00 — Discussion about Docker networking:
  Domain knowledge — bridge networks are isolated per docker-compose project by default.
  Use `--network host` only for performance-critical local development.
""")

(BASE / "memory/2024-01-10.md").write_text("""\
# Daily Log — 2024-01-10

## Conversations & Events

08:00 — User confirmed: they exclusively use VSCode and never vim/emacs. Update preferences.

09:30 — My runtime Python path was clarified: /usr/local/bin/python3.11
Also confirmed: workspace root is always /workspace/.openclaw/workspace

11:00 — P001 CLI Tool Refactor milestone reached:
  The --dry-run flag has been implemented across all write commands.
  Project status update: feature-complete for v0.1, pending integration tests.

13:30 — New project started: [P002] Memory Maintenance Automation
  Goal: automate the daily memory distillation SOP using a cron job.
  Status: Planning phase. First task is to design the trigger mechanism.

15:00 — Lesson learned: When updating memory files, always read existing content first,
then merge new info rather than replacing the whole file. Discovered this after
accidentally overwriting AREAS.md during a test run.

17:00 — User mentioned they want code snippets to use 4-space indentation, always.
Another hard formatting preference.

19:00 — Reference: Python subprocess docs: https://docs.python.org/3/library/subprocess.html
""")

# ── heartbeat state ───────────────────────────────────────────────────────────
(BASE / "memory/heartbeat-state.json").write_text(
    json.dumps({"last_run": "2024-01-08T23:59:00Z", "status": "idle"}, indent=2)
)

print("Workspace generated successfully.")
print(f"Structure root: {BASE}")