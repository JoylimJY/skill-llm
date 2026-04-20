from pathlib import Path
import json
import os
import random

random.seed(1337)
base = Path('.')
workspace = base / 'workspace'
workspace.mkdir(exist_ok=True)

# Marker files for deterministic verification
memory_dir = workspace / 'memory' / 'clawdbot-sync'
memory_dir.mkdir(parents=True, exist_ok=True)

peers = {
    'mac-mini': {
        'host': '100.95.193.55',
        'user': 'clawdbot',
        'path': '/Users/clawdbot/clawd',
        'workspace': '$WORKSPACE'
    },
    'server': {
        'host': '100.89.48.26',
        'user': 'clawdbot',
        'path': '/home/clawdbot/clawd',
        'workspace': '$WORKSPACE'
    }
}

config = {
    'sync_mode': 'bi-directional',
    'merge_logs': True,
    'skip_identity': True,
    'skip_config': True,
    'marker': 'SYNC_MARKER_ALPHA_7741'
}

history = [
    {'ts': '2025-01-01T00:00:00Z', 'peer': 'mac-mini', 'action': 'diff', 'files': 3},
    {'ts': '2025-01-02T00:00:00Z', 'peer': 'mac-mini', 'action': 'push', 'files': 2},
]

(memory_dir / 'peers.json').write_text(json.dumps(peers, indent=2, sort_keys=True), encoding='utf-8')
(memory_dir / 'config.json').write_text(json.dumps(config, indent=2, sort_keys=True), encoding='utf-8')
(memory_dir / 'history.json').write_text(json.dumps(history, indent=2, sort_keys=True), encoding='utf-8')
(memory_dir / 'README.marker.txt').write_text('MARKER:SYNC_MARKER_ALPHA_7741\nEXPECTED_PEER:mac-mini\n', encoding='utf-8')

# Additional workspace files that should be preserved by the task solution.
(workspace / 'MEMORY.md').write_text('Local memory root. Marker: KEEP_LOCAL_IDENTITY\n', encoding='utf-8')
(workspace / 'IDENTITY.md').write_text('Instance identity must not be synced. Marker: IDENTITY_LOCKED\n', encoding='utf-8')
(workspace / 'USER.md').write_text('User profile marker: USER_PROFILE_551\n', encoding='utf-8')

# Deterministic peer-like sample data
sample = workspace / 'memory' / '2025-01-26.md'
sample.parent.mkdir(parents=True, exist_ok=True)
sample.write_text('''# Sync Note\n\nPeer: mac-mini\nMarker: SYNC_NOTE_2025_01_26\nFiles changed: 4\n''', encoding='utf-8')
