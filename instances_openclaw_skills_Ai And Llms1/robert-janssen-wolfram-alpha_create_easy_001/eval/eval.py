import json
import os
import re
import sys
from pathlib import Path

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    workspace = Path(sys.argv[1])
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "argument_parse", "passed": False, "detail": f"bad arguments: {e}"}]}))
    raise SystemExit(0)

# Check 1: output file exists
try:
    output_path = workspace / 'output.txt'
    if output_path.exists() and output_path.is_file():
        add_check('output_exists', True, 'output.txt found')
    else:
        add_check('output_exists', False, 'output.txt is missing')
        content = ''
except Exception as e:
    add_check('output_exists', False, f'error checking output file: {e}')
    content = ''

# Check 2: content contains the expected exact result in a forgiving way
try:
    if 'content' not in locals() or not content:
        try:
            content = output_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            content = ''
            add_check('content_read', False, f'could not read output.txt: {e}')
    normalized = re.sub(r'[^0-9a-zA-Z\\./\-]+', ' ', content).lower()
    # Accept common equivalent forms of 9 exactly
    patterns = [r'\b9\b', r'\b9\.0\b', r'\bexactly\s+9\b']
    passed = any(re.search(p, normalized) for p in patterns)
    add_check('correct_answer', passed, f'normalized output: {normalized[:200]}')
except Exception as e:
    add_check('correct_answer', False, f'error validating answer: {e}')

# Check 3: single-line answer preferred
try:
    if 'content' not in locals() or not content:
        try:
            content = output_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            content = ''
            add_check('single_line', False, f'could not read output.txt: {e}')
    lines = [ln for ln in content.splitlines() if ln.strip()]
    passed = len(lines) == 1
    add_check('single_line', passed, f'non-empty lines: {len(lines)}')
except Exception as e:
    add_check('single_line', False, f'error checking line count: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
passed = passed_count == len(checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}))