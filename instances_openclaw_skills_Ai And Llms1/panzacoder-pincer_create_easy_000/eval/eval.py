import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    output_path = workspace / 'scan_report.json'
    if not output_path.exists():
        add_check('output_exists', False, 'scan_report.json was not found')
    else:
        try:
            data = json.loads(output_path.read_text(encoding='utf-8'))
            marker_hit = False
            text_blob = json.dumps(data, ensure_ascii=False).lower()
            marker_hit = 'safe_marker_7f3a'.lower() in text_blob
            add_check('json_parses', True, 'scan_report.json parsed successfully')
            add_check('marker_referenced', marker_hit, 'marker SAFE_MARKER_7F3A found in output' if marker_hit else 'marker SAFE_MARKER_7F3A not referenced in output')
        except Exception as e:
            add_check('json_parses', False, f'failed to parse scan_report.json: {e}')
            add_check('marker_referenced', False, 'could not inspect output because JSON parsing failed')
except Exception as e:
    add_check('output_exists', False, f'unexpected error while checking output: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks) if checks else False
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
