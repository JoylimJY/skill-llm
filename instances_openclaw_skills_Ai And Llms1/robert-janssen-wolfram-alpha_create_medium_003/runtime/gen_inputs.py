from pathlib import Path
import json
import random

random.seed(42)

# Main data file with embedded marker content
lines = [
    'project: alpha-study',
    'marker: WOLFRAM_VERIFICATION_TOKEN_7F3A',
    'samples: 12',
    'measurements: 4.5, 7.2, 6.1, 8.4, 5.9, 9.0',
    'notes: values collected under controlled conditions',
]
Path('input.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')

# Auxiliary JSON data with deterministic values
payload = {
    'title': 'Alpha Study Data',
    'marker': 'WOLFRAM_VERIFICATION_TOKEN_7F3A',
    'values': [3, 5, 8, 13],
    'scale_factor': 2,
}
Path('data.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
