import json
from pathlib import Path

base = Path('.')
(base / 'memory' / 'clawdbot-sync').mkdir(parents=True, exist_ok=True)

peers = {
    'peers.json': {
        'peers': [
            {
                'name': 'lab-peer',
                'host': '100.64.10.25',
                'user': 'clawdbot',
                'path': '/home/clawdbot/clawd',
                'workspace': '$WORKSPACE'
            }
        ],
        'marker': 'SYNC_MARKER_ALPHA_7'
    },
    'history.json': {
        'events': [],
        'marker': 'SYNC_HISTORY_MARKER_BETA_3'
    },
    'config.json': {
        'auto_sync': False,
        'conflict_mode': 'newest-wins',
        'marker': 'SYNC_CONFIG_MARKER_GAMMA_9'
    }
}

for name, payload in peers.items():
    (base / 'memory' / 'clawdbot-sync' / name).write_text(json.dumps(payload, indent=2), encoding='utf-8')

(base / 'README_TASK.txt').write_text(
    'Task marker: READ_ME_TASK_DELTA_11\nAdd the peer and keep the sync workspace metadata intact.\n',
    encoding='utf-8'
)
