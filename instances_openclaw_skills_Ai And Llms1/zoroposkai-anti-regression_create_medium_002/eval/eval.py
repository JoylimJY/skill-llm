import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
    except Exception:
        return ''


def fuzzy_contains(text, phrase):
    try:
        return normalize(phrase) in normalize(text)
    except Exception:
        return False


checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
output_path = workspace / 'output.txt'

# Check 1: output exists
try:
    exists = output_path.exists()
    checks.append({
        'name': 'output_exists',
        'passed': bool(exists),
        'detail': 'output.txt found' if exists else 'output.txt is missing'
    })
except Exception as e:
    checks.append({
        'name': 'output_exists',
        'passed': False,
        'detail': f'error checking existence: {e}'
    })

# Check 2: contains marker alpha
try:
    text = output_path.read_text(encoding='utf-8') if output_path.exists() else ''
    ok = fuzzy_contains(text, 'CTO test')
    checks.append({
        'name': 'contains_cto_test',
        'passed': bool(ok),
        'detail': 'found CTO test marker' if ok else 'missing CTO test marker'
    })
except Exception as e:
    checks.append({
        'name': 'contains_cto_test',
        'passed': False,
        'detail': f'error reading output.txt: {e}'
    })

# Check 3: contains marker beta
try:
    text = output_path.read_text(encoding='utf-8') if output_path.exists() else ''
    ok = fuzzy_contains(text, 'semantic search first')
    checks.append({
        'name': 'contains_semantic_search_first',
        'passed': bool(ok),
        'detail': 'found semantic search first marker' if ok else 'missing semantic search first marker'
    })
except Exception as e:
    checks.append({
        'name': 'contains_semantic_search_first',
        'passed': False,
        'detail': f'error reading output.txt: {e}'
    })

# Check 4: three non-empty lines
try:
    lines = []
    if output_path.exists():
        lines = [ln.strip() for ln in output_path.read_text(encoding='utf-8').splitlines() if ln.strip()]
    ok = len(lines) == 3
    checks.append({
        'name': 'three_nonempty_lines',
        'passed': bool(ok),
        'detail': f'found {len(lines)} non-empty lines' if lines is not None else 'could not read lines'
    })
except Exception as e:
    checks.append({
        'name': 'three_nonempty_lines',
        'passed': False,
        'detail': f'error validating lines: {e}'
    })

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)

print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
