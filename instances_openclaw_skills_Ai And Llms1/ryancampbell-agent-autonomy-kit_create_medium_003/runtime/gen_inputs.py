from pathlib import Path

base = Path('.')
(base / 'tasks').mkdir(exist_ok=True)
(base / 'memory').mkdir(exist_ok=True)

(base / 'SKILL.md').write_text('''---
name: agent-autonomy-kit
version: 1.0.0
description: Stop waiting for prompts. Keep working.
homepage: https://github.com/itskai-dev/agent-autonomy-kit
metadata:
  openclaw:
    emoji: "🚀"
    category: productivity
---
''', encoding='utf-8')

(base / 'tasks' / 'QUEUE.md').write_text('''# Task Queue

## Ready
- [ ] Review team handoff notes
- [ ] Draft tomorrow's priorities
- [ ] Check for stale blocked items

## In Progress
- [ ] @agent: improve heartbeat workflow

## Blocked
- [ ] Deploy demo changes (needs approval)

## Done Today
- [x] AUTONOMY DEMO READY
''', encoding='utf-8')

(base / 'HEARTBEAT.md').write_text('''# Heartbeat Routine

## Quick Checks
- [ ] Human messages waiting?
- [ ] Critical blockers?

## Work Mode
1. Read `tasks/QUEUE.md`
2. Pick the highest-priority Ready task
3. Do meaningful work
4. Update queue and memory

## End of Heartbeat
- Log progress to `memory/2025-05-15.md`
- Share a concise update if work changed
''', encoding='utf-8')

(base / 'memory' / '2025-05-15.md').write_text('''# Daily Memory — 2025-05-15

## Completed
- Updated task queue structure
- Refined heartbeat routine for proactive work
- AUTONOMY DEMO READY

## Next
- Pull the top Ready task from `tasks/QUEUE.md`
- Resolve the blocked deployment once approval arrives
- Add any new discoveries back into the queue
''', encoding='utf-8')
