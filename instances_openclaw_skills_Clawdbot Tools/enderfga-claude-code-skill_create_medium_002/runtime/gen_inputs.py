from pathlib import Path
import json

# Deterministic marker files for the task workspace
Path('task_marker.txt').write_text('OPENCLAW_TASK_MARKER: mcp-demo-001\n', encoding='utf-8')
Path('session_seed.json').write_text(json.dumps({
    'marker': 'OPENCLAW_SESSION_MARKER',
    'sessions': [
        {'id': 'local-1', 'updatedAt': 1000, 'content': 'alpha'},
        {'id': 'remote-1', 'updatedAt': 2000, 'content': 'beta'}
    ]
}, indent=2), encoding='utf-8')
