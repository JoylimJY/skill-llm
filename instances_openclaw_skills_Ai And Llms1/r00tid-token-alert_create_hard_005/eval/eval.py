from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    out_json = workspace / 'output' / 'token_alert_report.json'
    if out_json.exists():
        try:
            data = json.loads(out_json.read_text(encoding='utf-8'))
            ok = isinstance(data, dict)
            detail = 'JSON parsed successfully' if ok else 'Output JSON is not an object'
        except Exception as e:
            ok = False
            detail = f'Could not parse JSON: {type(e).__name__}'
    else:
        ok = False
        detail = 'Missing output/token_alert_report.json'
    add_check('json_report_exists_and_parses', ok, detail)
except Exception as e:
    add_check('json_report_exists_and_parses', False, f'Unexpected error: {type(e).__name__}')

try:
    report_path = workspace / 'output' / 'token_alert_report.json'
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding='utf-8'))
            text = json.dumps(data, ensure_ascii=False).lower()
            markers = ['token-alert-2025-05-marker', '75', '90', '95']
            found = [m for m in markers if m.lower() in text]
            ok = len(found) >= 3
            detail = f'Found markers: {found}' if found else 'Expected marker content not found'
        except Exception as e:
            ok = False
            detail = f'Could not inspect JSON content: {type(e).__name__}'
    else:
        ok = False
        detail = 'Missing report file'
    add_check('report_contains_marker_content', ok, detail)
except Exception as e:
    add_check('report_contains_marker_content', False, f'Unexpected error: {type(e).__name__}')

try:
    cfg = workspace / 'output' / 'alert_config.yaml'
    if cfg.exists():
        try:
            text = cfg.read_text(encoding='utf-8')
            norm = re.sub(r'[^a-z0-9%]+', ' ', text.lower())
            needed = ['75', '90', '95']
            ok = all(x in norm for x in needed)
            detail = 'Thresholds present' if ok else f'Missing one of thresholds: {needed}'
        except Exception as e:
            ok = False
            detail = f'Could not read config: {type(e).__name__}'
    else:
        ok = False
        detail = 'Missing output/alert_config.yaml'
    add_check('alert_config_contains_thresholds', ok, detail)
except Exception as e:
    add_check('alert_config_contains_thresholds', False, f'Unexpected error: {type(e).__name__}')

try:
    status = workspace / 'output' / 'status.txt'
    if status.exists():
        try:
            text = status.read_text(encoding='utf-8').lower()
            patterns = ['high warning', '78', '156,000', '44k']
            ok = sum(1 for p in patterns if p.lower() in text) >= 3
            detail = 'Status report looks consistent' if ok else 'Status report missing expected phrases'
        except Exception as e:
            ok = False
            detail = f'Could not read status: {type(e).__name__}'
    else:
        ok = False
        detail = 'Missing output/status.txt'
    add_check('status_report_present', ok, detail)
except Exception as e:
    add_check('status_report_present', False, f'Unexpected error: {type(e).__name__}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
