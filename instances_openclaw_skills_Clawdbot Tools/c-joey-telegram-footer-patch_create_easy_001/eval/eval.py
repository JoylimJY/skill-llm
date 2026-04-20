import json
import os
import re
import sys
from pathlib import Path

checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, e


try:
    workspace = Path(sys.argv[1]).resolve()
except Exception as e:
    workspace = Path('.').resolve()
    add_check('workspace_argument', False, f'Could not parse workspace argument: {e}')

# Check 1: output file exists
out_path = workspace / 'task_summary.txt'
try:
    if out_path.exists() and out_path.is_file():
        add_check('output_exists', True, 'task_summary.txt exists')
    else:
        add_check('output_exists', False, 'task_summary.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'Error while checking file existence: {e}')

# Check 2: content contains required phrase (fuzzy, case-insensitive)
try:
    text = None
    if out_path.exists():
        try:
            text = out_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('content_readable', False, f'Could not read task_summary.txt: {e}')
    if text is not None:
        norm = re.sub(r'\s+', ' ', text).strip().lower()
        phrase = 'telegram private-chat footer'.lower()
        passed = phrase in norm.replace('–', '-').replace('—', '-')
        add_check('contains_phrase', passed, 'Found required phrase' if passed else f'Missing phrase: {phrase}')
except Exception as e:
    add_check('contains_phrase', False, f'Exception while checking phrase: {e}')

# Check 3: file is short and summary-like
try:
    if out_path.exists():
        try:
            text = out_path.read_text(encoding='utf-8', errors='replace')
            words = re.findall(r'\b\w+\b', text)
            passed = 5 <= len(words) <= 60
            add_check('reasonable_length', passed, f'Word count = {len(words)}' if text else 'Empty file')
        except Exception as e:
            add_check('reasonable_length', False, f'Could not inspect length: {e}')
    else:
        add_check('reasonable_length', False, 'task_summary.txt missing, cannot assess length')
except Exception as e:
    add_check('reasonable_length', False, f'Exception while checking length: {e}')

# Check 4: reference input marker exists for traceability
try:
    marker_path = workspace / 'seed_marker.txt'
    if marker_path.exists():
        marker_text = marker_path.read_text(encoding='utf-8', errors='replace')
        passed = 'telegram private-chat footer'.lower() in marker_text.lower()
        add_check('input_marker_present', passed, 'Marker file contains required phrase' if passed else 'Marker file missing required phrase')
    else:
        add_check('input_marker_present', False, 'seed_marker.txt missing')
except Exception as e:
    add_check('input_marker_present', False, f'Exception while checking marker: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
