from pathlib import Path
import json

# Deterministic marker file for evaluation context
Path('task_marker.json').write_text(json.dumps({
    'marker': 'wolfram-alpha-hard-001',
    'query': 'integrate (3x^2 - 4x + 1) from x=0 to x=5',
    'expected_numeric_result': 85
}, indent=2), encoding='utf-8')
