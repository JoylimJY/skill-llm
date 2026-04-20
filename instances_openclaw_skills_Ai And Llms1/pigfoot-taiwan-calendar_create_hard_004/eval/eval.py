import json
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', str(s).lower())
    except Exception:
        return ''


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8')), None
    except Exception as e:
        return None, str(e)


def is_working_day(date_str):
    # Deterministic expected logic for the task: use Taiwan calendar facts for the given dates.
    # 2025-01-01 is New Year's Day holiday.
    # 2025-01-04 and 2025-01-05 are weekend.
    # 2025-01-06 is working day.
    # 2025-01-10 is working day.
    holiday_map = {
        '2025-01-01': False,
    }
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        if date_str in holiday_map:
            return holiday_map[date_str]
        return dt.weekday() < 5
    except Exception:
        return False


workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: output.txt exists and has content
try:
    output_path = workspace / 'output.txt'
    if output_path.exists():
        txt = output_path.read_text(encoding='utf-8', errors='replace')
        passed = len(txt.strip()) > 0
        detail = 'output.txt found with content' if passed else 'output.txt is empty'
    else:
        passed = False
        detail = 'output.txt is missing'
except Exception as e:
    passed = False
    detail = f'Could not read output.txt: {e}'
checks.append({'name': 'output_file_exists', 'passed': passed, 'detail': detail})

# Check 2: summary.json exists and is parseable
summary = None
try:
    summary_path = workspace / 'summary.json'
    if summary_path.exists():
        summary, err = load_json(summary_path)
        passed = summary is not None and isinstance(summary, dict)
        detail = 'summary.json parsed successfully' if passed else f'summary.json invalid: {err}'
    else:
        passed = False
        detail = 'summary.json is missing'
except Exception as e:
    passed = False
    detail = f'Could not inspect summary.json: {e}'
checks.append({'name': 'summary_json_exists', 'passed': passed, 'detail': detail})

# Check 3: output mentions each required date classification
expected_phrases = {
    '2025-01-01': ['2025-01-01', 'non-working', 'holiday', 'new year'],
    '2025-01-04': ['2025-01-04', 'non-working', 'weekend'],
    '2025-01-06': ['2025-01-06', 'working'],
    '2025-01-10': ['2025-01-10', 'working'],
}
try:
    txt = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    low = txt.lower()
    hit_count = 0
    missing = []
    for date, phrases in expected_phrases.items():
        ok = norm(date) in norm(low)
        if ok:
            # fuzzy phrase presence
            phrase_ok = any(norm(p) in norm(low) for p in phrases[1:])
        else:
            phrase_ok = False
        if ok and phrase_ok:
            hit_count += 1
        else:
            missing.append(date)
    passed = hit_count >= 3
    detail = f'Found {hit_count}/4 expected date classifications; missing: {", ".join(missing) if missing else "none"}'
except Exception as e:
    passed = False
    detail = f'Could not analyze output text: {e}'
checks.append({'name': 'date_classifications', 'passed': passed, 'detail': detail})

# Check 4: range working day count is correct for 2025-01-01 to 2025-01-10
try:
    txt = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    m = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2})\s*(?:to|到)\s*([0-9]{4}-[0-9]{2}-[0-9]{2}).*?(\d+)\s*(?:working\s*days?|work\s*days?|個工作日)', txt, re.I | re.S)
    if m:
        count = int(m.group(3))
        passed = count == 7
        detail = f'Parsed working day count {count}; expected 7'
    else:
        # fallback fuzzy search
        passed = '7' in re.findall(r'\d+', txt) and ('working' in txt.lower() or '工作日' in txt)
        detail = 'Could not robustly parse count; used fallback presence check'
except Exception as e:
    passed = False
    detail = f'Could not evaluate range count: {e}'
checks.append({'name': 'range_count', 'passed': passed, 'detail': detail})

# Check 5: next working day after reference date
try:
    txt = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace') if (workspace / 'output.txt').exists() else ''
    passed = ('2025-01-07' in txt) or ('1/7' in txt.replace('-', '/')) or ('jan 7' in txt.lower())
    detail = 'Referenced next working day 2025-01-07' if passed else 'Next working day date not found in output'
except Exception as e:
    passed = False
    detail = f'Could not evaluate next working day: {e}'
checks.append({'name': 'next_working_day', 'passed': passed, 'detail': detail})

# Check 6: summary.json contains required keys and marker
try:
    if isinstance(summary, dict):
        required_keys = ['marker', 'reference_date', 'range_start', 'range_end', 'working_day_count', 'next_working_day']
        present = [k for k in required_keys if k in summary]
        marker_ok = norm(summary.get('marker', '')) == norm('MARKER-TC-2025-01-06')
        count_ok = summary.get('working_day_count') == 7
        next_ok = summary.get('next_working_day') == '2025-01-07'
        passed = len(present) >= 5 and marker_ok and count_ok and next_ok
        detail = f'Present keys: {present}; marker_ok={marker_ok}; count_ok={count_ok}; next_ok={next_ok}'
    else:
        passed = False
        detail = 'summary.json not available for inspection'
except Exception as e:
    passed = False
    detail = f'Could not validate summary.json contents: {e}'
checks.append({'name': 'summary_content', 'passed': passed, 'detail': detail})

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
