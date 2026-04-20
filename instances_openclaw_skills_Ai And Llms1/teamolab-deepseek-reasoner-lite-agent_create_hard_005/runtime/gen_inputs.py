from pathlib import Path
import json

base = Path('.')
(base / 'source_notes.txt').write_text(
    'PROJECT: Aurora Launch\n'
    'MARKER_ID: ALPHA-7429\n'
    'DATE_WINDOW: 2025-04-12 to 2025-04-19\n'
    'PRIMARY_GOAL: introduce the new dashboard workflow\n'
    'AUDIENCE: operations managers and team leads\n'
    'HARD_REQUIREMENT: mention the beta invitation code BETA-91X in all customer-facing copy\n'
    'STYLE: concise, confident, and practical\n',
    encoding='utf-8'
)

(base / 'facts.json').write_text(json.dumps({
    'project': 'Aurora Launch',
    'marker_id': 'ALPHA-7429',
    'beta_code': 'BETA-91X',
    'audience': ['operations managers', 'team leads'],
    'date_window': {'start': '2025-04-12', 'end': '2025-04-19'},
    'goal': 'introduce the new dashboard workflow'
}, indent=2), encoding='utf-8')
