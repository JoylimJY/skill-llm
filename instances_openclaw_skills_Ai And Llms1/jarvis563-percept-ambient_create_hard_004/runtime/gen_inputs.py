from pathlib import Path
import json

root = Path('.')
(root / 'data').mkdir(exist_ok=True)

conversations = [
    {
        'id': 'c001',
        'timestamp': '2025-05-01T09:00:00Z',
        'speaker': 'Avery',
        'text': 'Avery and Jordan agreed that Project Lumen is for Northstar Labs and the deadline is Friday.'
    },
    {
        'id': 'c002',
        'timestamp': '2025-05-01T10:15:00Z',
        'speaker': 'Jordan',
        'text': 'Jordan mentioned that Northstar Labs wants a privacy review before launch. Avery will draft notes.'
    },
    {
        'id': 'c003',
        'timestamp': '2025-05-01T11:30:00Z',
        'speaker': 'Mina',
        'text': 'Mina said Project Lumen depends on the ambient dashboard and the search index being ready.'
    }
]

(root / 'data' / 'conversations.json').write_text(json.dumps(conversations, indent=2), encoding='utf-8')
(root / 'data' / 'marker.txt').write_text('MARKER_PERCEPT_42\n', encoding='utf-8')
