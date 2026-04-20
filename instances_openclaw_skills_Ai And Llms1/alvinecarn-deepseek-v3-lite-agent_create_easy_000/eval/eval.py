import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: file exists
    try:
        target = workspace / 'welcome.txt'
        exists = target.exists()
        detail = 'welcome.txt exists' if exists else 'welcome.txt is missing'
        checks.append({'name': 'file_exists', 'passed': bool(exists), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'file_exists', 'passed': False, 'detail': f'error checking file existence: {e}'})

    # Check 2: content contains greeting and phrase
    try:
        text = (workspace / 'welcome.txt').read_text(encoding='utf-8', errors='replace')
        n = normalize(text)
        ok = ('maya' in n) and ('workspace is ready' in n) and ('let s get started' in n)
        detail = 'content includes Maya, workspace is ready, and Let\'s get started' if ok else f'normalized content: {n[:200]}'
        checks.append({'name': 'content_check', 'passed': bool(ok), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'content_check', 'passed': False, 'detail': f'error reading welcome.txt: {e}'})

    # Check 3: marker input exists and remains intact
    try:
        marker_path = workspace / 'input_marker.txt'
        marker_text = marker_path.read_text(encoding='utf-8', errors='replace')
        n = normalize(marker_text)
        ok = ('marker welcome task' in n) and ('user maya' in n)
        detail = 'input marker file present and intact' if ok else f'normalized marker content: {n[:200]}'
        checks.append({'name': 'marker_check', 'passed': bool(ok), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'marker_check', 'passed': False, 'detail': f'error reading input_marker.txt: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks)
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'unhandled error: {e}'}]}, ensure_ascii=False))
