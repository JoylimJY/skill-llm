from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def norm_text(value: object) -> str:
    try:
        s = str(value)
    except Exception:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


def safe_read_text(path: Path) -> tuple[bool, str]:
    try:
        return True, path.read_text(encoding='utf-8')
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def safe_read_json(path: Path) -> tuple[bool, object]:
    try:
        return True, json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def main() -> None:
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check config.json exists and matches requested values fuzzily
    ok, data = safe_read_json(ws / 'config.json')
    passed = False
    detail = ''
    if ok and isinstance(data, dict):
        letter_ok = norm_text(data.get('letter')) == 'o'
        name_ok = 'orion' in norm_text(data.get('name'))
        timeout_ok = False
        try:
            timeout_ok = int(data.get('idle_timeout')) == 600
        except Exception:
            timeout_ok = False
        passed = letter_ok and name_ok and timeout_ok
        detail = f"letter={data.get('letter')!r}, name={data.get('name')!r}, idle_timeout={data.get('idle_timeout')!r}"
    else:
        detail = f'config.json missing or unreadable: {data}'
    checks.append({'name': 'config updated for ORION', 'passed': passed, 'detail': detail})

    # Check monogram file exists and contains marker content
    ok, text = safe_read_text(ws / 'assets' / 'monograms' / 'O.txt')
    passed = False
    detail = ''
    if ok:
        t = text.lower()
        passed = ('orion-monogram' in t) and ('marker-start' in t) and ('marker-end' in t)
        detail = 'found marker text' if passed else 'missing expected marker text'
    else:
        detail = text
    checks.append({'name': 'O monogram marker file', 'passed': passed, 'detail': detail})

    # Check state.json exists and is non-idle with a visible message
    ok, data = safe_read_json(ws / 'state.json')
    passed = False
    detail = ''
    if ok and isinstance(data, dict):
        state = norm_text(data.get('state'))
        msg = norm_text(data.get('message'))
        passed = (state in {'work', 'think', 'alert', 'sleep'}) and bool(msg)
        detail = f"state={data.get('state')!r}, message={data.get('message')!r}"
    else:
        detail = f'state.json missing or unreadable: {data}'
    checks.append({'name': 'state is active with message', 'passed': passed, 'detail': detail})

    # Check scripts are present
    script_paths = [ws / 'scripts' / 'configure.py', ws / 'scripts' / 'status.py', ws / 'scripts' / 'display.py']
    missing = []
    for p in script_paths:
        try:
            if not p.exists():
                missing.append(p.name)
        except Exception:
            missing.append(p.name)
    passed = len(missing) == 0
    detail = 'missing: ' + ', '.join(missing) if missing else 'all scripts present'
    checks.append({'name': 'required scripts present', 'passed': passed, 'detail': detail})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    result = {
        'passed': passed_count == total,
        'score': passed_count / total if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Absolute fallback: never crash.
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal error', 'passed': False, 'detail': f'{type(e).__name__}: {e}'}]}))
