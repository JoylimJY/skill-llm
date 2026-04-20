from pathlib import Path
import json

root = Path('.')
assets = root / 'assets' / 'monograms'
assets.mkdir(parents=True, exist_ok=True)

# Deterministic marker-rich monogram file
mono = [
    'OOO-MARKER-START',
    'O   O',
    'O   O   ORION-MONOGRAM',
    'O   O',
    'OOO-MARKER-END',
]
(assets / 'O.txt').write_text('\n'.join(mono) + '\n', encoding='utf-8')

# Provide a pre-existing state file with known marker content for evaluation.
state = {
    'state': 'work',
    'message': 'initial marker payload',
    'updated': 1700000000.0,
}
(root / 'state.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')

# Seed a config file that the task should update.
config = {
    'letter': 'A',
    'name': 'AGENT',
    'idle_timeout': 300,
    'marker': 'config-seed-marker'
}
(root / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
