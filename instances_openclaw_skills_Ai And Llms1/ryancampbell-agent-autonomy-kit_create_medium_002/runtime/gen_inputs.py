from pathlib import Path
from datetime import date
import json

base = Path('.')
(base / 'tasks').mkdir(parents=True, exist_ok=True)
(base / 'memory').mkdir(parents=True, exist_ok=True)

marker = {
    'project': 'agent-autonomy-kit',
    'marker': 'AUK-SEED-2025-05',
    'focus': 'proactive heartbeat and task queue'
}

(base / 'seed_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')

# Deterministic reference content for the task authoring target
(base / 'REFERENCE.md').write_text(
    '# Reference\n\nMarker: AUK-SEED-2025-05\nGoal: create queue, heartbeat, and daily memory note.\n',
    encoding='utf-8'
)

today = date(2025, 5, 1).isoformat()
(base / 'TODAY.txt').write_text(today + '\n', encoding='utf-8')
