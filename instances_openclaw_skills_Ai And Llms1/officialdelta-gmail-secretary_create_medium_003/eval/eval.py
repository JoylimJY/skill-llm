import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

try:
    inbox_dir = workspace / 'inbox'
    files = sorted(inbox_dir.glob('*.json'))
    checks.append({
        'name': 'inbox_input_files_exist',
        'passed': len(files) >= 6,
        'detail': f'Found {len(files)} JSON input files.'
    })
except Exception as e:
    checks.append({'name': 'inbox_input_files_exist', 'passed': False, 'detail': f'Error reading inputs: {e}'})

try:
    target = workspace / 'triage_result.json'
    if not target.exists():
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'triage_result.json is missing.'})
    else:
        data = json.loads(target.read_text(encoding='utf-8'))
        checks.append({'name': 'output_exists', 'passed': True, 'detail': 'triage_result.json found.'})
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'Could not read output: {e}'})
    data = None

# Expected fuzzy signals
expected = {
    'm1': ['needs reply', 'school'],
    'm2': ['read later'],
    'm3': ['clubs'],
    'm4': ['admin', 'accounts'],
    'm5': ['school'],
    'm6': ['clubs'],
}

try:
    if isinstance(data, dict):
        items = data.get('items') or data.get('messages') or data.get('results') or []
        by_id = {}
        for item in items:
            try:
                key = str(item.get('id') or item.get('messageId') or '').strip()
                if key:
                    by_id[key] = item
            except Exception:
                pass
        matched = 0
        for mid, labels in expected.items():
            item = by_id.get(mid)
            ok = False
            detail = 'missing'
            if item:
                lbls = item.get('labels') or [item.get('label')] if item.get('label') else []
                norm = ' '.join(str(x).lower() for x in lbls if x)
                ok = all(re.search(r'\b' + re.escape(lab.lower().replace(' / ', ' ').replace('/', ' ')) + r'\b', norm) for lab in labels)
                detail = f"labels={lbls}"
            checks.append({'name': f'label_{mid}', 'passed': ok, 'detail': detail})
            matched += int(ok)
        score_hint = matched / max(1, len(expected))
    else:
        for mid in expected:
            checks.append({'name': f'label_{mid}', 'passed': False, 'detail': 'No parseable output object.'})
        score_hint = 0.0
except Exception as e:
    checks.append({'name': 'label_validation', 'passed': False, 'detail': f'Validation error: {e}'})
    score_hint = 0.0

try:
    drafts = workspace / 'drafts' / 'reply_drafts.json'
    if drafts.exists():
        txt = drafts.read_text(encoding='utf-8').lower()
        has_marker = any(m in txt for m in ['marker_admissions_offer_8q2', 'marker_account_verify_c7'])
        checks.append({'name': 'drafts_created', 'passed': has_marker, 'detail': 'Draft file present with marker content.' if has_marker else 'Draft file present but markers not detected.'})
    else:
        checks.append({'name': 'drafts_created', 'passed': False, 'detail': 'reply_drafts.json is missing.'})
except Exception as e:
    checks.append({'name': 'drafts_created', 'passed': False, 'detail': f'Could not inspect drafts: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / max(1, len(checks))
passed = all(c.get('passed') for c in checks)

print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
