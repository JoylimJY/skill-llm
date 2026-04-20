import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# 1. output file exists
try:
    out_path = workspace / 'output.txt'
    exists = out_path.exists() and out_path.is_file()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
    text = ''
    if exists:
        try:
            text = out_path.read_text(encoding='utf-8', errors='ignore')
        except Exception as e:
            add_check('output_readable', False, f'Could not read output.txt: {e}')
        else:
            add_check('output_readable', True, 'output.txt is readable')
    else:
        text = ''
except Exception as e:
    add_check('output_exists', False, f'Unexpected error checking output: {e}')
    text = ''

# 2. contains required sections, fuzzy matching
try:
    norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())
    required = ['signal board', 'composite risk light', 'actionable notes', 'data gaps']
    sec_pass = all(r in norm for r in required)
    add_check('required_sections', sec_pass, 'All required section names present' if sec_pass else f'Missing one or more sections in: {required}')
except Exception as e:
    add_check('required_sections', False, f'Error parsing output sections: {e}')

# 3. composite light appears and is one of allowed values
try:
    allowed = ['green', 'yellow', 'orange', 'red']
    m = re.search(r'composite\s+risk\s+light\s*[:\-]?\s*([a-z]+)', text.lower())
    value = m.group(1) if m else ''
    passed = value in allowed
    add_check('composite_value', passed, f'Found {value!r}' if value else 'Composite risk light not found')
except Exception as e:
    add_check('composite_value', False, f'Error checking composite value: {e}')

# 4. signal board has at least 10 indicator-like lines
try:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    indicator_lines = []
    for ln in lines:
        low = ln.lower()
        if re.match(r'^(a|b|c)\d', low) or re.match(r'^\d+[\).\-]\s*', low) or 'indicator' in low:
            indicator_lines.append(ln)
    passed = len(indicator_lines) >= 10
    add_check('ten_indicators', passed, f'Found {len(indicator_lines)} indicator-like lines')
except Exception as e:
    add_check('ten_indicators', False, f'Error counting indicators: {e}')

# 5. no obvious placeholder/marker leakage from inputs required? Ensure user did not simply copy raw marker text as solution dependency, but allow mention. Instead verify mentions a timestamp/date style.
try:
    date_like = re.search(r'\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b', text) or re.search(r'\b20\d{2}\b', text)
    add_check('contains_date', bool(date_like), 'Date or as-of reference found' if date_like else 'No date/as-of reference found')
except Exception as e:
    add_check('contains_date', False, f'Error checking date: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result))
