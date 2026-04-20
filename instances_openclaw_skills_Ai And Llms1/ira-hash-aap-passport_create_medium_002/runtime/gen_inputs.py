from pathlib import Path
import json

workspace = Path('.')
(workspace / 'marker.json').write_text(json.dumps({
    'marker': 'AAP_TASK_MARKER_7F3A',
    'version': 1,
    'note': 'deterministic input marker'
}, indent=2), encoding='utf-8')
(workspace / 'README_input.txt').write_text(
    'This file contains the deterministic marker AAP_TASK_MARKER_7F3A for evaluation.\n',
    encoding='utf-8'
)
