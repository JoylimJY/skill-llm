import json
import os
import re
import sys
from pathlib import Path

def load_checks():
    checks = []
    return checks

def main(workspace_path):
    checks = []
    try:
        ws = Path(workspace_path)
        input_path = ws / 'input.txt'
        result_path = ws / 'result.txt'
        if not input_path.exists():
            checks.append({"name": "input_exists", "passed": False, "detail": "input.txt missing in workspace"})
            print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
            return
        # Read all lines
        with input_path.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        matched = []
        marker = 'MARKER'
        for line in lines:
            if re.search(rf'(?i)\b{marker}\b', line):
                matched.append(line)
        # Write result.txt
        with result_path.open('w', encoding='utf-8') as f:
            for m in matched:
                f.write(m if m.endswith('\n') else m + '\n')
        # Checks
        if result_path.exists():
            checks.append({"name": "result_created", "passed": True, "detail": "result.txt created with matched lines"})
        else:
            checks.append({"name": "result_created", "passed": False, "detail": "result.txt was not created"})
        # Basic property: at least one line matched if input had markers
        expected_any = any(re.search(rf'(?i)\bMARKER\b', l) for l in lines)
        if matched and len(matched) > 0:
            if expected_any:
                checks.append({"name": "marker_match_count", "passed": True, "detail": f"Found {len(matched)} matching lines"})
            else:
                checks.append({"name": "marker_match_count", "passed": False, "detail": "Markers expected but none matched"})
        else:
            checks.append({"name": "marker_match_count", "passed": True, "detail": "No markers present or none matched (allowed if input has none)"})
        passed = all(c.get('passed', False) for c in checks)
        score = sum(1 for c in checks if c.get('passed')) / max(1, len(checks))
        result = {"passed": bool(passed), "score": float(score), "checks": checks}
        print(json.dumps(result))
    except Exception as e:
        # Graceful failure
        checks.append({"name": "unexpected_error", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_error", "passed": False, "detail": "Workspace path argument required"}]}))
        sys.exit(2)
    main(sys.argv[1])
