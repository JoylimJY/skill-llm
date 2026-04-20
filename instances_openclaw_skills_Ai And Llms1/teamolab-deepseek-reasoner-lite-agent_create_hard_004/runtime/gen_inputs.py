from pathlib import Path
import json

Path('input').mkdir(exist_ok=True)
notes = {
    'project': 'Northstar Launch',
    'date': '2025-04-18',
    'owner': 'Mina Patel',
    'milestone': 'beta review',
    'key_points': [
        'The launch checklist is complete.',
        'Customer feedback emphasizes faster onboarding.',
        'A final demo is scheduled for Friday at 14:00 UTC.'
    ],
    'marker': 'MARKER-7F3A-DELTA'
}
Path('input/notes.json').write_text(json.dumps(notes, indent=2), encoding='utf-8')
Path('input/source.txt').write_text(
    'Northstar Launch briefing source\n'
    'Owner: Mina Patel\n'
    'Milestone: beta review\n'
    'Date: 2025-04-18\n'
    'Marker: MARKER-7F3A-DELTA\n',
    encoding='utf-8'
)
