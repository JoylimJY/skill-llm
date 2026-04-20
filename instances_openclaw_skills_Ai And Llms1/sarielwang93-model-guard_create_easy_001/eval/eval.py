import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def fuzzy_contains(text, needle):
    try:
        if text is None:
            return False
        norm_text = re.sub(r'[^a-z0-9]+', '', text.lower())
        norm_needle = re.sub(r'[^a-z0-9]+', '', needle.lower())
        return norm_needle in norm_text
    except Exception:
        return False


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: required input markers exist
    try:
        status_txt = workspace / 'status.txt'
        status_json = workspace / 'status.json'
        ok = status_txt.exists() and status_json.exists()
        detail = []
        if not status_txt.exists():
            detail.append('missing status.txt')
        if not status_json.exists():
            detail.append('missing status.json')
        if ok:
            txt, err1 = safe_read(status_txt)
            js, err2 = safe_read(status_json)
            ok = fuzzy_contains(txt, 'MARKER_STATUS_ALPHA_2025') and fuzzy_contains(js, 'MARKER_JSON_BETA_2025')
            if not ok:
                detail.append('marker content not found')
        checks.append({'name': 'input markers', 'passed': ok, 'detail': '; '.join(detail) if detail else 'ok'})
    except Exception as e:
        checks.append({'name': 'input markers', 'passed': False, 'detail': f'exception: {e}'})

    # Check 2: guard.js exists and mentions threshold/fallback configurables
    try:
        guard = workspace / 'guard.js'
        ok = guard.exists()
        detail = []
        if not ok:
            detail.append('missing guard.js')
        else:
            txt, err = safe_read(guard)
            ok = fuzzy_contains(txt, 'THRESHOLD') and fuzzy_contains(txt, 'FALLBACK_MODEL')
            if not ok:
                detail.append('missing configurable constants')
        checks.append({'name': 'guard configuration', 'passed': ok, 'detail': '; '.join(detail) if detail else 'ok'})
    except Exception as e:
        checks.append({'name': 'guard configuration', 'passed': False, 'detail': f'exception: {e}'})

    # Check 3: output file exists and is non-empty
    try:
        out = workspace / 'output.txt'
        ok = out.exists() and out.stat().st_size > 0
        detail = 'ok' if ok else 'output.txt missing or empty'
        checks.append({'name': 'output file', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output file', 'passed': False, 'detail': f'exception: {e}'})

    # Check 4: output mentions the selected model in a forgiving way
    try:
        out = workspace / 'output.txt'
        txt = out.read_text(encoding='utf-8') if out.exists() else ''
        ok = fuzzy_contains(txt, 'google-antigravity/claude-sonnet-4-5') or fuzzy_contains(txt, 'google-gemini-3-flash-preview')
        detail = 'contains expected model mention' if ok else 'expected model mention not found'
        checks.append({'name': 'output content', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output content', 'passed': False, 'detail': f'exception: {e}'})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
