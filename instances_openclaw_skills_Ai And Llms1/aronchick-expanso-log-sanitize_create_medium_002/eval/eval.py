import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def redact_count(text):
    if text is None:
        return 0
    patterns = [
        r'password\s*[:=]\s*\S+',
        r'api[_-]?token\s*[:=]\s*\S+',
        r'token\s*[:=]\s*\S+',
        r'bearer\s+\S+',
        r'secret[_-]?key\s*[:=]\s*\S+',
    ]
    count = 0
    for pat in patterns:
        try:
            count += len(re.findall(pat, text, flags=re.IGNORECASE))
        except Exception:
            pass
    return count


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_dir = workspace / 'output'
    sanitized = out_dir / 'sanitized.log'
    report = out_dir / 'redaction_report.json'

    try:
        if sanitized.exists():
            text = sanitized.read_text(encoding='utf-8')
            lowered = text.lower()
            passed = all(x not in lowered for x in ['summer2025!', 'sk_live_abc123xyz789', 'prod-secret-99887766'])
            checks.append({'name': 'sanitized_log_exists_and_redacted', 'passed': passed, 'detail': 'sanitized.log present and sensitive markers absent' if passed else 'sanitized.log still contains sensitive content'})
        else:
            checks.append({'name': 'sanitized_log_exists_and_redacted', 'passed': False, 'detail': 'output/sanitized.log is missing'})
    except Exception as e:
        checks.append({'name': 'sanitized_log_exists_and_redacted', 'passed': False, 'detail': f'error reading sanitized.log: {e}'})

    try:
        if report.exists():
            data = json.loads(report.read_text(encoding='utf-8'))
            # Accept either format: with total_redactions field OR per-file counts
            has_total = 'total_redactions' in data
            has_files = 'files' in data
            # Accept per-file counts as integers or dicts
            has_per_file = isinstance(data, dict) and any(isinstance(v, (int, dict)) for v in data.values())
            passed = has_total or has_files or has_per_file
            checks.append({'name': 'report_exists_and_has_fields', 'passed': passed, 'detail': 'redaction_report.json parsed' if passed else 'report missing required fields'})
        else:
            checks.append({'name': 'report_exists_and_has_fields', 'passed': False, 'detail': 'output/redaction_report.json is missing'})
    except Exception as e:
        checks.append({'name': 'report_exists_and_has_fields', 'passed': False, 'detail': f'error parsing report: {e}'})

    try:
        marker_path = workspace / 'input' / 'marker.json'
        if marker_path.exists():
            marker = json.loads(marker_path.read_text(encoding='utf-8'))
            passed = 'KNOWN_MARKER_LOG_SANITIZE_42' in json.dumps(marker)
            checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': 'marker file contains expected deterministic marker' if passed else 'marker mismatch'})
        else:
            checks.append({'name': 'input_marker_present', 'passed': False, 'detail': 'input/marker.json missing'})
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'error reading marker file: {e}'})

    try:
        if sanitized.exists() and report.exists():
            report_data = json.loads(report.read_text(encoding='utf-8'))
            # Try to get total_redactions directly
            total = report_data.get('total_redactions', -1)
            # If not found, calculate from per-file counts
            if total == -1 and isinstance(report_data, dict):
                total = 0
                for key, value in report_data.items():
                    if isinstance(value, dict):
                        for v in value.values():
                            if isinstance(v, int):
                                total += v
                    elif isinstance(value, int):
                        total += value
            passed = isinstance(total, int) and total >= 4
            checks.append({'name': 'redaction_count_reasonable', 'passed': passed, 'detail': f'total_redactions={total}'})
        else:
            checks.append({'name': 'redaction_count_reasonable', 'passed': False, 'detail': 'missing files for count check'})
    except Exception as e:
        checks.append({'name': 'redaction_count_reasonable', 'passed': False, 'detail': f'error evaluating counts: {e}'})

    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()