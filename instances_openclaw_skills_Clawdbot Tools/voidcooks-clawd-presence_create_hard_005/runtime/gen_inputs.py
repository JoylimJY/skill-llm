from pathlib import Path
import json
import random

random.seed(20240517)

root = Path('.')
assets = root / 'assets' / 'monograms'
assets.mkdir(parents=True, exist_ok=True)

# Marker file for evaluation
marker = root / 'task_marker.txt'
marker.write_text('CLAWD-PRESENCE-DEMO-MARKER\nseed=20240517\nexpected_letter=N\nexpected_name=NOVA\n', encoding='utf-8')

# Minimal custom monogram for N with marker content
monogram_n = assets / 'N.txt'
monogram_n.write_text(
    'N   N\n'
    'NN  N\n'
    'N N N\n'
    'N  NN\n'
    'N   N\n'
    'marker:NOVA-N\n',
    encoding='utf-8'
)

# Extra monogram files to make the workspace realistic
monogram_a = assets / 'A.txt'
monogram_a.write_text('  A  \n A A \nAAAAA\nA   A\nA   A\n', encoding='utf-8')
monogram_z = assets / 'Z.txt'
monogram_z.write_text('ZZZZZ\n   Z \n  Z  \n Z   \nZZZZZ\n', encoding='utf-8')

# Seed a small instruction/note file used by the user request
note = root / 'presence_plan.txt'
note.write_text(
    'Transition plan:\n'
    '1. idle -> work\n'
    '2. work -> think\n'
    '3. think -> alert\n'
    '4. alert -> idle\n'
    'Final target: idle with message cleared\n',
    encoding='utf-8'
)

# Provide an expected config template marker for deterministic verification
config_template = root / 'expected_config.json'
config_template.write_text(json.dumps({
    'letter': 'N',
    'name': 'NOVA',
    'idle_timeout': 720,
    'marker': 'clawd-presence-demo'
}, indent=2), encoding='utf-8')
