from pathlib import Path
import json

base = Path('.')
(base / 'README_INPUT.txt').write_text('CLAWFACE_MARKER: demo-ready\nUse this marker to verify the task input was generated deterministically.\n', encoding='utf-8')
(base / 'avatar_seed.json').write_text(json.dumps({
    'marker': 'CLAWFACE_MARKER',
    'emotion': 'happy',
    'action': 'idle',
    'effect': 'sparkles',
    'message': 'Demo input prepared.'
}, indent=2), encoding='utf-8')
