import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        return re.sub(r'[^a-z0-9]+', '', text.lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out_path = workspace / 'output.txt'
    expected_marker = 'SCREEN_VISION_MARKER_4821'

    try:
        if out_path.exists():
            content = out_path.read_text(encoding='utf-8', errors='replace')
            found = expected_marker.lower() in content.lower() or normalize(expected_marker) in normalize(content)
            checks.append({'name': 'output_exists_and_contains_marker', 'passed': bool(found), 'detail': 'output.txt found and marker comparison performed' if found else 'output.txt found but marker text was not detected'})
        else:
            checks.append({'name': 'output_exists_and_contains_marker', 'passed': False, 'detail': 'output.txt is missing'})
    except Exception as e:
        checks.append({'name': 'output_exists_and_contains_marker', 'passed': False, 'detail': f'error reading output.txt: {e}'})

    try:
        if out_path.exists():
            content = out_path.read_text(encoding='utf-8', errors='replace').strip()
            one_line = '\n' not in content.strip('\n')
            checks.append({'name': 'single_line_output', 'passed': bool(one_line), 'detail': 'output appears to be single-line' if one_line else 'output contains multiple lines'})
        else:
            checks.append({'name': 'single_line_output', 'passed': False, 'detail': 'output.txt is missing'})
    except Exception as e:
        checks.append({'name': 'single_line_output', 'passed': False, 'detail': f'error checking line count: {e}'})

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = (passed_count / total) if total else 0.0
        passed = passed_count == total and total > 0
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()
