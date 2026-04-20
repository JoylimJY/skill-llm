import json
import os
from pathlib import Path

workspace = Path(os.environ.get('WORKSPACE', '.'))
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    out_path = workspace / 'output.txt'
    if not out_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
    else:
        text = out_path.read_text(encoding='utf-8', errors='replace')
        norm = ' '.join(text.lower().split())
        add_check('output_exists', True, 'output.txt found')
        add_check('mentions_keyboard', 'keyboard' in norm, 'contains the word keyboard' if 'keyboard' in norm else 'missing keyboard')
        add_check('under_80_words', len(text.split()) <= 80, f'word_count={len(text.split())}')
        add_check('friendly_tone', any(w in norm for w in ['friendly', 'fun', 'great', 'easy', 'smooth', 'enjoy']), 'tone appears friendly/energetic' if any(w in norm for w in ['friendly', 'fun', 'great', 'easy', 'smooth', 'enjoy']) else 'tone not detected')
except Exception as e:
    add_check('evaluation_error', False, f'exception: {type(e).__name__}: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = len(checks) > 0 and passed_count == len(checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
