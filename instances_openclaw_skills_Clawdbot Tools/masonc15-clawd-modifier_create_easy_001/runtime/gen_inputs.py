from pathlib import Path
import json

workspace = Path('.')
(workspace / 'markers').mkdir(exist_ok=True)

# Deterministic marker files for evaluation
(workspace / 'markers' / 'clawd_task_marker.txt').write_text(
    'CLAWD_TASK_MARKER\nEXPECTED_COLOR=blue\nEXPECTED_VARIANT=with-arms\n',
    encoding='utf-8'
)

(workspace / 'input_spec.json').write_text(
    json.dumps({
        'task': 'customize clawd',
        'target_color': 'blue',
        'target_variant': 'with-arms',
        'marker': 'CLAWD_TASK_MARKER'
    }, indent=2),
    encoding='utf-8'
)
