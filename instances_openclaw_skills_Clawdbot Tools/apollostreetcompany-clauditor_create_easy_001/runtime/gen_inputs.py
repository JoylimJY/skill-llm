from pathlib import Path
import json
import random

random.seed(42)

root = Path('.')
(root / 'input').mkdir(exist_ok=True)

marker = 'CLAUDITOR_MARKER_7F3A'
files = {
    'input/events.log': [
        {'ts': '2025-05-01T10:00:00Z', 'event': 'open', 'path': '/var/log/auth.log', 'marker': marker},
        {'ts': '2025-05-01T10:00:01Z', 'event': 'read', 'path': '/etc/sysaudit/config.toml', 'marker': marker},
        {'ts': '2025-05-01T10:00:02Z', 'event': 'write', 'path': '/var/lib/.sysd/.audit/events.log', 'marker': marker},
    ],
    'input/summary_template.json': {
        'title': 'clauditor audit summary',
        'version': 1,
        'marker': marker,
        'notes': 'Use the provided events to produce a concise summary.'
    }
}

for rel, content in files.items():
    p = root / rel
    if isinstance(content, list):
        p.write_text('\n'.join(json.dumps(x) for x in content) + '\n', encoding='utf-8')
    else:
        p.write_text(json.dumps(content, indent=2) + '\n', encoding='utf-8')

(root / 'input' / 'expected_marker.txt').write_text(marker + '\n', encoding='utf-8')
