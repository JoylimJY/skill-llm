import json
import os
import re
from pathlib import Path

workspace = Path(os.environ.get('PWD', '.'))
checks = []
score = 0.0

try:
    target = workspace / 'output.txt'
    if not target.exists():
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
    else:
        text = ''
        try:
            text = target.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            checks.append({'name': 'output_readable', 'passed': False, 'detail': f'Could not read output.txt: {e}'})
            text = ''
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
        has_phrase = 'anti regression' in norm
        has_marker = 'marker 42' in norm
        checks.append({'name': 'contains_phrase', 'passed': has_phrase, 'detail': 'Found anti-regression phrase' if has_phrase else 'Missing anti-regression phrase'})
        checks.append({'name': 'contains_marker', 'passed': has_marker, 'detail': 'Found MARKER-42 marker' if has_marker else 'Missing MARKER-42 marker'})
except Exception as e:
    checks.append({'name': 'eval_error', 'passed': False, 'detail': f'Unexpected eval error: {e}'})

if checks:
    score = sum(1 for c in checks if c['passed']) / len(checks)
passed = bool(checks) and all(c['passed'] for c in checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
