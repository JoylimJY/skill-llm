from pathlib import Path
import json

base = Path('.')
(base / 'memory').mkdir(parents=True, exist_ok=True)
(base / 'memory' / 'clawdbot-sync').mkdir(parents=True, exist_ok=True)

payload = {
    'peers': [
        {
            'name': 'laptop',
            'host': '100.64.12.34',
            'user': 'alice',
            'path': '/workspace/clawd',
            'marker': 'SYNC_MARKER_LAPTOP_001'
        }
    ],
    'status': 'pending'
}

(base / 'memory' / 'clawdbot-sync' / 'peers.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
(base / 'memory' / 'clawdbot-sync' / 'history.json').write_text(json.dumps({'events': ['SYNC_MARKER_HISTORY_001']}, indent=2), encoding='utf-8')
(base / 'input_marker.txt').write_text('SYNC_MARKER_INPUT_ABC123\n', encoding='utf-8')
