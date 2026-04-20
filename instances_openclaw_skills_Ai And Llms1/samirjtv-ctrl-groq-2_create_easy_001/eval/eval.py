import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    out_path = workspace / 'output.txt'
    if not out_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
    else:
        text = out_path.read_text(encoding='utf-8', errors='replace')
        norm = re.sub(r'\s+', ' ', text).strip().lower()
        has_fast = 'fast ai inference' in norm
        has_summary = len(norm) > 10
        add_check('contains_phrase', has_fast, 'Found required phrase' if has_fast else 'Required phrase not found')
        add_check('nonempty_summary', has_summary, 'File has content' if has_summary else 'File is too short or empty')
except Exception as e:
    add_check('read_output', False, f'Error reading output.txt: {e}')

try:
    marker_path = workspace / 'input_marker.txt'
    if not marker_path.exists():
        add_check('input_marker', False, 'input_marker.txt missing')
    else:
        marker = marker_path.read_text(encoding='utf-8', errors='replace')
        ok = 'groq_task_input' in marker.lower()
        add_check('input_marker', ok, 'Marker present' if ok else 'Marker missing')
except Exception as e:
    add_check('input_marker', False, f'Error reading input marker: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
