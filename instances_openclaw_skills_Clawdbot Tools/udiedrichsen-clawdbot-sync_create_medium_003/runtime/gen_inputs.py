from pathlib import Path
import json

base = Path('.')
ws = base / 'workspace'
(ws / 'memory' / 'clawdbot-sync').mkdir(parents=True, exist_ok=True)
(ws / 'memory').mkdir(parents=True, exist_ok=True)

marker = {
    'marker': 'CLAWDBOT_SYNC_MARKER_9417',
    'workspace': 'workspace',
    'peer_name': 'office-peer',
    'peer_host': '100.64.12.34',
    'peer_user': 'clawdbot',
    'peer_path': '/home/clawdbot/clawd',
    'workspace_var': '$WORKSPACE'
}

(ws / 'memory' / 'README.txt').write_text('marker=' + marker['marker'] + '\n', encoding='utf-8')
(ws / 'memory' / 'clawdbot-sync' / 'peers.json').write_text(json.dumps({'peers': []}, indent=2) + '\n', encoding='utf-8')
(ws / 'memory' / 'clawdbot-sync' / 'history.json').write_text(json.dumps({'entries': []}, indent=2) + '\n', encoding='utf-8')
(ws / 'memory' / 'clawdbot-sync' / 'config.json').write_text(json.dumps({'auto_sync': False, 'sync_identity': False, 'include_skills': True}, indent=2) + '\n', encoding='utf-8')
(ws / 'memory' / 'IDENTITY.md').write_text('instance identity marker: keep-separate\n', encoding='utf-8')
(ws / 'memory' / 'USER.md').write_text('user profile marker: persistent\n', encoding='utf-8')
