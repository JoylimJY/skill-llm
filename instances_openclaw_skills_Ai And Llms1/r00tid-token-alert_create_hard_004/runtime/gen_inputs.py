from pathlib import Path
import json

base = Path('.')
marker = 'TOKEN_ALERT_MARKER_7F3A'

session_data = {
    'session_name': 'deep-work-session',
    'token_limit': 200000,
    'tokens_used': 156000,
    'marker': marker,
    'notes': 'Deterministic input for token alert task.'
}

(base / 'session_report.json').write_text(json.dumps(session_data, indent=2), encoding='utf-8')
(base / 'README_INPUT.txt').write_text(
    'Session report generated for evaluation.\n'
    f'MARKER={marker}\n'
    'Expected thresholds: 75, 90, 95.\n',
    encoding='utf-8'
)
