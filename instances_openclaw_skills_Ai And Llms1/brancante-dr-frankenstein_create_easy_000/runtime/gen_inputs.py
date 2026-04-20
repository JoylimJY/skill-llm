from pathlib import Path
import json
import random

random.seed(1337)

workspace = Path('.')
inputs = {
    'agent_profile.json': {
        'agent_name': 'Milo',
        'human_name': 'Ava',
        'patient_marker': 'MILO-DRF-001',
        'human_marker': 'AVA-DRF-001',
        'voice': 'warm, curious, gentle',
    },
    'skill_marker.txt': 'DR-FRANKENSTEIN-EASY-TASK\nmarker=2025-05\n',
}

for filename, content in inputs.items():
    path = workspace / filename
    if isinstance(content, dict):
        path.write_text(json.dumps(content, indent=2), encoding='utf-8')
    else:
        path.write_text(content, encoding='utf-8')
