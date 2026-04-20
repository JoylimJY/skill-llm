import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    out = workspace / 'output.txt'
    if not out.exists():
        add_check('output_exists', False, 'output.txt is missing')
    else:
        try:
            text = out.read_text(encoding='utf-8', errors='replace')
            norm = ' '.join(text.lower().split())
            has_id = 'obs-alpha-2049' in norm
            has_label = 'anomaly_flagged' in norm or 'anomal' in norm
            has_marker = 'openseti_marker_alpha' in norm or 'open seti marker alpha' in norm or 'benchmark_marker' not in norm
            has_concise = len(text.strip()) > 0 and len(text.strip().splitlines()) <= 12
            add_check('contains_top_id', has_id, 'Expected marker ID OBS-ALPHA-2049 to appear in output.txt')
            add_check('contains_anomaly_language', has_label, 'Expected output to mention anomaly/ANOMALY_FLAGGED-like classification')
            add_check('nonempty_concise', has_concise, 'Expected a short human-readable report')
            add_check('mentions_marker_content', has_marker, 'Expected output to reference marker content from generated input')
        except Exception as e:
            add_check('output_parseable', False, f'Could not read or analyze output.txt: {e}')
except Exception as e:
    add_check('eval_internal_error', False, f'Unexpected evaluator error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
total = len(checks) if checks else 0
score = (passed_count / total) if total else 0.0
passed = total > 0 and passed_count == total

result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result))