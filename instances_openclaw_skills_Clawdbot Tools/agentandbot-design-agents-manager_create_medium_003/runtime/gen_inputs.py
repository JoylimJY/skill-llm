from pathlib import Path
import json
import random

random.seed(42)
base = Path('.')

(base / 'task_seed.txt').write_text('TASK-REF: SAP-ROUTER-ALPHA-17\nMARKER: internal-routing-update\n', encoding='utf-8')

registry_hint = {
    'human_owner': 'Ilkerkaan',
    'parent_agent': 'main',
    'preferred_language': ['tr', 'en'],
    'task_code': 'SAP-ROUTER-ALPHA-17'
}
(base / 'registry_hint.json').write_text(json.dumps(registry_hint, indent=2), encoding='utf-8')

(base / 'notes.txt').write_text(
    'Marker: do not invent unrelated agents.\n'
    'The new agent should be specialized for SAP routing and escalation.\n'
    'Use the task code from task_seed.txt exactly once in the card.\n',
    encoding='utf-8'
)
