import json
import os
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    import sys
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Check 1: output file exists
    try:
        out = ws / 'output.txt'
        exists = out.exists()
        checks.append({
            'name': 'output_file_exists',
            'passed': bool(exists),
            'detail': 'output.txt found' if exists else 'output.txt is missing'
        })
    except Exception as e:
        checks.append({
            'name': 'output_file_exists',
            'passed': False,
            'detail': f'error checking existence: {e}'
        })

    # Check 2: output contains marker text from input_marker.txt
    try:
        marker_path = ws / 'input_marker.txt'
        marker_text, marker_err = safe_read(marker_path)
        out_text, out_err = safe_read(ws / 'output.txt')
        if marker_text is None:
            checks.append({
                'name': 'contains_marker_text',
                'passed': False,
                'detail': f'could not read input_marker.txt: {marker_err}'
            })
        elif out_text is None:
            checks.append({
                'name': 'contains_marker_text',
                'passed': False,
                'detail': f'could not read output.txt: {out_err}'
            })
        else:
            marker_norm = norm(marker_text)
            out_norm = norm(out_text)
            passed = bool(marker_norm) and marker_norm in out_norm
            checks.append({
                'name': 'contains_marker_text',
                'passed': passed,
                'detail': 'marker phrase present' if passed else 'marker phrase not found in output.txt'
            })
    except Exception as e:
        checks.append({
            'name': 'contains_marker_text',
            'passed': False,
            'detail': f'error validating marker text: {e}'
        })

    # Check 3: no accidental overwrite of distractor file
    try:
        distractor = ws / 'notes.txt'
        text, err = safe_read(distractor)
        passed = text is not None and 'distractor' in text.lower()
        checks.append({
            'name': 'distractor_unchanged',
            'passed': passed,
            'detail': 'notes.txt still intact' if passed else (f'notes.txt missing or changed: {err}' if text is None else 'notes.txt content unexpected')
        })
    except Exception as e:
        checks.append({
            'name': 'distractor_unchanged',
            'passed': False,
            'detail': f'error checking distractor file: {e}'
        })

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
