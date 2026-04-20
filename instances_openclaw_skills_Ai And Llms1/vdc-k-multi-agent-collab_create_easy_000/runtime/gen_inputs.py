from pathlib import Path
import json

base = Path('.')
(base / 'seed_marker.txt').write_text('AGENT_SYNC_MARKER::ALPHA_NOTES::2025-05', encoding='utf-8')
(base / 'project_name.txt').write_text('alpha-notes', encoding='utf-8')
(base / 'starter_tasks.json').write_text(json.dumps({
    'project': 'alpha-notes',
    'tasks': ['Draft initial docs', 'Record first decision', 'Prepare weekly report']
}, indent=2), encoding='utf-8')
