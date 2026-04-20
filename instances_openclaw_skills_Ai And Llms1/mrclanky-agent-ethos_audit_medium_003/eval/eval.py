import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    except Exception:
        return ''


def main():
    checks = []
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    root = Path(workspace)
    report_path = root / 'audit_report.txt'

    # Check 1: output file exists
    try:
        exists = report_path.exists()
        checks.append({
            'name': 'audit_report_exists',
            'passed': bool(exists),
            'detail': 'audit_report.txt found' if exists else 'audit_report.txt is missing'
        })
    except Exception as e:
        checks.append({'name': 'audit_report_exists', 'passed': False, 'detail': f'Error checking existence: {e}'})

    # Check 2: contains required section names
    try:
        text, err = safe_read(report_path)
        if text is None:
            checks.append({'name': 'sections_present', 'passed': False, 'detail': f'Could not read report: {err}'})
        else:
            n = normalize(text)
            required = ['strengths', 'risks', 'recommendation']
            found = [sec for sec in required if sec in n]
            passed = len(found) == len(required)
            checks.append({
                'name': 'sections_present',
                'passed': passed,
                'detail': f'Found sections: {found}' if passed else f'Missing sections: {sorted(set(required) - set(found))}'
            })
    except Exception as e:
        checks.append({'name': 'sections_present', 'passed': False, 'detail': f'Error validating sections: {e}'})

    # Check 3: uses evidence from log and candid style
    try:
        report_text, err1 = safe_read(report_path)
        log_text, err2 = safe_read(root / 'incident_log.txt')
        if report_text is None:
            checks.append({'name': 'evidence_alignment', 'passed': False, 'detail': f'Could not read report: {err1}'})
        elif log_text is None:
            checks.append({'name': 'evidence_alignment', 'passed': False, 'detail': f'Could not read incident log: {err2}'})
        else:
            report_n = normalize(report_text)
            log_n = normalize(log_text)
            markers = ['confident', 'corrected', 'unclear instructions', 'slowing down', 'high stakes']
            score = sum(1 for m in markers if m in report_n or m in log_n)
            passed = score >= 3
            checks.append({
                'name': 'evidence_alignment',
                'passed': passed,
                'detail': f'Matched {score}/5 evidence markers'
            })
    except Exception as e:
        checks.append({'name': 'evidence_alignment', 'passed': False, 'detail': f'Error validating evidence: {e}'})

    # Check 4: ends with reliability sentence about high-stakes work
    try:
        text, err = safe_read(report_path)
        if text is None:
            checks.append({'name': 'reliability_sentence', 'passed': False, 'detail': f'Could not read report: {err}'})
        else:
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            last = lines[-1] if lines else ''
            nlast = normalize(last)
            ok = ('high stakes' in nlast or 'high-stakes' in last.lower()) and ('reliable' in nlast or 'not reliable' in nlast or 'enough' in nlast)
            checks.append({
                'name': 'reliability_sentence',
                'passed': bool(ok),
                'detail': f'Last line: {last[:120]}' if lines else 'Report is empty'
            })
    except Exception as e:
        checks.append({'name': 'reliability_sentence', 'passed': False, 'detail': f'Error validating ending sentence: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed == total,
        'score': (passed / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': 'Unhandled error in eval script'}]}))
