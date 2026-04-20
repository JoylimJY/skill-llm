from pathlib import Path
import json
import random

random.seed(1337)

workspace = Path('.')
(workspace / 'input_data').mkdir(exist_ok=True)

# Marker file 1
marker1 = {
    'skill': 'clawface',
    'marker': 'CLAWFACE_MARKER_ALPHA_913',
    'sequence': ['thinking', 'searching', 'coding', 'success']
}
(workspace / 'input_data' / 'clawface_markers.json').write_text(json.dumps(marker1, indent=2), encoding='utf-8')

# Marker file 2
lines = [
    'OpenClaw visual feedback test fixture',
    'Marker: CLAWFACE_MARKER_BETA_481',
    'Expected mode: robot',
    'Expected effect: confetti',
]
(workspace / 'input_data' / 'usage_notes.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# Deterministic pseudo-random token file
letters = 'abcdefghijklmnopqrstuvwxyz'
token = ''.join(random.choice(letters) for _ in range(12))
(workspace / 'input_data' / 'token.txt').write_text(f'TOKEN={token}\nMARKER=CLAWFACE_MARKER_GAMMA_204\n', encoding='utf-8')
