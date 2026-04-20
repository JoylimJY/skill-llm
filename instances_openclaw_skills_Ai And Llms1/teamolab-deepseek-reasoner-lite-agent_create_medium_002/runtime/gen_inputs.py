from pathlib import Path
import json

base = Path('.')
(base / 'source_notes.txt').write_text(
    'MARKER_ALPHA\n'
    'Creator focus: concise educational content\n'
    'Preferred style: clear, practical, and friendly\n'
    'Core themes: writing, planning, editing, and delivery\n'
    'Audience: people who want actionable guidance\n'
    'Notable phrase: make complex ideas easy to use\n',
    encoding='utf-8'
)

(base / 'reference_tags.json').write_text(
    json.dumps({
        'seed': 4242,
        'tags': ['writing', 'planning', 'editing', 'delivery', 'education']
    }, indent=2),
    encoding='utf-8'
)
