import json
from pathlib import Path


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    out = ws / 'token_report.txt'

    # Check 1: output exists
    try:
        exists = out.exists()
        checks.append({
            'name': 'output_exists',
            'passed': bool(exists),
            'detail': 'token_report.txt found' if exists else 'token_report.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'Error checking existence: {e}'})

    # Check 2: content contains report-like status and marker-derived numbers
    try:
        content = out.read_text(encoding='utf-8') if out.exists() else ''
        n = normalize(content)
        has_status = any(k in n for k in ['warning', 'critical', 'high', 'medium', 'low'])
        has_percent = '%' in content
        has_tokens = 'tokens' in n
        passed = has_status and has_percent and has_tokens
        checks.append({
            'name': 'report_content',
            'passed': passed,
            'detail': 'Looks like a token status report' if passed else 'Missing one or more expected report elements'
        })
    except Exception as e:
        checks.append({'name': 'report_content', 'passed': False, 'detail': f'Error reading report: {e}'})

    # Check 3: input marker file exists and is valid
    try:
        src = ws / 'session_status.json'
        if not src.exists():
            checks.append({'name': 'input_marker', 'passed': False, 'detail': 'session_status.json is missing'})
        else:
            data = json.loads(src.read_text(encoding='utf-8'))
            passed = data.get('marker', '').lower() == 'token_alert_marker_v1' and data.get('used_tokens') == 156000
            checks.append({
                'name': 'input_marker',
                'passed': passed,
                'detail': 'Marker file verified' if passed else 'Marker file content did not match expected values'
            })
    except Exception as e:
        checks.append({'name': 'input_marker', 'passed': False, 'detail': f'Error parsing marker file: {e}'})

    score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
    passed = all(c.get('passed') for c in checks)
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
