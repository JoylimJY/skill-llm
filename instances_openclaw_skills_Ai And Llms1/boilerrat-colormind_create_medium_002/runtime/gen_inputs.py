from pathlib import Path
import json

# Deterministic marker file for evaluation context.
Path('task_marker.txt').write_text('COLORMIND_TASK_MARKER_2025_05\n', encoding='utf-8')

# Optional reference file with fixed expectations for the evaluator.
reference = {
    'model': 'ui',
    'locked': [[18, 18, 24], [88, 101, 242], None, None, None],
    'required_outputs': ['palette.json', 'palette.txt']
}
Path('reference.json').write_text(json.dumps(reference, indent=2), encoding='utf-8')
