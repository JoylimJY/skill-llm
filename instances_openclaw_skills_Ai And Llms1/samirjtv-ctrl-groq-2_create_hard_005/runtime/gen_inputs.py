from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')
base.mkdir(parents=True, exist_ok=True)

records = []
for i in range(12):
    records.append({
        'id': f'rec_{i:02d}',
        'group': 'alpha' if i % 3 == 0 else 'beta' if i % 3 == 1 else 'gamma',
        'value': (i * 7 + 11) % 50,
        'note': f'normal-{i}'
    })

# Embedded markers for evaluation
records.extend([
    {'id': 'marker_a', 'group': 'alpha', 'value': 91, 'note': 'MARKER_ALPHA_91'},
    {'id': 'marker_b', 'group': 'beta', 'value': 84, 'note': 'MARKER_BETA_84'},
    {'id': 'marker_c', 'group': 'gamma', 'value': 77, 'note': 'MARKER_GAMMA_77'},
])

with open(base / 'input.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

with open(base / 'instructions.txt', 'w', encoding='utf-8') as f:
    f.write('Compute the sum of values for marker_* records and report the per-group maximum value.\n')
    f.write('Use the exact marker notes in your summary.\n')
