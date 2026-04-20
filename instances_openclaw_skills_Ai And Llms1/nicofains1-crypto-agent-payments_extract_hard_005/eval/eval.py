import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

expected_file = workspace / 'output.txt'
try:
    if not expected_file.exists():
        add_check('output_exists', False, 'output.txt is missing')
        text = ''
    else:
        text = expected_file.read_text(encoding='utf-8', errors='ignore')
        add_check('output_exists', True, 'output.txt exists')
except Exception as e:
    add_check('output_exists', False, f'Could not read output.txt: {e}')
    text = ''

norm = re.sub(r'[^a-zA-Z0-9]+', ' ', text).lower()

expected_items = [
    ('primary_id', 'alpha 7842'),
    ('code_phrase', 'orange lantern'),
    ('checksum', 'm7q 55 x9'),
]

for name, needle in expected_items:
    try:
        ok = needle in norm
        add_check(name, ok, f"Looking for '{needle}' in normalized output")
    except Exception as e:
        add_check(name, False, f'Error while checking {name}: {e}')

try:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    minimal = len(lines) <= 3
    add_check('concise_output', minimal, f'{len(lines)} non-empty line(s) found')
except Exception as e:
    add_check('concise_output', False, f'Could not analyze line count: {e}')

passed_count = sum(1 for c in checks if c['passed'])
total = len(checks)
score = passed_count / total if total else 0.0
passed = passed_count == total
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))