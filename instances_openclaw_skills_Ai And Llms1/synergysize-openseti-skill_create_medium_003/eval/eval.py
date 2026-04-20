import json
import os
import re
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()
    except Exception:
        return ''


def main():
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    ws = Path(workspace)
    checks = []

    # Check 1: output file exists
    try:
        output_path = ws / 'output.txt'
        exists = output_path.exists()
        checks.append({
            'name': 'output_exists',
            'passed': bool(exists),
            'detail': 'output.txt found' if exists else 'output.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    # Check 2: output contains classification and marker token
    try:
        if (ws / 'output.txt').exists():
            text, err = safe_read_text(ws / 'output.txt')
            if text is None:
                checks.append({'name': 'output_contents', 'passed': False, 'detail': f'could not read output.txt: {err}'})
            else:
                n = normalize(text)
                has_class = any(k in n for k in ['anomaly flagged', 'investigating', 'weak signal', 'natural'])
                has_marker = 'openseti marker 7f3a' in n or 'open seti marker 7f3a' in n or 'openseti_marker_7f3a'.replace('_', ' ') in n
                checks.append({
                    'name': 'output_contents',
                    'passed': bool(has_class and has_marker),
                    'detail': f'classification_found={has_class}, marker_found={has_marker}'
                })
        else:
            checks.append({'name': 'output_contents', 'passed': False, 'detail': 'output.txt missing, cannot inspect contents'})
    except Exception as e:
        checks.append({'name': 'output_contents', 'passed': False, 'detail': f'error inspecting contents: {e}'})

    # Check 3: output mentions justification / reasoning
    try:
        if (ws / 'output.txt').exists():
            text, err = safe_read_text(ws / 'output.txt')
            if text is None:
                checks.append({'name': 'output_justification', 'passed': False, 'detail': f'could not read output.txt: {err}'})
            else:
                n = normalize(text)
                has_reason = any(k in n for k in ['because', 'justification', 'due to', 'signal', 'drift', 'snr', 'bandwidth'])
                checks.append({
                    'name': 'output_justification',
                    'passed': bool(has_reason),
                    'detail': f'reasoning_markers_found={has_reason}'
                })
        else:
            checks.append({'name': 'output_justification', 'passed': False, 'detail': 'output.txt missing, cannot inspect justification'})
    except Exception as e:
        checks.append({'name': 'output_justification', 'passed': False, 'detail': f'error inspecting justification: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
