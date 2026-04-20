from pathlib import Path
import json

root = Path('.')
(root / 'tasks').mkdir(parents=True, exist_ok=True)
(root / 'memory').mkdir(parents=True, exist_ok=True)

queue = '''# Task Queue

## Ready
- [ ] Write a short onboarding checklist

## In Progress
- [ ] @kai: Draft autonomy overview

## Blocked
- [ ] Publish team update (needs: approval)

## Done Today
- [x] Create initial task queue marker
'''
(root / 'tasks' / 'QUEUE.md').write_text(queue, encoding='utf-8')

heartbeat = '''# Heartbeat Routine

## Quick Checks
- [ ] Check for urgent human messages
- [ ] Check for blockers

## Work Mode
1. Read `tasks/QUEUE.md`
2. Pick one Ready task
3. Do the work
4. Update the queue and log progress
'''
(root / 'HEARTBEAT.md').write_text(heartbeat, encoding='utf-8')

marker = {
    'marker': 'AUTONOMY_KIT_DEMO',
    'files': ['tasks/QUEUE.md', 'HEARTBEAT.md']
}
(root / 'memory' / 'seed.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
