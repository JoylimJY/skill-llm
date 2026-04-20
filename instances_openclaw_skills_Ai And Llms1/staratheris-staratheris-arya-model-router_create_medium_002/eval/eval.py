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


def normalize(s):
    try:
        s = s.lower()
        s = re.sub(r'\s+', ' ', s)
        s = re.sub(r'[^a-z0-9@:_\- ]+', '', s)
        return s.strip()
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: required input markers exist
    try:
        expected_inputs = [
            ('input_main.txt', 'MARKER:ROUTER-INPUT-ALPHA'),
            ('input_override.txt', 'MARKER:ROUTER-INPUT-BETA'),
            ('input_daily.txt', 'MARKER:ROUTER-INPUT-GAMMA'),
        ]
        ok = True
        details = []
        for fname, marker in expected_inputs:
            p = workspace / fname
            if not p.exists():
                ok = False
                details.append(f'missing {fname}')
                continue
            try:
                txt = p.read_text(encoding='utf-8', errors='replace')
                if marker.lower() not in txt.lower():
                    ok = False
                    details.append(f'{fname} missing marker')
            except Exception as e:
                ok = False
                details.append(f'{fname} unreadable: {e}')
        checks.append({"name": "generated input markers", "passed": ok, "detail": '; '.join(details) if details else 'all markers present'})
    except Exception as e:
        checks.append({"name": "generated input markers", "passed": False, "detail": f'exception: {e}'})

    # Check 2: rules.json exists and contains routing tiers
    try:
        p = workspace / 'skills' / 'arya-model-router' / 'rules.json'
        ok = p.exists()
        detail = ''
        if ok:
            try:
                data = json.loads(p.read_text(encoding='utf-8'))
                models = normalize(json.dumps(data.get('models', {})))
                ok = all(x in models for x in ['cheap', 'default', 'pro'])
                detail = 'models loaded'
            except Exception as e:
                ok = False
                detail = f'parse failed: {e}'
        else:
            detail = 'rules.json missing'
        checks.append({"name": "rules file", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "rules file", "passed": False, "detail": f'exception: {e}'})

    # Check 3: README exists and mentions router auto / brief_first / daily report
    try:
        p = workspace / 'skills' / 'arya-model-router' / 'README.md'
        ok = p.exists()
        detail = ''
        if ok:
            try:
                txt = p.read_text(encoding='utf-8', errors='replace')
                n = normalize(txt)
                phrases = ['router auto on', 'brief_first', 'daily report']
                ok = sum(1 for ph in phrases if ph in n) >= 2
                detail = 'documentation phrases found' if ok else 'documentation too sparse'
            except Exception as e:
                ok = False
                detail = f'parse failed: {e}'
        else:
            detail = 'README missing'
        checks.append({"name": "documentation presence", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "documentation presence", "passed": False, "detail": f'exception: {e}'})

    # Check 4: router.py exists and appears to output JSON decision
    try:
        p = workspace / 'skills' / 'arya-model-router' / 'router.py'
        ok = p.exists()
        detail = ''
        if ok:
            try:
                txt = p.read_text(encoding='utf-8', errors='replace')
                n = normalize(txt)
                ok = 'json.dumps' in txt and 'decision' in n and 'response_policy' in n
                detail = 'router script structure looks correct' if ok else 'router script missing expected elements'
            except Exception as e:
                ok = False
                detail = f'parse failed: {e}'
        else:
            detail = 'router.py missing'
        checks.append({"name": "router implementation", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "router implementation", "passed": False, "detail": f'exception: {e}'})

    score = 0.0
    try:
        score = sum(1 for c in checks if c.get('passed')) / float(len(checks) or 1)
    except Exception:
        score = 0.0

    result = {
        "passed": all(c.get('passed') for c in checks),
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
