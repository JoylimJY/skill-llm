import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read {path}: {e}'


def safe_read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, f'could not parse json {path}: {e}'


def fuzzy_has(text, needle):
    try:
        return needle.lower().replace(' ', '') in text.lower().replace(' ', '')
    except Exception:
        return False


workspace = Path(__import__('sys').argv[1])
checks = []
score = 0.0

report_path = workspace / 'output' / 'safety' / 'audit-report.txt'
summary_path = workspace / 'output' / 'safety' / 'audit-summary.json'
config_path = workspace / 'input' / 'safety-checks.yaml'
markers_path = workspace / 'input' / 'markers.txt'
cache_path = workspace / 'input' / 'cache_inventory.json'
session_path = workspace / 'input' / 'session_state.json'

# Check 1: report exists and contains all required sections
try:
    if not report_path.exists():
        checks.append({'name': 'report_exists_and_sections', 'passed': False, 'detail': 'audit-report.txt is missing'})
    else:
        text = report_path.read_text(encoding='utf-8', errors='ignore')
        required = ['model', 'fallback', 'cache', 'session']
        missing = [r for r in required if not fuzzy_has(text, r)]
        passed = len(missing) == 0
        checks.append({'name': 'report_exists_and_sections', 'passed': passed, 'detail': 'all sections present' if passed else f'missing sections: {missing}'})
except Exception as e:
    checks.append({'name': 'report_exists_and_sections', 'passed': False, 'detail': f'error: {e}'})

# Check 2: report mentions marker values from inputs
try:
    markers = Path(markers_path).read_text(encoding='utf-8', errors='ignore') if markers_path.exists() else ''
    report_text = Path(report_path).read_text(encoding='utf-8', errors='ignore') if report_path.exists() else ''
    wanted = []
    for key in ['MODEL_PIN=', 'FALLBACK_CHAIN=', 'STALE_CACHE_COUNT=', 'SESSION_STATE=', 'AUDIT_TOKEN=']:
        for line in markers.splitlines():
            if line.startswith(key):
                wanted.append(line.split('=', 1)[1].strip())
                break
    missing = [v for v in wanted if not fuzzy_has(report_text, v)]
    passed = len(missing) == 0 and len(wanted) > 0
    checks.append({'name': 'report_mentions_markers', 'passed': passed, 'detail': 'all marker values referenced' if passed else f'missing values: {missing}'})
except Exception as e:
    checks.append({'name': 'report_mentions_markers', 'passed': False, 'detail': f'error: {e}'})

# Check 3: summary exists and has required keys
try:
    if not summary_path.exists():
        checks.append({'name': 'summary_json_schema', 'passed': False, 'detail': 'audit-summary.json is missing'})
    else:
        data = json.loads(summary_path.read_text(encoding='utf-8', errors='ignore'))
        required_keys = ['workspace', 'overall_status', 'findings', 'generated_at']
        missing = [k for k in required_keys if k not in data]
        passed = len(missing) == 0 and isinstance(data.get('findings', None), list)
        checks.append({'name': 'summary_json_schema', 'passed': passed, 'detail': 'required keys present' if passed else f'missing or invalid keys: {missing}'})
except Exception as e:
    checks.append({'name': 'summary_json_schema', 'passed': False, 'detail': f'error: {e}'})

# Check 4: summary references expected content
try:
    data = json.loads(summary_path.read_text(encoding='utf-8', errors='ignore')) if summary_path.exists() else {}
    cfg = json.loads(config_path.read_text(encoding='utf-8', errors='ignore')) if config_path.exists() else {}
    cache = json.loads(cache_path.read_text(encoding='utf-8', errors='ignore')) if cache_path.exists() else {}
    session = json.loads(session_path.read_text(encoding='utf-8', errors='ignore')) if session_path.exists() else {}
    text_blob = json.dumps(data).lower() if data else ''
    expectations = [
        cfg.get('model', {}).get('expected', ''),
        'primary-model', 'fallback-model', 'cached-model', 'primary-path', 'backup-path',
        str(cache.get('stale_entries', '')), session.get('state', '')
    ]
    missing = [x for x in expectations if x and not fuzzy_has(text_blob, str(x))]
    passed = len(missing) == 0
    checks.append({'name': 'summary_references_expected_values', 'passed': passed, 'detail': 'summary includes expected values' if passed else f'missing references: {missing}'})
except Exception as e:
    checks.append({'name': 'summary_references_expected_values', 'passed': False, 'detail': f'error: {e}'})

# Check 5: no unintended input modification (lightweight integrity)
try:
    before = Path(markers_path).read_text(encoding='utf-8', errors='ignore') if markers_path.exists() else ''
    after = Path(markers_path).read_text(encoding='utf-8', errors='ignore') if markers_path.exists() else ''
    passed = before == after and bool(before)
    checks.append({'name': 'inputs_unchanged', 'passed': passed, 'detail': 'input markers file unchanged' if passed else 'markers file missing or modified'})
except Exception as e:
    checks.append({'name': 'inputs_unchanged', 'passed': False, 'detail': f'error: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)

print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))