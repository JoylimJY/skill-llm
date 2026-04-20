import json
from pathlib import Path

workspace = Path('.')
records = {
    'session_id': 'sess-0042',
    'records': [
        {'publicId': 'agent-alpha', 'verified': True, 'latencyMs': 812, 'note': 'ok'},
        {'publicId': 'agent-beta', 'verified': False, 'latencyMs': 1204, 'note': 'timeout'},
        {'publicId': 'marker-agent', 'verified': True, 'latencyMs': 666, 'note': 'MARKER::AAP::GREEN::7x6'},
        {'publicId': 'agent-gamma', 'verified': True, 'latencyMs': 905, 'note': 'ok'}
    ]
}
Path('handshakes.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
Path('README_INPUT.txt').write_text('Process handshakes.json and preserve the embedded marker exactly: MARKER::AAP::GREEN::7x6\n', encoding='utf-8')
