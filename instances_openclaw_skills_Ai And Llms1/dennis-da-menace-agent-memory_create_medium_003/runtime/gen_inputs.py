from pathlib import Path
import json
import random

random.seed(1337)

workspace = Path('.')

markers = {
    'session_name': 'atlas-session-42',
    'person_name': 'Mina Park',
    'project_name': 'Project Juniper',
    'fact_1': 'Marker fact: prefers concise notes.',
    'fact_2': 'Marker fact: uses the default memory DB.',
    'lesson_1': 'Marker lesson: retry failed imports once.',
    'entity_role': 'research engineer',
}

input_data = {
    'session': markers['session_name'],
    'person': markers['person_name'],
    'project': markers['project_name'],
    'facts': [markers['fact_1'], markers['fact_2']],
    'lesson': markers['lesson_1'],
    'entity': {
        'name': markers['person_name'],
        'type': 'person',
        'attributes': {'role': markers['entity_role']}
    }
}

(workspace / 'memory_input.json').write_text(json.dumps(input_data, indent=2), encoding='utf-8')
(workspace / 'task_marker.txt').write_text(
    '\n'.join([
        'MEMORY_TASK_MARKER',
        markers['session_name'],
        markers['person_name'],
        markers['project_name'],
        markers['fact_1'],
        markers['fact_2'],
        markers['lesson_1'],
    ]),
    encoding='utf-8'
)
