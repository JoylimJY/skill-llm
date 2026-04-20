from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)
marker = {
    'task_id': 'sci-fi-cargo-drone-001',
    'marker': 'OPENCLAW_3D_GEN_MARKER',
    'seed': 1337,
    'required_output': 'sci_fi_cargo_drone.stl'
}
(root / 'inputs' / 'task_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
(root / 'inputs' / 'description.txt').write_text(
    'Generate a detailed sci-fi cargo drone with ducted fans, landing gear, panel lines, and a cargo bay.',
    encoding='utf-8'
)
