import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    out_path = workspace / 'ethos_audit.json'
    if not out_path.exists():
        add_check('output_exists', False, 'ethos_audit.json is missing')
        data = None
    else:
        try:
            data = json.loads(out_path.read_text(encoding='utf-8'))
            add_check('output_exists', True, 'ethos_audit.json exists and is valid JSON')
        except Exception as e:
            data = None
            add_check('output_exists', False, f'Could not parse JSON: {e}')

    expected_markers = ['INCENTIVES', 'DRIFT', 'CANDOR']
    if isinstance(data, dict):
        summary = data.get('summary', '')
        findings = data.get('findings', [])
        recommendation = data.get('recommendation', '')

        add_check('top_level_keys', set(data.keys()) == {'summary', 'findings', 'recommendation'}, f'Keys found: {sorted(list(data.keys()))}')
        add_check('summary_present', isinstance(summary, str) and len(summary.strip()) > 0, 'Summary is present')
        add_check('findings_shape', isinstance(findings, list) and len(findings) == 3, f'findings length: {len(findings) if isinstance(findings, list) else "not a list"}')
        add_check('recommendation_present', isinstance(recommendation, str) and len(recommendation.strip()) > 0, 'Recommendation is present')

        if isinstance(findings, list):
            marker_ok = True
            evidence_ok = True
            interp_ok = True
            for i, marker in enumerate(expected_markers):
                try:
                    item = findings[i]
                    m = str(item.get('marker', '')).strip().upper()
                    e = str(item.get('evidence', '')).strip()
                    it = str(item.get('interpretation', '')).strip()
                    if marker.lower() not in m.lower():
                        marker_ok = False
                    if len(e) < 10:
                        evidence_ok = False
                    if len(it) < 10:
                        interp_ok = False
                except Exception:
                    marker_ok = evidence_ok = interp_ok = False
            add_check('markers_order', marker_ok, 'Markers appear in expected order with fuzzy matching')
            add_check('evidence_quality', evidence_ok, 'Each finding includes non-trivial evidence text')
            add_check('interpretation_quality', interp_ok, 'Each finding includes non-trivial interpretation text')
        else:
            add_check('markers_order', False, 'findings is not a list')
            add_check('evidence_quality', False, 'findings is not a list')
            add_check('interpretation_quality', False, 'findings is not a list')

        # Check that output is grounded in the input markers.
        try:
            input_text = (workspace / 'behavior_notes.txt').read_text(encoding='utf-8')
            all_present = all(m in input_text for m in expected_markers)
            add_check('input_markers_present', all_present, 'Input file contains all required markers')
        except Exception as e:
            add_check('input_markers_present', False, f'Could not read input file: {e}')

    total = len(checks) if checks else 1
    passed_count = sum(1 for c in checks if c['passed'])
    result = {'passed': passed_count == total and total > 0, 'score': passed_count / total, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    fallback = {'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}
    print(json.dumps(fallback, ensure_ascii=False))
