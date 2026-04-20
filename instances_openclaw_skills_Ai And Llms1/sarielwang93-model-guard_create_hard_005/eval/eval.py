import json
import os
import re
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
    except Exception:
        return ''


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    out = ws / 'model_guard_report.md'

    # Check 1: output exists
    try:
        exists = out.exists()
        checks.append({
            'name': 'output_exists',
            'passed': bool(exists),
            'detail': 'model_guard_report.md exists' if exists else 'model_guard_report.md is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    content = ''
    if out.exists():
        try:
            content = out.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            content = ''
            checks.append({'name': 'read_output', 'passed': False, 'detail': f'failed to read output: {e}'})

    # Check 2: mentions best model candidate
    try:
        n = norm(content)
        passed = 'claude sonnet 4 5 thinking' in n or 'gemini 3 flash' in n or 'claude sonnet 4 5' in n
        detail = 'contains a plausible model name' if passed else 'missing expected model reference'
        checks.append({'name': 'model_reference', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'model_reference', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: explains switch vs fallback outcome based on snapshot
    try:
        n = norm(content)
        has_switch_words = any(k in n for k in ['switch', 'fallback', 'fallback to', 'switching'])
        has_threshold = '20' in n or 'threshold' in n
        passed = has_switch_words and has_threshold
        detail = 'mentions decision logic and threshold' if passed else 'missing decision explanation or threshold reference'
        checks.append({'name': 'decision_explanation', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'decision_explanation', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: embedded marker from input snapshot is echoed or referenced
    try:
        n = norm(content)
        passed = 'alpha 742' in n or 'marker quota snapshot' in n
        detail = 'references snapshot marker' if passed else 'does not reference snapshot marker ALPHA-742'
        checks.append({'name': 'snapshot_marker_used', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'snapshot_marker_used', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
