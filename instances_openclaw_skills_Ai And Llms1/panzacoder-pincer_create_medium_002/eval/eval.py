import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    out_path = workspace / 'output.txt'
    if not out_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
        text = ''
    else:
        text = out_path.read_text(encoding='utf-8', errors='replace')
        add_check('output_exists', True, 'output.txt found')
except Exception as e:
    text = ''
    add_check('output_exists', False, f'failed to read output.txt: {e}')

norm = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()

try:
    topics = ['security-first', 'scan', 'install', 'audit']
    found = [t for t in topics if t.replace('-', ' ') in norm or t in norm]
    passed = len(found) >= 4
    add_check('core_topics', passed, f'found topics: {found}')
except Exception as e:
    add_check('core_topics', False, f'error checking topics: {e}')

try:
    risk_terms = ['clean', 'caution', 'danger', 'malware', 'blocked']
    found = [t for t in risk_terms if t in norm]
    passed = len(found) >= 3
    add_check('risk_levels_mentioned', passed, f'found risk terms: {found}')
except Exception as e:
    add_check('risk_levels_mentioned', False, f'error checking risk levels: {e}')

try:
    words = norm.split()
    word_count = len(words)
    passed = 20 <= word_count <= 120
    add_check('length_reasonable', passed, f'word_count={word_count}')
except Exception as e:
    add_check('length_reasonable', False, f'error checking length: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}))
