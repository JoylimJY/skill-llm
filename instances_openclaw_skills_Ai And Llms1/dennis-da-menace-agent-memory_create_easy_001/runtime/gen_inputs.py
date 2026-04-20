from pathlib import Path
import json

# Deterministic input marker files
Path('session_notes.txt').write_text(
    'MARKER_SESSION=alpha\n'
    'FACT_1=The project name is Aurora\n'
    'FACT_2=The preferred language is Python\n'
    'LESSON_1=Always save memory at the end of the session\n'
    'ENTITY_1=Taylor|person|role=engineer\n',
    encoding='utf-8'
)

Path('task_manifest.json').write_text(
    json.dumps({
        'marker': 'MEMORY_TASK_V1',
        'facts': ['project name', 'preferred language'],
        'lesson': 'save memory at the end',
        'entity': {'name': 'Taylor', 'type': 'person'}
    }, indent=2),
    encoding='utf-8'
)
