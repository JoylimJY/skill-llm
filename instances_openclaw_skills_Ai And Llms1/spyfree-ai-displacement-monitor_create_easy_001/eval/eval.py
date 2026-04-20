import json
import os
import re
import csv
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: output exists
try:
    output_path = workspace / 'output.txt'
    exists = output_path.exists()
    add_check('output_exists', exists, 'output.txt found' if exists else 'output.txt is missing')
except Exception as e:
    add_check('output_exists', False, f'error checking output existence: {e}')

# Check 2: contains signal board / composite / notes / gaps
try:
    text, err = safe_read_text(output_path)
    if text is None:
        add_check('required_sections', False, f'could not read output.txt: {err}')
    else:
        norm = re.sub(r'\s+', ' ', text.lower())
        wanted = ['signal board', 'composite risk light', 'actionable notes', 'data gaps']
        passed = all(w in norm for w in wanted)
        detail = 'all required sections present' if passed else 'missing one or more required sections'
        add_check('required_sections', passed, detail)
except Exception as e:
    add_check('required_sections', False, f'error: {e}')

# Check 3: uses markers from inputs
try:
    text, err = safe_read_text(output_path)
    if text is None:
        add_check('marker_usage', False, f'could not read output.txt: {err}')
    else:
        norm = re.sub(r'\s+', ' ', text.lower())
        keywords = ['ai displacement', 'substitution', 're-absorption']
        passed = sum(1 for k in keywords if k in norm) >= 2
        add_check('marker_usage', passed, 'mentions marker concepts' if passed else 'insufficient reference to dataset markers')
except Exception as e:
    add_check('marker_usage', False, f'error: {e}')

# Check 4: references the correct composite light based on provided data (at least orange/red expected)
try:
    text, err = safe_read_text(output_path)
    if text is None:
        add_check('composite_light', False, f'could not read output.txt: {err}')
    else:
        norm = re.sub(r'[^a-z]+', ' ', text.lower())
        found = None
        for c in ['red', 'orange', 'yellow', 'green']:
            if re.search(r'\b' + c + r'\b', norm):
                found = c.upper()
                break
        passed = found in ['RED', 'ORANGE']
        add_check('composite_light', passed, f'found composite light: {found or "none"}; expected ORANGE or RED')
except Exception as e:
    add_check('composite_light', False, f'error: {e}')

# Check 5: mentions at least 3 indicator IDs or labels from data
try:
    text, err = safe_read_text(output_path)
    if text is None:
        add_check('indicator_coverage', False, f'could not read output.txt: {err}')
    else:
        norm = text.lower()
        ids = ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'b3', 'c1', 'c2', 'c3']
        count = sum(1 for i in ids if re.search(r'\b' + re.escape(i) + r'\b', norm))
        passed = count >= 3
        add_check('indicator_coverage', passed, f'found {count} indicator ids' if passed else f'found only {count} indicator ids')
except Exception as e:
    add_check('indicator_coverage', False, f'error: {e}')

try:
    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = passed_count / total if total else 0.0
    passed = passed_count == total
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks + [{"name": "finalize", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
