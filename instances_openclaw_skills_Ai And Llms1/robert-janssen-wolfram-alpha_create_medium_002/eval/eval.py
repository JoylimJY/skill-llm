import json
import os
import re
import csv
from pathlib import Path
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: output exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.is_file()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'error while checking output existence: {e}')

# Read output safely
output_text = ''
try:
    if (workspace / 'output.txt').is_file():
        output_text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace')
except Exception as e:
    add_check('output_readable', False, f'could not read output.txt: {e}')
else:
    add_check('output_readable', True, 'output.txt read successfully')

# Check 2: contains marker phrase
try:
    passed = 'result verified' in output_text.lower()
    add_check('contains_verification_marker', passed, 'RESULT VERIFIED present' if passed else 'RESULT VERIFIED missing')
except Exception as e:
    add_check('contains_verification_marker', False, f'error while searching marker: {e}')

# Load inputs safely
values = []
try:
    csv_path = workspace / 'data' / 'measurements.csv'
    if csv_path.is_file():
        with csv_path.open('r', encoding='utf-8', errors='replace', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    values.append(float(str(row.get('value', '')).strip()))
                except Exception:
                    continue
    add_check('measurements_loaded', len(values) > 0, f'loaded {len(values)} numeric values' if values else 'no numeric values found')
except Exception as e:
    add_check('measurements_loaded', False, f'error reading measurements.csv: {e}')

# Check 3: sum and average loosely parsed
try:
    expected_sum = sum(values)
    expected_avg = expected_sum / len(values) if values else None
    norm = re.sub(r'[^a-z0-9.\-]+', ' ', output_text.lower())
    sum_ok = False
    avg_ok = False
    if expected_avg is not None:
        # flexible search for numeric values near keywords
        sum_match = re.search(r'(sum|total)[^0-9\-]*([0-9]+(?:\.[0-9]+)?)', norm)
        avg_match = re.search(r'(avg|average|mean)[^0-9\-]*([0-9]+(?:\.[0-9]+)?)', norm)
        if sum_match:
            try:
                found_sum = float(sum_match.group(2))
                sum_ok = abs(found_sum - expected_sum) <= 0.01
            except Exception:
                sum_ok = False
        if avg_match:
            try:
                found_avg = float(avg_match.group(2))
                avg_ok = abs(found_avg - expected_avg) <= 0.02
            except Exception:
                avg_ok = False
    add_check('sum_value', sum_ok, f'expected about {expected_sum:.2f}' if values else 'no expected value')
    add_check('average_value', avg_ok, f'expected about {expected_avg:.2f}' if expected_avg is not None else 'no expected value')
except Exception as e:
    add_check('math_values', False, f'error validating math values: {e}')

# Check 4: miles to km conversion
try:
    # 12.5 miles = 20.1168 km
    expected_km = 12.5 * 1.609344
    km_ok = False
    # allow flexible spacing and formatting
    m = re.search(r'(?:km|kilometers?|kilometres?)[^0-9\-]*([0-9]+(?:\.[0-9]+)?)', output_text.lower())
    if m:
        try:
            found_km = float(m.group(1))
            km_ok = abs(found_km - expected_km) <= 0.02
        except Exception:
            km_ok = False
    add_check('miles_to_km', km_ok, f'expected about {expected_km:.3f} km')
except Exception as e:
    add_check('miles_to_km', False, f'error validating conversion: {e}')

# Check 5: primary item name from notes
try:
    note_path = workspace / 'data' / 'notes.txt'
    marker_line = ''
    if note_path.is_file():
        text = note_path.read_text(encoding='utf-8', errors='replace')
        for line in text.splitlines():
            if 'MARKER:PRIMARY' in line:
                marker_line = line
                break
    expected_item_ok = False
    if marker_line:
        # fuzzy parse item name from the marker line
        # examples like: - item: primary sample MARKER:PRIMARY
        m = re.search(r'item\s*:\s*(.+?)\s*marker\s*:\s*primary', marker_line, re.IGNORECASE)
        if m:
            expected_item = m.group(1).strip().lower()
            expected_item_ok = expected_item in output_text.lower()
    add_check('primary_item_present', expected_item_ok, 'primary item name found in output' if expected_item_ok else 'primary item name missing or unreadable')
except Exception as e:
    add_check('primary_item_present', False, f'error validating primary item: {e}')

# Final scoring
try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    passed = passed_count == total
    result = {
        'passed': passed,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    fallback = {
        'passed': False,
        'score': 0.0,
        'checks': checks + [{"name": "finalize", "passed": False, "detail": f"failed to finalize result: {e}"}],
    }
    print(json.dumps(fallback, ensure_ascii=False))
