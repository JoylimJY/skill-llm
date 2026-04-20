import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: input marker exists
try:
    desc_path = workspace / 'inputs' / 'description.txt'
    if desc_path.exists():
        content = desc_path.read_text(encoding='utf-8', errors='replace')
        marker_ok = 'MARKER_TASK_ID=ai3d_medium_01' in content
        add_check('input_marker', marker_ok, 'marker found' if marker_ok else 'marker missing')
    else:
        add_check('input_marker', False, 'inputs/description.txt is missing')
except Exception as e:
    add_check('input_marker', False, f'error reading input file: {e}')

# Check 2: output script exists
try:
    out_path = workspace / 'solution.py'
    if out_path.exists():
        add_check('solution_exists', True, 'solution.py exists')
    else:
        add_check('solution_exists', False, 'solution.py is missing')
except Exception as e:
    add_check('solution_exists', False, f'error checking output: {e}')

# Check 3: output contains relevant Trimesh usage
try:
    out_path = workspace / 'solution.py'
    if out_path.exists():
        content = out_path.read_text(encoding='utf-8', errors='replace')
        tokens = ['trimesh', 'export', 'cylinder', 'sphere', 'panel']
        found = sum(1 for t in tokens if t.lower() in content.lower())
        ok = found >= 3
        add_check('implementation_signals', ok, f'found {found}/{len(tokens)} expected keywords')
    else:
        add_check('implementation_signals', False, 'solution.py missing, cannot inspect')
except Exception as e:
    add_check('implementation_signals', False, f'error inspecting solution: {e}')

# Check 4: final STL output exists
try:
    stl_candidates = list(workspace.glob('*.stl')) + list((workspace / 'output').glob('*.stl')) if (workspace / 'output').exists() else list(workspace.glob('*.stl'))
    if stl_candidates:
        add_check('stl_output_exists', True, f'found {len(stl_candidates)} STL file(s)')
    else:
        add_check('stl_output_exists', False, 'no STL output found')
except Exception as e:
    add_check('stl_output_exists', False, f'error checking STL outputs: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
