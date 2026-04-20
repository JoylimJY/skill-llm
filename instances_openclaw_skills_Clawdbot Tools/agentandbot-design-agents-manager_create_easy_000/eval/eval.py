import json
import os
import re
import sys
from pathlib import Path

checks = []

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
output_path = workspace / 'output.txt'

# Check 1: output file exists
try:
    exists = output_path.exists()
    checks.append({
        'name': 'output_exists',
        'passed': bool(exists),
        'detail': 'output.txt found' if exists else 'output.txt is missing'
    })
except Exception as e:
    checks.append({'name': 'output_exists', 'passed': False, 'detail': f'Error checking existence: {e}'})

# Check 2: content contains required markers, fuzzy matching
content = ''
try:
    if output_path.exists():
        content = output_path.read_text(encoding='utf-8', errors='replace')
    norm = re.sub(r'[^a-z0-9]+', ' ', content.lower())
    has_main = ' main ' in f' {norm} '
    has_clawdia = ' clawdia ' in f' {norm} '
    has_healthy = ' healthy ' in f' {norm} '
    checks.append({
        'name': 'required_terms',
        'passed': bool(has_main and has_clawdia and has_healthy),
        'detail': f'main={has_main}, clawdia={has_clawdia}, healthy={has_healthy}'
    })
except Exception as e:
    checks.append({'name': 'required_terms', 'passed': False, 'detail': f'Error reading/parsing output.txt: {e}'})

# Check 3: mentions reporting to Ilkerkaan in a forgiving way
try:
    norm = re.sub(r'[^a-z0-9]+', ' ', content.lower())
    mentions_report = ('report to ilkerkaan' in norm) or ('reports to ilkerkaan' in norm) or ('reporting to ilkerkaan' in norm)
    checks.append({
        'name': 'mentions_report_target',
        'passed': bool(mentions_report),
        'detail': 'Found a reference to reporting to Ilkerkaan' if mentions_report else 'No clear reference to reporting to Ilkerkaan'
    })
except Exception as e:
    checks.append({'name': 'mentions_report_target', 'passed': False, 'detail': f'Error checking report target: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
total = len(checks) if checks else 1
score = passed_count / total
passed = passed_count == total

print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
