import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace'), None
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1])

    # Check 1: marker file exists
    try:
        p = workspace / 'task_marker.txt'
        exists = p.exists()
        checks.append({
            'name': 'marker_file_exists',
            'passed': bool(exists),
            'detail': 'task_marker.txt is present' if exists else 'task_marker.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'marker_file_exists', 'passed': False, 'detail': f'error: {e}'})

    # Check 2: marker content is present (lenient check)
    try:
        content, err = safe_read(workspace / 'task_marker.txt')
        if content is None:
            checks.append({'name': 'marker_content', 'passed': False, 'detail': f'could not read task_marker.txt: {err}'})
        else:
            # Lenient check: just verify file has some content
            ok = len(content.strip()) > 0
            checks.append({'name': 'marker_content', 'passed': bool(ok), 'detail': 'marker content present' if ok else 'marker file is empty'})
    except Exception as e:
        checks.append({'name': 'marker_content', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: reference note mentions sysaudit
    try:
        content, err = safe_read(workspace / 'reference_note.txt')
        if content is None:
            checks.append({'name': 'reference_note', 'passed': False, 'detail': f'could not read reference_note.txt: {err}'})
        else:
            ok = 'sysaudit' in content.lower()
            checks.append({'name': 'reference_note', 'passed': bool(ok), 'detail': 'reference note includes sysaudit' if ok else 'sysaudit not found in reference note'})
    except Exception as e:
        checks.append({'name': 'reference_note', 'passed': False, 'detail': f'error: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks)
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()