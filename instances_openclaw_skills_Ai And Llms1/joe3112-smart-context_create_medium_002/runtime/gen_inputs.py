import json
from pathlib import Path

root = Path('.')
(root / 'source').mkdir(exist_ok=True)

(root / 'source' / 'brief.txt').write_text(
    'Project Orion\nStatus: active\nOwner: Team Blue\nMarker: ORION-2025-ALPHA\nNotes: prioritize low token usage and deterministic outputs.\n',
    encoding='utf-8'
)

(root / 'source' / 'metrics.csv').write_text(
    'metric,value\ncoverage,87\nlatency_ms,143\nerrors,2\nmarker,CSV-MARK-19\n',
    encoding='utf-8'
)

(root / 'source' / 'facts.json').write_text(
    json.dumps({
        'release': 'v2.4.1',
        'region': 'us-east',
        'marker': 'JSON-MARK-77',
        'flags': ['stable', 'audit-ready']
    }, indent=2),
    encoding='utf-8'
)
