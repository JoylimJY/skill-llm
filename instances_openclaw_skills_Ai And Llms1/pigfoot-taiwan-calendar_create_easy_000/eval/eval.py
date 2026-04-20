import json
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: required output file exists
    try:
        output_path = ws / 'output.txt'
        exists = output_path.exists()
        detail = 'output.txt exists' if exists else 'output.txt is missing'
        checks.append({'name': 'output_file_exists', 'passed': exists, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'error checking output.txt: {e}'})

    # Check 2: output mentions the correct next working day after 2025-01-03
    try:
        text = ''
        if (ws / 'output.txt').exists():
            text = (ws / 'output.txt').read_text(encoding='utf-8', errors='ignore')
        norm = normalize(text)
        expected_date = '2025 01 06'
        ok_date = expected_date.replace(' ', '') in norm.replace(' ', '') or '2025-01-06' in text or '1月6日' in text or '01 06' in norm
        ok_working_day = 'working day' in norm or '工作日' in text or 'work day' in norm
        passed = ok_date and ok_working_day
        detail = f'normalized_output={norm[:200]}'
        checks.append({'name': 'correct_date_and_status', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'correct_date_and_status', 'passed': False, 'detail': f'error reading output.txt: {e}'})

    # Check 3: marker input file exists and contains marker
    try:
        marker_path = ws / 'input_marker.txt'
        exists = marker_path.exists()
        marker_ok = False
        content = ''
        if exists:
            content = marker_path.read_text(encoding='utf-8', errors='ignore')
            marker_ok = 'TAIWAN_CALENDAR_TASK_MARKER_2025' in content
        passed = exists and marker_ok
        detail = 'marker found' if passed else f'exists={exists}, content_preview={content[:120]}'
        checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'error checking marker file: {e}'})

    total = len(checks) if checks else 1
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal_error', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))
