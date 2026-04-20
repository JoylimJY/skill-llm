import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    session_path = workspace / 'input' / 'session_data.json'
    passed = session_path.exists()
    add_check('session_data_exists', passed, 'Found session_data.json' if passed else 'session_data.json is missing')
except Exception as e:
    add_check('session_data_exists', False, f'Error while checking session_data.json: {e}')

try:
    data = {}
    session_path = workspace / 'input' / 'session_data.json'
    if session_path.exists():
        try:
            data = json.loads(session_path.read_text(encoding='utf-8'))
        except Exception as e:
            add_check('session_data_parses', False, f'Could not parse JSON: {e}')
            data = {}
    else:
        add_check('session_data_parses', False, 'session_data.json missing, cannot parse')

    used = data.get('used')
    limit = data.get('limit')
    percent = None
    try:
        if isinstance(used, (int, float)) and isinstance(limit, (int, float)) and limit:
            percent = round((used / limit) * 100, 1)
    except Exception as e:
        add_check('percentage_computation', False, f'Error computing percentage: {e}')

    expected_ok = percent is not None and 77.5 <= percent <= 78.5
    add_check('percentage_is_about_78', expected_ok, f'Computed percent={percent!r}' if percent is not None else 'Missing numeric used/limit values')
except Exception as e:
    add_check('percentage_is_about_78', False, f'Unexpected error: {e}')

try:
    marker_path = workspace / 'input' / 'README_MARKER.txt'
    if marker_path.exists():
        try:
            text = marker_path.read_text(encoding='utf-8', errors='ignore').lower()
            ok = ('token_alert_marker_high_warning' in text.replace('-', '_').replace(' ', '_')) and ('session-alert-7842' in text)
            add_check('marker_content_present', ok, 'Marker text verified' if ok else f'Marker content did not match: {text[:200]!r}')
        except Exception as e:
            add_check('marker_content_present', False, f'Could not read marker file: {e}')
    else:
        add_check('marker_content_present', False, 'README_MARKER.txt is missing')
except Exception as e:
    add_check('marker_content_present', False, f'Unexpected error: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result))
