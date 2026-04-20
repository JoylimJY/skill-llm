from pathlib import Path
import json

workspace = Path('.')
(workspace / 'markers').mkdir(exist_ok=True)

# Deterministic marker file for evaluation
marker = {
    'project': 'tokenguard-easy-create',
    'seed': 1337,
    'required_limit': 25.0,
    'session_name': 'clean-start'
}
(workspace / 'markers' / 'task_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
