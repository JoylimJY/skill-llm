import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = str(text)
    except Exception:
        return ''
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    try:
        workspace = Path(sys.argv[1])
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'workspace_arg', 'passed': False, 'detail': f'Invalid workspace argument: {e}'}]}, ensure_ascii=False))
        return

    expected_files = ['taiwan_workday_brief.txt', 'report.json']
    for fname in expected_files:
        try:
            exists = (workspace / fname).exists()
            checks.append({'name': f'{fname}_exists', 'passed': bool(exists), 'detail': 'found' if exists else 'missing'})
        except Exception as e:
            checks.append({'name': f'{fname}_exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    brief_text = ''
    report_text = ''
    try:
        brief_res = safe_read(workspace / 'taiwan_workday_brief.txt')
        if isinstance(brief_res, tuple):
            brief_text, brief_err = brief_res
            if brief_text is None:
                checks.append({'name': 'brief_readable', 'passed': False, 'detail': f'could not read brief: {brief_err}'})
            else:
                checks.append({'name': 'brief_readable', 'passed': True, 'detail': 'read ok'})
        else:
            brief_text = brief_res
            checks.append({'name': 'brief_readable', 'passed': True, 'detail': 'read ok'})
    except Exception as e:
        checks.append({'name': 'brief_readable', 'passed': False, 'detail': f'brief read exception: {e}'})

    try:
        report_res = safe_read(workspace / 'report.json')
        if isinstance(report_res, tuple):
            report_text, report_err = report_res
            if report_text is None:
                checks.append({'name': 'report_readable', 'passed': False, 'detail': f'could not read report: {report_err}'})
            else:
                checks.append({'name': 'report_readable', 'passed': True, 'detail': 'read ok'})
        else:
            report_text = report_res
            checks.append({'name': 'report_readable', 'passed': True, 'detail': 'read ok'})
    except Exception as e:
        checks.append({'name': 'report_readable', 'passed': False, 'detail': f'report read exception: {e}'})

    marker_checks = [
        ('anchor_date_present', '2025-01-06', True),
        ('holiday_date_present', '2025-01-01', True),
        ('weekday_date_present', '2025-01-03', True),
        ('note_present', 'tw-calendar-marker-7f3a', True),
    ]
    brief_norm = normalize(brief_text)
    report_norm = normalize(report_text)
    for name, needle, must_in_brief in marker_checks:
        try:
            ok_brief = needle in brief_norm
            ok_report = needle in report_norm
            passed = ok_brief or ok_report
            checks.append({'name': name, 'passed': passed, 'detail': f'brief={ok_brief}, report={ok_report}'})
        except Exception as e:
            checks.append({'name': name, 'passed': False, 'detail': f'error: {e}'})

    try:
        # Flexible content checks for likely conclusions
        b = brief_norm
        r = report_norm
        checks.append({'name': 'holiday_conclusion', 'passed': ('2025-01-01' in b and ('holiday' in b or 'non-working' in b or 'non working' in b)) or ('2025-01-01' in r and ('holiday' in r or 'non-working' in r or 'non working' in r)), 'detail': 'expects Jan 1 described as holiday/non-working'})
        checks.append({'name': 'workday_conclusion', 'passed': ('2025-01-03' in b and ('working day' in b or 'workday' in b)) or ('2025-01-03' in r and ('working day' in r or 'workday' in r)), 'detail': 'expects Jan 3 described as working day'})
        checks.append({'name': 'next_working_day_after_anchor', 'passed': ('2025-01-07' in b) or ('2025-01-07' in r), 'detail': 'expects a next working day mention around 2025-01-07 (flexible)'} )
        checks.append({'name': 'monthly_note', 'passed': ('working days' in b or 'workdays' in b or '工作日' in brief_text) or ('working days' in r or 'workdays' in r or '工作日' in report_text), 'detail': 'expects a month working-day summary'})
    except Exception as e:
        checks.append({'name': 'content_conclusions', 'passed': False, 'detail': f'content check exception: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    try:
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()
