from pathlib import Path
import json

# Deterministic marker-rich input files
Path('workspace').mkdir(exist_ok=True)
Path('workspace/notes.txt').write_text(
    'CLAWD_CUSTOMIZATION_TASK\n'
    'marker: blue_and_arms\n'
    'target: small mascot\n'
    'theme: terminal mascot edit\n',
    encoding='utf-8'
)

Path('workspace/spec.json').write_text(
    json.dumps(
        {
            'task': 'change_color_and_add_arms',
            'expected_color': 'blue',
            'expected_variant': 'with-arms',
            'marker': 'blue_and_arms',
        },
        indent=2,
        sort_keys=True,
    ),
    encoding='utf-8'
)
