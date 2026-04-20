from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

(base / 'inputs' / 'brief.txt').write_text(
    'Project codename: Orion-R2\n'
    'Release target: 2025-06-15\n'
    'Priority actions:\n'
    '- finalize API schema\n'
    '- verify deployment checklist\n'
    '- update changelog\n'
    'Marker: [[DOC-MARK-7F3A]]\n',
    encoding='utf-8'
)

(base / 'inputs' / 'notes.md').write_text(
    '# Notes\n\n'
    'The summary should stay short.\n'
    'Prefer the two most important actions only.\n',
    encoding='utf-8'
)

(base / 'inputs' / 'metadata.json').write_text(
    json.dumps({
        'owner': 'team-zenith',
        'confidence': 0.98,
        'markers': ['[[DOC-MARK-7F3A]]']
    }, indent=2),
    encoding='utf-8'
)
