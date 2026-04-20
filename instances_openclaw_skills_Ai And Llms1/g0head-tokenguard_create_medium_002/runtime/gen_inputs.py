from pathlib import Path
import json

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

limit = {
    'current_limit_usd': 20.0,
    'warning_pct': 0.8,
    'marker': 'TOKENGUARD_LIMIT_MARKER_ALPHA_7421'
}
session = {
    'date': '2025-05-01',
    'spent_usd': 12.34,
    'marker': 'TOKENGUARD_SESSION_MARKER_BETA_9183',
    'entries': [
        {'amount_usd': 4.23, 'description': 'Claude Sonnet - code review'},
        {'amount_usd': 8.11, 'description': 'GPT-4o-mini - test synthesis'}
    ]
}

(root / 'inputs' / 'limit.json').write_text(json.dumps(limit, indent=2), encoding='utf-8')
(root / 'inputs' / 'session.json').write_text(json.dumps(session, indent=2), encoding='utf-8')
(root / 'inputs' / 'README.txt').write_text(
    'Marker file for TokenGuard task.\n'
    'Look for TOKENGUARD_LIMIT_MARKER_ALPHA_7421 and TOKENGUARD_SESSION_MARKER_BETA_9183.\n',
    encoding='utf-8'
)
