import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    target = workspace / 'token-alert-note.md'
    try:
        exists = target.exists()
        checks.append({
            'name': 'output_file_exists',
            'passed': exists,
            'detail': 'Found token-alert-note.md' if exists else 'token-alert-note.md is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error checking file existence: {e}'})

    try:
        content, err = safe_read(target)
        if content is None:
            checks.append({'name': 'contains_thresholds', 'passed': False, 'detail': f'Could not read file: {err}'})
        else:
            n = normalize(content)
            has_75 = '75' in n and ('warning' in n or 'alert' in n)
            has_90 = '90' in n and ('warning' in n or 'critical' in n or 'alert' in n)
            session_only = 'session' in n and ('only' in n or 'based' in n or 'monitoring' in n)
            passed = has_75 and has_90 and session_only
            checks.append({
                'name': 'contains_thresholds',
                'passed': passed,
                'detail': f'75%={has_75}, 90%={has_90}, session-only={session_only}'
            })
    except Exception as e:
        checks.append({'name': 'contains_thresholds', 'passed': False, 'detail': f'Unexpected error: {e}'})

    try:
        marker_file = workspace / 'session_notes.txt'
        content, err = safe_read(marker_file)
        if content is None:
            checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'Could not read marker file: {err}'})
        else:
            n = normalize(content)
            passed = 'token alert marker' in n and '78' in n
            checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': f'Marker detected={passed}'})
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'Unexpected error: {e}'})

    try:
        total = len(checks)
        score = sum(1 for c in checks if c.get('passed')) / total if total else 0.0
        passed = all(c.get('passed') for c in checks)
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'final_output', 'passed': False, 'detail': f'Failed to serialize result: {e}'}]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
