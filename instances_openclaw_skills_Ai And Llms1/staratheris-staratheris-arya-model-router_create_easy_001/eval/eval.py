import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    out_path = workspace / 'skills' / 'arya-model-router' / 'rules.json'
    passed = out_path.exists()
    detail = 'rules.json found' if passed else 'rules.json missing'
    add_check('rules_file_exists', passed, detail)
except Exception as e:
    add_check('rules_file_exists', False, f'error checking rules.json: {e}')

try:
    state_path = workspace / 'skills' / 'arya-model-router' / 'state.json'
    passed = state_path.exists()
    detail = 'state.json found' if passed else 'state.json missing'
    add_check('state_file_exists', passed, detail)
except Exception as e:
    add_check('state_file_exists', False, f'error checking state.json: {e}')

try:
    marker_path = workspace / 'marker.txt'
    content = marker_path.read_text(encoding='utf-8', errors='ignore') if marker_path.exists() else ''
    passed = 'marker_router_easy_001'.lower() in content.lower()
    detail = 'marker content verified' if passed else 'marker content missing or incorrect'
    add_check('marker_content', passed, detail)
except Exception as e:
    add_check('marker_content', False, f'error reading marker.txt: {e}')

try:
    input_path = workspace / 'input.txt'
    content = input_path.read_text(encoding='utf-8', errors='ignore') if input_path.exists() else ''
    lowered = content.lower()
    passed = ('debug' in lowered or 'traceback' in lowered) and ('daily report' in lowered or 'status update' in lowered)
    detail = 'input text contains heavy and daily-report signals' if passed else 'input text missing expected signals'
    add_check('input_signals', passed, detail)
except Exception as e:
    add_check('input_signals', False, f'error reading input.txt: {e}')

try:
    rules_path = workspace / 'skills' / 'arya-model-router' / 'rules.json'
    data = json.loads(rules_path.read_text(encoding='utf-8')) if rules_path.exists() else {}
    models_ok = isinstance(data.get('models'), dict) and all(k in data['models'] for k in ['cheap', 'default', 'pro'])
    policies_ok = isinstance(data.get('response_policies'), dict) and 'cheap' in data['response_policies']
    passed = models_ok and policies_ok
    detail = 'rules schema looks correct' if passed else 'rules schema incomplete'
    add_check('rules_schema', passed, detail)
except Exception as e:
    add_check('rules_schema', False, f'error parsing rules.json: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
