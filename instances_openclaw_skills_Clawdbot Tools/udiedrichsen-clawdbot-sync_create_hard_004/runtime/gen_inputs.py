import json
import os
import random
from pathlib import Path

random.seed(1337)
base = Path('.')
work = base / 'workspace'
(work / 'memory' / 'clawdbot-sync' / 'conflicts').mkdir(parents=True, exist_ok=True)
(work / 'skills' / 'sample-skill').mkdir(parents=True, exist_ok=True)
(work / 'config').mkdir(parents=True, exist_ok=True)

marker = 'MARKER_SYNC_BUNDLE_7F3A9C'

peers = {
    'field-mac': {
        'host': '100.64.12.34',
        'user': 'clawdbot',
        'path': '/Users/clawdbot/clawd',
        'workspace': '$WORKSPACE'
    },
    'server': {
        'host': '100.64.99.18',
        'user': 'clawdbot',
        'path': '/home/clawdbot/clawd',
        'workspace': '$WORKSPACE'
    }
}

history = [
    {
        'ts': '2026-01-26T10:00:00Z',
        'peer': 'field-mac',
        'mode': 'dry-run',
        'result': 'preview-only',
        'marker': marker
    },
    {
        'ts': '2026-01-26T10:05:00Z',
        'peer': 'server',
        'mode': 'push',
        'result': 'ok',
        'marker': marker
    }
]

config = {
    'auto_sync': False,
    'conflict_policy': 'newest-wins',
    'selective_sync': ['memory', 'skills'],
    'marker': marker
}

(work / 'memory' / 'clawdbot-sync' / 'peers.json').write_text(json.dumps(peers, indent=2, sort_keys=True), encoding='utf-8')
(work / 'memory' / 'clawdbot-sync' / 'history.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
(work / 'memory' / 'clawdbot-sync' / 'config.json').write_text(json.dumps(config, indent=2, sort_keys=True), encoding='utf-8')

(work / 'memory' / 'MEMORY.md').write_text(
    '# MEMORY\n\n- Sync bundle prepared for peer field-mac.\n- Conflict policy: newest-wins.\n- Marker: ' + marker + '\n',
    encoding='utf-8'
)
(work / 'memory' / 'USER.md').write_text(
    '# USER\n\nPreferred peer name: field-mac\nPreferred sync mode: dry-run first\nMarker: ' + marker + '\n',
    encoding='utf-8'
)
(work / 'skills' / 'sample-skill' / 'SKILL.md').write_text(
    '---\nname: sample-skill\nversion: 1.0.0\n---\n\nSample skill for sync verification.\nMarker: ' + marker + '\n',
    encoding='utf-8'
)
(work / 'config' / 'local.json').write_text(
    json.dumps({'instance': 'primary', 'marker': marker}, indent=2),
    encoding='utf-8'
)

conflict_a = work / 'memory' / 'clawdbot-sync' / 'conflicts' / 'memory-2026-01-24.conflict.json'
conflict_a.write_text(json.dumps({'file': 'memory/2026-01-24.md', 'winner': 'local', 'marker': marker}, indent=2), encoding='utf-8')

print(marker)
