import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out_path = workspace / 'output' / 'optimization_report.json'

    # Check 1: file exists
    try:
        exists = out_path.exists()
        checks.append({
            'name': 'report_exists',
            'passed': bool(exists),
            'detail': 'output/optimization_report.json found' if exists else 'output/optimization_report.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'report_exists', 'passed': False, 'detail': f'Existence check failed: {e}'})

    data = None
    raw = None
    # Check 2: parseable JSON
    try:
        if out_path.exists():
            raw = out_path.read_text(encoding='utf-8')
            data = json.loads(raw)
            checks.append({'name': 'json_parseable', 'passed': True, 'detail': 'Report is valid JSON'})
        else:
            checks.append({'name': 'json_parseable', 'passed': False, 'detail': 'Cannot parse because file is missing'})
    except Exception as e:
        checks.append({'name': 'json_parseable', 'passed': False, 'detail': f'JSON parse failed: {e}'})

    # Check 3: required top-level sections with fuzzy validation
    try:
        ok = False
        detail = 'Missing required content'
        if isinstance(data, dict):
            txt = normalize(json.dumps(data, ensure_ascii=False))
            service_ok = 'checkoutapi' in txt
            summary_ok = any(k in data for k in ['summary', 'overview'])
            findings_ok = any(k in data for k in ['findings', 'bottlenecks'])
            actions_ok = any(k in data for k in ['recommended_actions', 'actions', 'recommendations'])
            rollback_ok = any(k in data for k in ['rollback_criteria', 'rollback', 'rollback_plan'])
            ok = service_ok and summary_ok and findings_ok and actions_ok and rollback_ok
            detail = f'service_ok={service_ok}, summary_ok={summary_ok}, findings_ok={findings_ok}, actions_ok={actions_ok}, rollback_ok={rollback_ok}'
        checks.append({'name': 'required_sections', 'passed': bool(ok), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'required_sections', 'passed': False, 'detail': f'Validation failed: {e}'})

    # Check 4: marker propagation from inputs
    try:
        expected_markers = ['DB-PROFILE-MARKER-7Q2', 'APP-PROFILE-MARKER-4K9', 'TARGETS-MARKER-9Z1']
        report_text = raw if isinstance(raw, str) else ''
        norm_report = normalize(report_text)
        found = []
        for m in expected_markers:
            if normalize(m) in norm_report:
                found.append(m)
        passed = len(found) >= 2
        checks.append({
            'name': 'marker_propagation',
            'passed': passed,
            'detail': f'Found markers: {found}'
        })
    except Exception as e:
        checks.append({'name': 'marker_propagation', 'passed': False, 'detail': f'Marker check failed: {e}'})

    # Check 5: rollback criteria mention safe rollback
    try:
        text = normalize(raw or '')
        keywords = ['rollback', 'revert', 'safe', 'regression']
        hits = [k for k in keywords if k in text]
        passed = len(hits) >= 2
        checks.append({'name': 'rollback_criteria', 'passed': passed, 'detail': f'Keyword hits: {hits}'})
    except Exception as e:
        checks.append({'name': 'rollback_criteria', 'passed': False, 'detail': f'Rollback check failed: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
