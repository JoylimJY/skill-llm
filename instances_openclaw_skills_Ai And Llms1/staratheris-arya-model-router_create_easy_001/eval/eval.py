import json
import os
from pathlib import Path


def normalize(text):
    try:
        return ''.join(ch.lower() for ch in str(text) if ch.isalnum())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


workspace = Path(os.environ.get('1', '.'))
checks = []

# Check 1: output exists
try:
    out_path = workspace / 'output.json'
    if out_path.exists():
        checks.append({'name': 'output_exists', 'passed': True, 'detail': 'output.json found'})
    else:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.json is missing'})
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking file: {e}'})

# Check 2: valid line-delimited JSON with required fields
parsed = []
try:
    text, err = safe_read(workspace / 'output.json')
    if text is None:
        checks.append({'name': 'output_parse', 'passed': False, 'detail': f'cannot read output.json: {err}'})
    else:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        ok = True
        detail = f'{len(lines)} non-empty lines'
        for idx, line in enumerate(lines):
            try:
                obj = json.loads(line)
                parsed.append(obj)
                for key in ['input_file', 'level', 'model', 'actions']:
                    if key not in obj:
                        ok = False
                        detail = f'line {idx+1} missing key {key}'
                        break
            except Exception as e:
                ok = False
                detail = f'line {idx+1} invalid json: {e}'
                break
        checks.append({'name': 'output_schema', 'passed': ok, 'detail': detail})
except Exception as e:
    checks.append({'name': 'output_schema', 'passed': False, 'detail': f'error parsing output: {e}'})

# Check 3: expected number of records and marker-related correspondence
try:
    manifest_text, err = safe_read(workspace / 'manifest.json')
    expected_count = 3
    if manifest_text is not None:
        try:
            manifest = json.loads(manifest_text)
            expected_count = int(manifest.get('count', 3))
        except Exception:
            pass
    count_ok = len(parsed) == expected_count
    checks.append({'name': 'record_count', 'passed': count_ok, 'detail': f'found {len(parsed)}, expected {expected_count}'})
except Exception as e:
    checks.append({'name': 'record_count', 'passed': False, 'detail': f'error evaluating count: {e}'})

# Check 4: at least one obvious routing distinction
try:
    levels = [normalize(obj.get('level', '')) for obj in parsed]
    has_cheap = any('cheap' in lvl for lvl in levels)
    has_pro_or_default = any(('pro' in lvl) or ('default' in lvl) for lvl in levels)
    passed = has_cheap and has_pro_or_default
    checks.append({'name': 'level_variation', 'passed': passed, 'detail': f'levels={levels}'})
except Exception as e:
    checks.append({'name': 'level_variation', 'passed': False, 'detail': f'error checking levels: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
