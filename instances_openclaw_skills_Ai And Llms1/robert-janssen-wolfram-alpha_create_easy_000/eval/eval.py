import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

try:
    output_path = workspace / 'output.txt'
    if not output_path.exists():
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
    else:
        try:
            text = output_path.read_text(encoding='utf-8', errors='replace')
            norm = re.sub(r'[^a-z0-9.+\-]+', ' ', text.lower())
            has_9 = bool(re.search(r'\b9\b', norm))
            has_third = 'third' in norm
            has_three = bool(re.search(r'\b3\b', norm))
            passed = has_9 and (has_third or has_three)
            detail = f'content={text.strip()[:200]!r}'
            checks.append({'name': 'contains_integral_result', 'passed': passed, 'detail': detail})
        except Exception as e:
            checks.append({'name': 'contains_integral_result', 'passed': False, 'detail': f'read/parse error: {e}'})

    try:
        marker_path = workspace / 'input_marker.txt'
        if not marker_path.exists():
            checks.append({'name': 'marker_file_exists', 'passed': False, 'detail': 'input_marker.txt is missing'})
        else:
            marker_text = marker_path.read_text(encoding='utf-8', errors='replace')
            passed = 'wolfram_task_marker' in marker_text.lower()
            checks.append({'name': 'marker_file_exists', 'passed': passed, 'detail': f'content={marker_text.strip()[:200]!r}'})
    except Exception as e:
        checks.append({'name': 'marker_file_exists', 'passed': False, 'detail': f'read error: {e}'})

    try:
        workspace_ok = workspace.exists() and workspace.is_dir()
        checks.append({'name': 'workspace_valid', 'passed': workspace_ok, 'detail': str(workspace)})
    except Exception as e:
        checks.append({'name': 'workspace_valid', 'passed': False, 'detail': f'workspace check error: {e}'})

except Exception as e:
    checks.append({'name': 'fatal_guard', 'passed': False, 'detail': f'unexpected error: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
total = len(checks) if checks else 1
result = {
    'passed': passed_count == total,
    'score': passed_count / total,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
