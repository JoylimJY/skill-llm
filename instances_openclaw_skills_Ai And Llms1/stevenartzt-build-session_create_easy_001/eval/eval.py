import json
import os
import re
import sys
from pathlib import Path

checks = []

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    output_path = workspace / 'build_session_note.txt'
    if not output_path.exists():
        add_check('output_exists', False, 'build_session_note.txt is missing')
    else:
        try:
            text = output_path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            add_check('output_exists', False, f'Could not read build_session_note.txt: {e}')
            text = ''

        normalized = re.sub(r'[^a-z0-9]+', ' ', text.lower())

        quick_check_ok = all(token in normalized for token in ['quick check', 'urgent messages', 'blocker', 'current date time'])
        add_check('quick_check_section', quick_check_ok, 'Found quick check markers' if quick_check_ok else 'Missing one or more quick check items')

        one_thing_ok = any(token in normalized for token in ['pick one thing', 'chosen task', 'one thing', 'ship this session'])
        add_check('picked_one_thing', one_thing_ok, 'Found a task-selection section' if one_thing_ok else 'No clear single-task selection found')

        log_ok = all(token in normalized for token in ['log it', 'what i built', 'key insights'])
        add_check('log_section', log_ok, 'Found log-style section' if log_ok else 'Missing log section markers')

        length_ok = len(text.strip()) > 80
        add_check('non_trivial_content', length_ok, 'Note has sufficient content' if length_ok else 'Note content is too short')
except Exception as e:
    add_check('fatal_error', False, f'Unexpected evaluator error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks) and len(checks) > 0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
