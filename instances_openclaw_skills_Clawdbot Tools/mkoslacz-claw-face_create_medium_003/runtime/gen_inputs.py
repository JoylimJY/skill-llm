from pathlib import Path
import json

base = Path('.')
(base / 'assets').mkdir(exist_ok=True)
(base / 'docs').mkdir(exist_ok=True)

# Marker files for evaluation
(base / 'docs' / 'README_MARKER.txt').write_text(
    'CLAWFACE_DEMO_MARKER\nThis file is deterministic and used for verification.\n',
    encoding='utf-8'
)

state = {
    'emotion': 'neutral',
    'action': 'idle',
    'effect': 'none',
    'message': 'Marker input ready: CLAWFACE_DEMO_MARKER'
}
(base / 'assets' / 'input_state.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')

(base / 'assets' / 'launch_notes.txt').write_text(
    'Launch target: robot mode\nCustom greeting: Hello from ClawFace\nExpected marker: CLAWFACE_DEMO_MARKER\n',
    encoding='utf-8'
)
