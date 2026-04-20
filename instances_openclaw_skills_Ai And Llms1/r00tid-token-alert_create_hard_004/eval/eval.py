import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        session_path = workspace / 'session_report.json'
        if session_path.exists():
            try:
                data = json.loads(session_path.read_text(encoding='utf-8'))
                marker_ok = 'TOKEN_ALERT_MARKER_7F3A' in str(data.get('marker', ''))
                add_check('input marker present', marker_ok, 'marker found in session_report.json' if marker_ok else 'marker missing or altered in session_report.json')
            except Exception as e:
                add_check('input marker present', False, f'failed to parse session_report.json: {e}')
        else:
            add_check('input marker present', False, 'session_report.json is missing')
    except Exception as e:
        add_check('input marker present', False, f'unexpected error: {e}')

    expected_files = ['output.txt', 'dashboard.html']
    for fname in expected_files:
        try:
            p = workspace / fname
            if p.exists():
                add_check(f'{fname} exists', True, f'{fname} found')
            else:
                add_check(f'{fname} exists', False, f'{fname} is missing')
        except Exception as e:
            add_check(f'{fname} exists', False, f'error while checking existence: {e}')

    try:
        output_path = workspace / 'output.txt'
        if output_path.exists():
            try:
                txt = output_path.read_text(encoding='utf-8')
                n = normalize(txt)
                has_75 = '75' in txt or '75' in n
                has_90 = '90' in txt or '90' in n
                has_95 = '95' in txt or '95' in n
                has_marker = 'TOKEN_ALERT_MARKER_7F3A'.lower() in txt.lower()
                passed = has_75 and has_90 and has_95 and has_marker
                detail = 'contains threshold references and marker' if passed else 'missing one or more threshold references or marker'
                add_check('output.txt content', passed, detail)
            except Exception as e:
                add_check('output.txt content', False, f'could not read output.txt: {e}')
        else:
            add_check('output.txt content', False, 'output.txt missing')
    except Exception as e:
        add_check('output.txt content', False, f'unexpected error: {e}')

    try:
        dashboard_path = workspace / 'dashboard.html'
        if dashboard_path.exists():
            try:
                html = dashboard_path.read_text(encoding='utf-8')
                html_norm = html.lower()
                has_html = '<html' in html_norm and '</html>' in html_norm
                has_title = 'token' in html_norm and 'dashboard' in html_norm
                has_marker = 'TOKEN_ALERT_MARKER_7F3A'.lower() in html_norm
                passed = has_html and has_title and has_marker
                detail = 'valid html dashboard with title and marker' if passed else 'html structure/title/marker check failed'
                add_check('dashboard.html content', passed, detail)
            except Exception as e:
                add_check('dashboard.html content', False, f'could not read dashboard.html: {e}')
        else:
            add_check('dashboard.html content', False, 'dashboard.html missing')
    except Exception as e:
        add_check('dashboard.html content', False, f'unexpected error: {e}')

    try:
        score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
        passed = all(c['passed'] for c in checks) if checks else False
        result = {'passed': passed, 'score': score, 'checks': checks}
    except Exception as e:
        result = {'passed': False, 'score': 0.0, 'checks': checks + [{'name': 'result assembly', 'passed': False, 'detail': str(e)}]}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))
