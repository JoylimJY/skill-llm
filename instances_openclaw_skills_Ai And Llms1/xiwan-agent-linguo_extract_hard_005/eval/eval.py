import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def main():
    checks = []
    ws = Path(sys.argv[1])

    # 1) output exists
    try:
        out = ws / 'output.txt'
        ok = out.exists() and out.is_file()
        detail = 'output.txt found' if ok else 'output.txt is missing'
        checks.append({'name': 'output_exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output existence: {e}'})

    # 2) contains marker strings from inputs
    try:
        txt = safe_read(ws / 'output.txt')
        markers = ['MARKER-ALPHA-7QX', 'SPEC-DRIFT-BETA-19']
        hits = sum(1 for m in markers if m.lower() in txt.lower())
        ok = hits == len(markers)
        detail = f'found {hits}/{len(markers)} required markers'
        checks.append({'name': 'markers_present', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'markers_present', 'passed': False, 'detail': f'error reading output: {e}'})

    # 3) summary mentions protocol behavior and handshake/security concepts
    try:
        txtn = norm(safe_read(ws / 'output.txt'))
        wanted = ['agent lingua', 'handshake', 'security', 'capabilities']
        hits = sum(1 for w in wanted if w in txtn)
        ok = hits >= 3
        detail = f'normalised keyword hits {hits}/{len(wanted)}'
        checks.append({'name': 'content_summary', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'content_summary', 'passed': False, 'detail': f'error analyzing output: {e}'})

    # 4) mentions contradictions/typos
    try:
        txtn = norm(safe_read(ws / 'output.txt'))
        wanted = ['typo', 'contradiction', 'misspell', 'canonical url']
        hits = sum(1 for w in wanted if w in txtn)
        ok = hits >= 2
        detail = f'found {hits} typo/contradiction indicators'
        checks.append({'name': 'typo_note', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'typo_note', 'passed': False, 'detail': f'error checking typo note: {e}'})

    # 5) file should be reasonably structured, with multiple lines
    try:
        txt = safe_read(ws / 'output.txt')
        lines = [ln for ln in txt.splitlines() if ln.strip()]
        ok = len(lines) >= 6
        detail = f'non-empty line count = {len(lines)}'
        checks.append({'name': 'structured_report', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'structured_report', 'passed': False, 'detail': f'error checking structure: {e}'})

    try:
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / len(checks) if checks else 0.0
        result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()
