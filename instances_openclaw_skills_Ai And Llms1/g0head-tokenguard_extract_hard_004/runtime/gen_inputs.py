import json
from pathlib import Path

base = Path('.')
(base / 'tokenguard').mkdir(exist_ok=True)

session = {
    'session_date': '2025-05-17',
    'limit_usd': 20.0,
    'spent_usd': 14.23,
    'warning_threshold_pct': 0.8,
    'entries': [
        {'ts': '2025-05-17T09:12:01Z', 'amount': 2.50, 'desc': 'Claude Sonnet - code review', 'marker': 'MARKER_ALPHA'},
        {'ts': '2025-05-17T10:45:33Z', 'amount': 5.00, 'desc': 'GPT-4o - spec analysis', 'marker': 'MARKER_BETA'},
        {'ts': '2025-05-17T11:03:21Z', 'amount': 6.73, 'desc': 'Claude 3.5 Sonnet - summarization', 'marker': 'MARKER_GAMMA'}
    ]
}

limit = {
    'currency': 'USD',
    'current_limit_usd': 20.0,
    'default_limit_usd': 20.0
}

(base / 'tokenguard' / 'session.json').write_text(json.dumps(session, indent=2), encoding='utf-8')
(base / 'tokenguard' / 'limit.json').write_text(json.dumps(limit, indent=2), encoding='utf-8')
