import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        # 加上 , None
        return Path(path).read_text(encoding='utf-8', errors='ignore'), None 
    except Exception as e:
        return None, str(e)

# Check 1: output.txt exists
try:
    out_path = workspace / 'output.txt'
    if out_path.exists():
        add_check('output_exists', True, 'output.txt found')
    else:
        add_check('output_exists', False, 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'exception: {e}')

# Check 2: contains marker phrase
try:
    text = None
    err = None
    if (workspace / 'output.txt').exists():
        text, err = safe_read(workspace / 'output.txt')
    if text is None:
        add_check('marker_present', False, f'could not read output.txt: {err}')
    else:
        normalized = re.sub(r'\s+', ' ', text).lower()
        marker = 'deepseek_v3_lite_agent_ready'.lower()
        add_check('marker_present', marker in normalized, 'marker phrase found' if marker in normalized else 'marker phrase not found')
except Exception as e:
    add_check('marker_present', False, f'exception: {e}')

# Check 3: under length limit
try:
    if (workspace / 'output.txt').exists():
        text, err = safe_read(workspace / 'output.txt')
        if text is None:
            add_check('length_limit', False, f'could not read output.txt: {err}')
        else:
            passed = len(text.split()) <= 220
            add_check('length_limit', passed, f'word_count={len(text.split())}')
    else:
        add_check('length_limit', False, 'output.txt missing')
except Exception as e:
    add_check('length_limit', False, f'exception: {e}')

# Check 4: required section headings roughly present
try:
    required = ['overview', 'features', 'usage', 'notes']
    if (workspace / 'output.txt').exists():
        text, err = safe_read(workspace / 'output.txt')
        if text is None:
            add_check('sections_present', False, f'could not read output.txt: {err}')
        else:
            normalized = re.sub(r'[^a-z0-9\n ]+', ' ', text.lower())
            found = [sec for sec in required if sec in normalized]
            passed = len(found) == len(required)
            add_check('sections_present', passed, f'found={found}')
    else:
        add_check('sections_present', False, 'output.txt missing')
except Exception as e:
    add_check('sections_present', False, f'exception: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": all(c['passed'] for c in checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
