from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
assets = root / 'assets' / 'monograms'
assets.mkdir(parents=True, exist_ok=True)

# Deterministic marker files
(root / 'README_MARKER.txt').write_text('MARKER:CLAWD-PRESENCE-INPUT-ROOT\n', encoding='utf-8')

# Create a few deterministic monogram files with verifiable markers
letters = ['A', 'M', 'Z']
for idx, letter in enumerate(letters):
    lines = [
        f'MARKER-MONO-{letter}-TOP',
        f'  {letter}{letter}{letter}  ',
        f' {letter}   {letter} ',
        f'{letter}{letter}{letter}{letter}{letter}',
        f'  {letter} {letter}  ',
        f'MARKER-MONO-{letter}-BOTTOM',
    ]
    (assets / f'{letter}.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# Seeded reference config/state used by the eval to verify behavior
config = {
    'letter': 'M',
    'name': 'DECK',
    'idle_timeout': 123,
    'marker': 'CONFIG-MARKER-7',
}
state = {
    'state': 'think',
    'message': 'Reviewing command deck layout',
    'updated': 1700000000.0,
    'marker': 'STATE-MARKER-11',
}
(root / 'config.json').write_text(json.dumps(config, indent=2) + '\n', encoding='utf-8')
(root / 'state.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
