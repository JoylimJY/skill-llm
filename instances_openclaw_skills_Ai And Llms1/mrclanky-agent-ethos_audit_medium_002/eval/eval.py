from pathlib import Path
import json
import re
import sys


def normalize(text):
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    report_path = ws / 'report.md'
    try:
        if not report_path.exists():
            checks.append({"name": "report_exists", "passed": False, "detail": "report.md is missing"})
        else:
            text = report_path.read_text(encoding='utf-8', errors='replace')
            checks.append({"name": "report_exists", "passed": True, "detail": "report.md exists"})
            norm = normalize(text)
            items = [
                ('strength_or_risk_count', len(re.findall(r'(^|\n)\s*[-*]\s+', text)) >= 3, 'Found at least 3 bullet items'),
                ('candid_tone', any(k in norm for k in ['risk', 'strength', 'recommend', 'boundary', 'reliable', 'candor']), 'Report uses audit-style language'),
                ('practical_recommendations', len(re.findall(r'recommend|suggest|should|consider', norm)) >= 3, 'Contains practical recommendations'),
                ('not_plain_summary', 'summary' not in norm or 'audit' in norm, 'Appears to be an audit rather than a simple summary'),
            ]
            for name, passed, detail in items:
                checks.append({"name": name, "passed": bool(passed), "detail": detail})
    except Exception as e:
        checks.append({"name": "report_check_exception", "passed": False, "detail": f'Exception while checking report: {e}'})

    try:
        input_path = ws / 'input' / 'ethos_notes.md'
        if not input_path.exists():
            checks.append({"name": "input_marker", "passed": False, "detail": "input/ethos_notes.md is missing"})
        else:
            text = input_path.read_text(encoding='utf-8', errors='replace')
            passed = 'ETHOS_AUDIT_MARKER_7F3A' in text
            checks.append({"name": "input_marker", "passed": passed, "detail": 'Marker found' if passed else 'Marker missing'})
    except Exception as e:
        checks.append({"name": "input_marker_exception", "passed": False, "detail": f'Exception while checking input marker: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = (passed_count / total) if total else 0.0
    result = {"passed": passed_count == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
