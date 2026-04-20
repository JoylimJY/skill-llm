import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


# Check 1: output.txt exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.exists() and output_path.is_file()
    add_check('output_file_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_file_exists', False, f'error checking output.txt: {e}')

# Check 2: output.txt contains a reasonable greeting or completion text
try:
    text = ''
    if (workspace / 'output.txt').exists():
        text = (workspace / 'output.txt').read_text(encoding='utf-8', errors='replace')
    norm = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    keywords = ['hello', 'hi', 'greeting', 'alex']
    passed = all(k in norm for k in keywords[:2]) or ('alex' in norm and any(k in norm for k in ['hello', 'hi']))
    add_check('output_content_plausible', passed, f'normalized content: {norm[:200]}')
except Exception as e:
    add_check('output_content_plausible', False, f'error reading output.txt: {e}')

# Check 3: input marker file exists and contains marker content
try:
    input_path = workspace / 'input_message.txt'
    text = input_path.read_text(encoding='utf-8', errors='replace') if input_path.exists() else ''
    passed = 'groq-completion-easy-task' in text.lower()
    add_check('input_marker_present', passed, 'marker found' if passed else 'marker missing in input_message.txt')
except Exception as e:
    add_check('input_marker_present', False, f'error reading input_message.txt: {e}')

# Score calculation
try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    passed = passed_count == total
except Exception:
    score = 0.0
    passed = False

print(json.dumps({"passed": passed, "score": score, "checks": checks}))
