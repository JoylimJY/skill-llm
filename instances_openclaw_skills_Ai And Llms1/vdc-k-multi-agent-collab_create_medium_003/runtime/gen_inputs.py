from pathlib import Path
import json

root = Path('.')
files = {
    'TASK.md': """# TASK

- [ ] Set up the initial Agent Sync workspace for nebula-sync
- [ ] Confirm document-driven workflow conventions

Marker: NEBULA_SYNC_MARKER
""",
    'CHANGELOG.md': """# CHANGELOG

- 2025-05-01 by claude: Initialized project scaffolding #init #nebula_sync

Marker: NEBULA_SYNC_MARKER
""",
    'CONTEXT.md': """# CONTEXT

## Decision Log
- Use TASK.md as the source of truth for active work.
- Use CHANGELOG.md for one-line updates with tags.

## Notes
- This workspace follows the Agent Sync collaboration pattern.
- Marker: NEBULA_SYNC_MARKER
""",
    'WEEKLY-REPORT.md': """# WEEKLY REPORT

## Summary
- First weekly setup for nebula-sync.

## Pattern Discovery
- Repeated operation candidate skill: updating TASK.md after each work session.
- Repeated operation candidate skill: appending tagged CHANGELOG entries.

Marker: NEBULA_SYNC_MARKER
""",
    'llms.txt': """# llms.txt

TASK.md
CHANGELOG.md
CONTEXT.md
WEEKLY-REPORT.md

NEBULA_SYNC_MARKER
""",
}
for name, content in files.items():
    Path(name).write_text(content, encoding='utf-8')
