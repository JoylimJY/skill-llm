from pathlib import Path
import json

Path('input').mkdir(exist_ok=True)

marker = {
    'session_id': 'session-2025-04-01',
    'person_name': 'Ava Chen',
    'project_name': 'Orchid'
}

Path('input/markers.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
Path('input/context.txt').write_text(
    'Marker: ORCHID-42\n'
    'Remember this stable fact for evaluation.\n'
    'Lesson context: debugging memory retrieval.\n'
    'Entity context: Ava Chen is the project engineer for Orchid.\n',
    encoding='utf-8'
)
