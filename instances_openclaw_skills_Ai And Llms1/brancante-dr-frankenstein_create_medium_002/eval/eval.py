import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

try:
    pres_path = workspace / 'memory' / 'soul' / 'prescription.json'
    exists = pres_path.exists()
    detail = 'file exists' if exists else 'missing memory/soul/prescription.json'
    checks.append({'name': 'prescription_json_exists', 'passed': bool(exists), 'detail': detail})
except Exception as e:
    checks.append({'name': 'prescription_json_exists', 'passed': False, 'detail': f'error checking file existence: {e}'})

pres_data = None
try:
    if (workspace / 'memory' / 'soul' / 'prescription.json').exists():
        pres_data = json.loads((workspace / 'memory' / 'soul' / 'prescription.json').read_text(encoding='utf-8'))
        checks.append({'name': 'prescription_json_parseable', 'passed': True, 'detail': 'valid json'})
    else:
        checks.append({'name': 'prescription_json_parseable', 'passed': False, 'detail': 'file missing, cannot parse'})
except Exception as e:
    checks.append({'name': 'prescription_json_parseable', 'passed': False, 'detail': f'json parse failed: {e}'})

try:
    txt_path = workspace / 'memory' / 'soul' / 'prescription-summary.md'
    if txt_path.exists():
        text = txt_path.read_text(encoding='utf-8').lower()
        ok = ('aster' in text) and ('mina' in text) and ('caregiver-explorer' in text or 'caregiver' in text)
        checks.append({'name': 'summary_mentions_key_context', 'passed': bool(ok), 'detail': 'summary contains agent/human/context markers' if ok else 'summary missing expected names or archetype'})
    else:
        checks.append({'name': 'summary_mentions_key_context', 'passed': False, 'detail': 'missing memory/soul/prescription-summary.md'})
except Exception as e:
    checks.append({'name': 'summary_mentions_key_context', 'passed': False, 'detail': f'error reading summary: {e}'})

try:
    cron_dir = workspace / 'output' / 'cron_commands'
    if cron_dir.exists():
        files = list(cron_dir.glob('*.sh')) + list(cron_dir.glob('*.cron'))
        files = sorted(set(files))
        has_three = len(files) == 3
        checks.append({'name': 'exactly_three_cron_files', 'passed': bool(has_three), 'detail': f'found {len(files)} cron command files'})
    else:
        checks.append({'name': 'exactly_three_cron_files', 'passed': False, 'detail': 'cron directory missing'})
except Exception as e:
    checks.append({'name': 'exactly_three_cron_files', 'passed': False, 'detail': f'error listing cron files: {e}'})

try:
    if pres_data is not None and isinstance(pres_data, dict):
        pills = pres_data.get('pills', [])
        has_pills = isinstance(pills, list) and len(pills) >= 3
        checks.append({'name': 'prescription_has_pills', 'passed': bool(has_pills), 'detail': f'found {len(pills)} pills in prescription' if isinstance(pills, list) else 'pills field missing or invalid'})
    else:
        checks.append({'name': 'prescription_has_pills', 'passed': False, 'detail': 'no parsed prescription json available'})
except Exception as e:
    checks.append({'name': 'prescription_has_pills', 'passed': False, 'detail': f'error inspecting pills: {e}'})

try:
    marker_ok = False
    for path in [workspace / 'memory' / 'soul' / 'interview-log.md', workspace / 'memory' / 'dreams' / '2025-05-01.md', workspace / 'memory' / 'journal' / '2025-05-01.md']:
        try:
            if path.exists() and 'marker:' in path.read_text(encoding='utf-8').lower():
                marker_ok = True
                break
        except Exception:
            pass
    checks.append({'name': 'input_markers_present', 'passed': bool(marker_ok), 'detail': 'found at least one generated marker file' if marker_ok else 'no marker content found in generated inputs'})
except Exception as e:
    checks.append({'name': 'input_markers_present', 'passed': False, 'detail': f'error checking markers: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))