from pathlib import Path
import json

base = Path('.')
store = base / '.tokenguard'
store.mkdir(parents=True, exist_ok=True)

limit = {
    'limit': 25.0,
    'currency': 'USD',
    'warning_pct': 0.8
}
session = {
    'date': '2025-04-18',
    'spent': 13.75,
    'entries': [
        {'amount': 4.50, 'desc': 'Claude Sonnet - planning pass', 'ts': '2025-04-18T10:00:00Z'},
        {'amount': 2.25, 'desc': 'Embeddings batch refresh', 'ts': '2025-04-18T10:30:00Z'},
        {'amount': 6.00, 'desc': 'Code review loop', 'ts': '2025-04-18T11:00:00Z'},
        {'amount': 1.00, 'desc': 'Tiny follow-up', 'ts': '2025-04-18T11:15:00Z'}
    ]
}

(store / 'limit.json').write_text(json.dumps(limit, indent=2), encoding='utf-8')
(store / 'session.json').write_text(json.dumps(session, indent=2), encoding='utf-8')

# Marker file for eval verification
(base / 'marker_tokenguard_seed.txt').write_text('TOKENGUARD-SEED-2025-04-18\nSESSION-ENTRIES=4\nTOP-ENTRY=6.00\n', encoding='utf-8')
