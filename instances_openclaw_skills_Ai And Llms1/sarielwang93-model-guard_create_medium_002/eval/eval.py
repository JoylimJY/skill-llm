import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', (s or '').lower())
    except Exception:
        return ''


def main():
    checks = []
    total = 0

    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: marker input file exists and contains the expected marker.
    total += 1
    try:
        p = workspace / 'marker_status.txt'
        txt = p.read_text(encoding='utf-8', errors='replace') if p.exists() else None
        ok = bool(txt) and 'marker: model_guard_input' in txt.lower()
        checks.append({
            'name': 'generated marker file',
            'passed': ok,
            'detail': 'marker_status.txt found with marker content' if ok else 'marker_status.txt missing or marker text not found'
        })
    except Exception as e:
        checks.append({'name': 'generated marker file', 'passed': False, 'detail': f'error reading marker_status.txt: {e}'})

    # Check 2: task implementation file exists.
    total += 1
    try:
        p = workspace / 'guard.js'
        ok = p.exists() and p.is_file()
        checks.append({
            'name': 'guard.js exists',
            'passed': ok,
            'detail': 'guard.js present' if ok else 'guard.js missing'
        })
    except Exception as e:
        checks.append({'name': 'guard.js exists', 'passed': False, 'detail': f'error checking guard.js: {e}'})

    # Check 3: guard.js keeps editable threshold and fallback settings.
    total += 1
    try:
        txt = (workspace / 'guard.js').read_text(encoding='utf-8', errors='replace') if (workspace / 'guard.js').exists() else ''
        ok = ('threshold' in txt.lower()) and ('fallback_model' in txt.lower())
        checks.append({
            'name': 'config knobs present',
            'passed': ok,
            'detail': 'threshold and fallback model settings detected' if ok else 'missing threshold or fallback model settings'
        })
    except Exception as e:
        checks.append({'name': 'config knobs present', 'passed': False, 'detail': f'error reading guard.js: {e}'})

    # Check 4: status_snapshot.json exists and contains expected defaults.
    total += 1
    try:
        p = workspace / 'status_snapshot.json'
        txt = p.read_text(encoding='utf-8', errors='replace') if p.exists() else ''
        n = normalize(txt)
        ok = 'googleantigravityclaudesonnet45' in n and 'googleantigravitygemini3prohigh' in n
        checks.append({
            'name': 'snapshot data present',
            'passed': ok,
            'detail': 'status_snapshot.json contains expected model markers' if ok else 'status_snapshot.json missing expected markers'
        })
    except Exception as e:
        checks.append({'name': 'snapshot data present', 'passed': False, 'detail': f'error reading status_snapshot.json: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    passed = passed_count == total and total > 0

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
