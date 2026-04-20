import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    sanitized = workspace / 'sanitized.log'
    if sanitized.exists():
        text = sanitized.read_text(encoding='utf-8', errors='replace')
        lower = text.lower()
        sensitive_patterns = [
            r'password\s*=\s*[^\s]+',
            r'api[_-]?key\s*=\s*[^\s]+',
            r'bearer\s*[^\s]+',
            r'token\s*=\s*[^\s]+',
            r'session[_-]?id\s*=\s*[^\s]+',
            r'ghp_[a-z0-9]+',
            r'sk_test_[a-z0-9]+',
        ]
        found = []
        for pat in sensitive_patterns:
            if re.search(pat, lower):
                found.append(pat)
        add_check('sanitized_log_exists', True, 'sanitized.log is present')
        add_check('no_sensitive_patterns', len(found) == 0, 'sensitive patterns found: ' + (', '.join(found) if found else 'none'))
    else:
        add_check('sanitized_log_exists', False, 'sanitized.log is missing')
        add_check('no_sensitive_patterns', False, 'cannot inspect missing sanitized.log')
except Exception as e:
    add_check('sanitized_log_exists', False, f'error reading sanitized.log: {e}')
    add_check('no_sensitive_patterns', False, f'error inspecting sanitized.log: {e}')

try:
    report = workspace / 'sanitize-report.txt'
    if report.exists():
        rpt = report.read_text(encoding='utf-8', errors='replace')
        lowered = rpt.lower()
        ok = ('app.log' in lowered) and ('service.log' in lowered) and ('notes.log' in lowered)
        add_check('report_exists', True, 'sanitize-report.txt is present')
        add_check('report_mentions_inputs', ok, 'report mentions all expected input files' if ok else 'report is missing one or more expected filenames')
        redaction_words = ['redaction', 'redactions', 'sanitized']
        ok2 = any(w in lowered for w in redaction_words)
        add_check('report_has_redaction_summary', ok2, 'report includes a redaction summary' if ok2 else 'report lacks summary language')
    else:
        add_check('report_exists', False, 'sanitize-report.txt is missing')
        add_check('report_mentions_inputs', False, 'cannot inspect missing report')
        add_check('report_has_redaction_summary', False, 'cannot inspect missing report')
except Exception as e:
    add_check('report_exists', False, f'error reading report: {e}')
    add_check('report_mentions_inputs', False, f'error reading report: {e}')
    add_check('report_has_redaction_summary', False, f'error reading report: {e}')

try:
    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    passed = all(c['passed'] for c in checks) if checks else False
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'serialization', 'passed': False, 'detail': f'failed to serialize result: {e}'}]}, ensure_ascii=False))
