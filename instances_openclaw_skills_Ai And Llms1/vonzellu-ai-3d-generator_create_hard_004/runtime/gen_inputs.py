from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')
(base / 'workspace_marker.txt').write_text('AI_3D_GENERATOR_MARKER::DRONE_TASK::1337\n', encoding='utf-8')
(base / 'input_description.json').write_text(json.dumps({
    'marker': 'AI_3D_GENERATOR_MARKER::DRONE_TASK::1337',
    'request': 'high-detail sci-fi drone with rotor rings and landing skids',
    'detail_level': 'high'
}, indent=2), encoding='utf-8')
