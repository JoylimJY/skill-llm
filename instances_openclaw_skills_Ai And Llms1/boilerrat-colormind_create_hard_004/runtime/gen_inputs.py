from pathlib import Path
import json

Path('input').mkdir(exist_ok=True)
markers = {
    'task_id': 'colormind_hard_001',
    'expected_model': 'ui',
    'locked_colors': ['18,18,30', '92,88,184', '34,193,195'],
    'notes': 'Use only locked colors for reproducibility; no image sampling.'
}
Path('input/markers.json').write_text(json.dumps(markers, indent=2), encoding='utf-8')
Path('input/README.txt').write_text(
    'MARKER: COLORMIND_TASK\nThis directory contains deterministic task markers for evaluation.\n',
    encoding='utf-8'
)
