from pathlib import Path
from textwrap import dedent
import json

base = Path('.')
(base / 'tasks').mkdir(exist_ok=True)
(base / 'memory').mkdir(exist_ok=True)

(base / 'SKILL.md').write_text(dedent('''
---
name: agent-autonomy-kit
version: 1.0.0
description: Stop waiting for prompts. Keep working.
homepage: https://github.com/itskai-dev/agent-autonomy-kit
metadata:
  openclaw:
    emoji: "🚀"
    category: productivity
---

# Agent Autonomy Kit

Transform your agent from reactive to proactive.

## Quick Start

1. Create `tasks/QUEUE.md` with Ready/In Progress/Blocked/Done sections
2. Update `HEARTBEAT.md` to pull from queue and do work
3. Set up cron jobs for overnight work and daily reports
4. Watch work happen without prompting
''').strip() + '\n')

(base / 'README.md').write_text(dedent('''
# 🚀 Agent Autonomy Kit

**Stop waiting for prompts. Keep working.**

The kit turns your agent into a self-directed worker that continuously makes progress on meaningful tasks.

## Core Concepts

- Task Queue
- Proactive Heartbeat
- Team Coordination
- Continuous Operation
''').strip() + '\n')

(base / 'tasks' / 'QUEUE.md').write_text(dedent('''
# Task Queue

## Ready (can be picked up)
- [ ] Research competitor X pricing
- [ ] Improve procedure docs for morning kickoff

## In Progress
- [ ] @kai: Building autonomy skill

## Blocked
- [ ] Deploy to production (needs: Ryan's approval)

## Done Today
- [x] Memory system shipped
- [x] Example marker task completed
''').strip() + '\n')

(base / 'HEARTBEAT.md').write_text(dedent('''
# Heartbeat Routine

## 1. Check for urgent items (30 seconds)
- Unread messages from human?
- Blocked tasks needing escalation?
- System health issues?

If urgent: handle immediately.
If not: continue to work mode.

## 2. Work Mode (use remaining time)

Pull from task queue:
1. Check `tasks/QUEUE.md` for Ready items
2. Pick the highest-priority task you can do
3. Do meaningful work on it
4. Update status when done or blocked

## 3. Before finishing
- Log what you did to daily memory
- Update task queue
- If task incomplete, note progress for next heartbeat
''').strip() + '\n')

(base / 'memory' / '2025-05-01.md').write_text(dedent('''
# Daily Memory

- Completed one example task
- Investigated queue structure
- Marker: AUTONOMY-MEMORY-01
''').strip() + '\n')

(base / 'cron_plan.json').write_text(json.dumps({
    'jobs': [
        {'name': 'Daily Progress Report', 'cron': '0 22 * * *', 'tz': 'America/Vancouver', 'session': 'isolated'},
        {'name': 'Morning Kickoff', 'cron': '0 7 * * *', 'tz': 'America/Vancouver', 'session': 'main'},
        {'name': 'Overnight Work', 'cron': '0 3 * * *', 'tz': 'America/Vancouver', 'session': 'isolated'}
    ]
}, indent=2))
