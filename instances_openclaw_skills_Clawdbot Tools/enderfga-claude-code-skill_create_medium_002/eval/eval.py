import json
from pathlib import Path
import sys

workspace = Path(sys.argv[1])
checks = []

def add_check(name, condition, detail):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})

try:
    marker = workspace / 'task_marker.txt'
    add_check('marker_exists', marker.exists(), 'task_marker.txt should exist')
    if marker.exists():
        try:
            text = marker.read_text(encoding='utf-8', errors='replace')
            ok = 'openclaw_task_marker' in text.lower()
            add_check('marker_content', ok, 'task marker text should contain the expected marker')
        except Exception as e:
            add_check('marker_content', False, f'Could not read task_marker.txt: {e}')
    else:
        add_check('marker_content', False, 'task_marker.txt missing')
except Exception as e:
    add_check('marker_checks', False, f'Unexpected error: {e}')

try:
    session_file = workspace / 'session_seed.json'
    add_check('session_seed_exists', session_file.exists(), 'session_seed.json should exist')
    if session_file.exists():
        try:
            data = json.loads(session_file.read_text(encoding='utf-8', errors='replace'))
            marker_ok = str(data.get('marker', '')).lower() == 'openclaw_session_marker'
            sessions = data.get('sessions', [])
            session_ok = isinstance(sessions, list) and len(sessions) >= 2
            add_check('session_marker', marker_ok, 'session marker should be present')
            add_check('session_count', session_ok, 'session list should contain at least two items')
        except Exception as e:
            add_check('session_json_valid', False, f'Could not parse session_seed.json: {e}')
    else:
        add_check('session_json_valid', False, 'session_seed.json missing')
except Exception as e:
    add_check('session_checks', False, f'Unexpected error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks
}
print(json.dumps(result, ensure_ascii=False))
