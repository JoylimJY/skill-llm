from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)
marker = {
    'task_id': 'clawface-hard-demo-001',
    'marker': 'CLAWFACE_DETERMINISTIC_MARKER_7F3A',
    'expected_flow': ['thinking', 'speaking', 'idle']
}
(base / 'inputs' / 'marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
(base / 'inputs' / 'instructions.txt').write_text(
    'MARKER: CLAWFACE_DETERMINISTIC_MARKER_7F3A\nPlease create the avatar state output using this marker.\n',
    encoding='utf-8'
)
