from pathlib import Path
import json
import sys
import re

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

# Helper: find JSON files in output directory
def find_json_files(directory):
    if not directory.exists():
        return []
    return list(directory.glob('*.json'))

# 1) Required output artifact exists (any JSON file with marker)
try:
    output_dir = workspace / 'output'
    json_files = find_json_files(output_dir)
    
    status_file = None
    for jf in json_files:
        try:
            content = jf.read_text(encoding='utf-8')
            if re.search(r'token_guard_ready', content, re.IGNORECASE):
                status_file = jf
                break
        except:
            continue
    
    if status_file:
        add_check('status_json_exists', True, f'found status file: {status_file.name}')
    else:
        add_check('status_json_exists', False, 'no JSON file with TOKEN_GUARD_READY marker found in output/')
except Exception as e:
    add_check('status_json_exists', False, f'error while checking file existence: {e}')

# 2) JSON is well-formed and contains marker text
try:
    if status_file:
        data = json.loads(status_file.read_text(encoding='utf-8'))
        marker = str(data.get('marker', ''))
        passed = re.search(r'token_guard_ready', marker, re.IGNORECASE) is not None
        add_check('status_marker', passed, f'marker={marker!r}')
    else:
        add_check('status_marker', False, 'cannot inspect missing status file')
except Exception as e:
    add_check('status_marker', False, f'error parsing status file: {e}')

# 3) Must include at least one model state
try:
    if status_file:
        data = json.loads(status_file.read_text(encoding='utf-8'))
        models = data.get('models', {})
        passed = isinstance(models, dict) and len(models) >= 1
        add_check('has_model_state', passed, f'model_count={len(models) if isinstance(models, dict) else "n/a"}')
    else:
        add_check('has_model_state', False, 'cannot inspect missing status file')
except Exception as e:
    add_check('has_model_state', False, f'error inspecting models: {e}')

# 4) Usage artifact exists and includes expected model key (search any JSON file)
try:
    usage_file = None
    for jf in json_files:
        try:
            content = jf.read_text(encoding='utf-8')
            if re.search(r'gemini-3-flash', content, re.IGNORECASE):
                usage_file = jf
                break
        except:
            continue
    
    if usage_file:
        usage = json.loads(usage_file.read_text(encoding='utf-8'))
        passed = re.search(r'gemini-3-flash', json.dumps(usage, ensure_ascii=False), re.IGNORECASE) is not None
        add_check('usage_state_contains_model', passed, f'found gemini-3-flash in {usage_file.name}')
    else:
        add_check('usage_state_contains_model', False, 'no JSON file with gemini-3-flash found in output/')
except Exception as e:
    add_check('usage_state_contains_model', False, f'error inspecting usage file: {e}')

# 5) Derived score from passed checks
try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    overall_passed = all(c['passed'] for c in checks)
except Exception as e:
    score = 0.0
    overall_passed = False
    add_check('score_computation', False, f'error computing score: {e}')

result = {'passed': overall_passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))