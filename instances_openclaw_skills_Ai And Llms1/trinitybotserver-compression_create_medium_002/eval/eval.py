import json
import os
import re
import sys
from pathlib import Path


def load_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def check_exists(path):
    try:
        return Path(path).exists(), f'found={Path(path).exists()}'
    except Exception as e:
        return False, str(e)


def fuzzy_contains(text, needles):
    if text is None:
        return False
    low = text.lower()
    return all(n.lower() in low for n in needles)


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        p = ws / 'trinity-compress.config.json'
        ok = p.exists()
        checks.append({'name': 'config file exists', 'passed': ok, 'detail': str(p)})
    except Exception as e:
        checks.append({'name': 'config file exists', 'passed': False, 'detail': str(e)})

    try:
        p = ws / 'scripts' / 'trinity-compress.sh'
        ok = p.exists()
        detail = 'present' if ok else 'missing'
        if ok:
            try:
                txt = p.read_text(encoding='utf-8', errors='ignore')
                ok = fuzzy_contains(txt, ['balanced']) and fuzzy_contains(txt, ['bak'])
                detail = 'contains balanced and bak' if ok else 'script content missing expected markers'
            except Exception as e:
                ok = False
                detail = str(e)
        checks.append({'name': 'compression script', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'compression script', 'passed': False, 'detail': str(e)})

    try:
        mk = ws / 'Makefile'
        ok = mk.exists()
        detail = 'missing'
        if ok:
            try:
                txt = mk.read_text(encoding='utf-8', errors='ignore')
                ok = fuzzy_contains(txt, ['optimize-prompts']) and fuzzy_contains(txt, ['optimize-undo'])
                detail = 'make targets present' if ok else 'make targets absent'
            except Exception as e:
                ok = False
                detail = str(e)
        checks.append({'name': 'makefile targets', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'makefile targets', 'passed': False, 'detail': str(e)})

    try:
        gi = ws / '.gitignore'
        ok = gi.exists()
        detail = 'missing'
        if ok:
            try:
                txt = gi.read_text(encoding='utf-8', errors='ignore')
                ok = '*.bak' in txt or 'bak' in txt.lower()
                detail = 'ignores bak files' if ok else 'no bak ignore rule found'
            except Exception as e:
                ok = False
                detail = str(e)
        checks.append({'name': 'gitignore update', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'gitignore update', 'passed': False, 'detail': str(e)})

    try:
        ps1 = ws / 'scripts' / 'install.ps1'
        sh = ws / 'scripts' / 'install.sh'
        ok1 = ps1.exists()
        ok2 = sh.exists()
        checks.append({'name': 'installer scripts', 'passed': ok1 and ok2, 'detail': f'ps1={ok1}, sh={ok2}'})
    except Exception as e:
        checks.append({'name': 'installer scripts', 'passed': False, 'detail': str(e)})

    try:
        # verify workspace markers remain available for evaluation context
        readme = ws / 'README.md'
        ok = readme.exists()
        detail = 'missing'
        if ok:
            try:
                txt = readme.read_text(encoding='utf-8', errors='ignore')
                ok = 'MARKER:README-SEED-2025' in txt
                detail = 'marker preserved' if ok else 'marker absent'
            except Exception as e:
                ok = False
                detail = str(e)
        checks.append({'name': 'input marker preserved', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input marker preserved', 'passed': False, 'detail': str(e)})

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
