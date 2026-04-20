import json
from pathlib import Path

base = Path('.')
workspace = base / 'workspace'
workspace.mkdir(parents=True, exist_ok=True)

memory_dir = workspace / 'memory' / 'clawdbot-sync'
memory_dir.mkdir(parents=True, exist_ok=True)

peers = {
    'peers': [
        {
            'name': 'lab-mac',
            'host': '100.64.18.22',
            'user': 'clawdbot',
            'path': '/Users/clawdbot/clawd',
            'workspace': '$WORKSPACE',
            'marker': 'SYNC-MARKER-ALPHA-4812'
        }
    ]
}
config = {
    'dry_run_default': True,
    'conflict_resolution': 'newest-wins',
    'marker': 'SYNC-CONFIG-MARKER-2049'
}
history = {
    'entries': [
        {
            'id': 'hist-001',
            'peer': 'lab-mac',
            'action': 'bootstrap',
            'timestamp': '2025-01-14T09:00:00Z',
            'note': 'SYNC-HISTORY-MARKER-7731'
        }
    ]
}

(workspace / 'README.txt').write_text(
    'Workspace for clawdbot sync task.\nMarker: TASK-WORKSPACE-MARKER-9001\n',
    encoding='utf-8'
)
(memory_dir / 'peers.json').write_text(json.dumps(peers, indent=2), encoding='utf-8')
(memory_dir / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
(memory_dir / 'history.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
