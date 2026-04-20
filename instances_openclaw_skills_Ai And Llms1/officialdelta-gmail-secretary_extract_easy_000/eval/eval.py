import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    out_file = workspace / 'summary.txt'
    try:
        if out_file.exists():
            content = out_file.read_text(encoding='utf-8', errors='ignore')
            n = norm(content)
            has_marker = 'marker alpha' in n or 'marker-alpha' in n or 'markeralpha' in n
            has_label = any(k in n for k in ['read later', 'receipt billing', 'school'])
            passed = has_marker and has_label
            detail = 'found summary.txt with marker and label text' if passed else 'summary.txt exists but marker/label text was not sufficient'
        else:
            passed = False
            detail = 'summary.txt is missing'
    except Exception as e:
        passed = False
        detail = f'error checking summary.txt: {e}'
    checks.append({'name': 'summary file', 'passed': passed, 'detail': detail})

    try:
        src = workspace / 'inbox' / 'messages.json'
        if src.exists():
            raw = src.read_text(encoding='utf-8', errors='ignore')
            ok = 'MARKER-ALPHA' in raw and 'MARKER-BETA' in raw and 'MARKER-GAMMA' in raw
            passed = ok
            detail = 'input bundle contains all expected markers' if ok else 'one or more expected markers missing from inputs'
        else:
            passed = False
            detail = 'input messages.json missing'
    except Exception as e:
        passed = False
        detail = f'error checking input markers: {e}'
    checks.append({'name': 'input markers', 'passed': passed, 'detail': detail})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
