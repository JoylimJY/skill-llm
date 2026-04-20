import json
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

try:
    out = workspace / 'output.txt'
    exists = out.exists()
    checks.append({
        'name': 'output_exists',
        'passed': bool(exists),
        'detail': 'output.txt found' if exists else 'output.txt is missing'
    })
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output.txt: {e}'})

try:
    marker = workspace / 'marker.json'
    data = json.loads(marker.read_text(encoding='utf-8')) if marker.exists() else {}
    ok = isinstance(data, dict) and 'marker' in data and 'MODEL_GUARD_TEST' in str(data.get('marker', '')).upper()
    checks.append({
        'name': 'marker_present',
        'passed': bool(ok),
        'detail': f"marker={data.get('marker')}" if data else 'marker.json missing or unreadable'
    })
except Exception as e:
    checks.append({'name': 'marker_present', 'passed': False, 'detail': f'error parsing marker.json: {e}'})

try:
    status = workspace / 'status.txt'
    text = status.read_text(encoding='utf-8') if status.exists() else ''
    lowered = ' '.join(text.lower().split())
    ok = 'google-antigravity usage' in lowered and '85% left' in lowered
    checks.append({
        'name': 'status_marker_verified',
        'passed': bool(ok),
        'detail': 'status marker verified' if ok else 'status.txt missing required marker content'
    })
except Exception as e:
    checks.append({'name': 'status_marker_verified', 'passed': False, 'detail': f'error reading status.txt: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
