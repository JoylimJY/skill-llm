import json
import sys
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore'), None
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []
    ws = workspace

    # Check 1: output.json exists
    try:
        out_path = ws / 'output.json'
        exists = out_path.exists()
        checks.append({
            'name': 'output_exists',
            'passed': bool(exists),
            'detail': 'output.json found' if exists else 'output.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error: {e}'})

    # Parse output if possible
    data = None
    parse_err = None
    try:
        if (ws / 'output.json').exists():
            data = json.loads((ws / 'output.json').read_text(encoding='utf-8', errors='ignore'))
        else:
            data = {}
    except Exception as e:
        parse_err = str(e)
        data = {}

    # Check 2: project name
    try:
        val = data.get('project_name') or data.get('project') or data.get('name') or ''
        passed = norm(val) == norm('Project Aurora') or norm('Project Aurora') in norm(val)
        checks.append({
            'name': 'project_name',
            'passed': bool(passed),
            'detail': f'got={val!r}' + (f', parse_error={parse_err}' if parse_err else '')
        })
    except Exception as e:
        checks.append({'name': 'project_name', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: percentage value
    try:
        val = data.get('percentage') or data.get('percent') or data.get('completion') or ''
        sval = str(val)
        passed = '78' in ''.join(ch for ch in sval if ch.isdigit())
        checks.append({
            'name': 'percentage',
            'passed': bool(passed),
            'detail': f'got={val!r}'
        })
    except Exception as e:
        checks.append({'name': 'percentage', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: status text
    try:
        val = data.get('status') or data.get('state') or ''
        passed = norm('Running') in norm(val) or norm('Status: Running') in norm(val)
        checks.append({
            'name': 'status_text',
            'passed': bool(passed),
            'detail': f'got={val!r}'
        })
    except Exception as e:
        checks.append({'name': 'status_text', 'passed': False, 'detail': f'error: {e}'})

    # Check 5: coordinates present and plausible
    try:
        coords = (data.get('coordinates') or data.get('coords') or 
                  data.get('point') or data.get('percentage_coordinates') or {})
        if isinstance(coords, dict):
            x = coords.get('x')
            y = coords.get('y')
            passed = isinstance(x, int) and isinstance(y, int) and 0 <= x <= 1200 and 0 <= y <= 800
            detail = f'x={x!r}, y={y!r}'
        elif isinstance(coords, (list, tuple)) and len(coords) >= 2:
            x, y = coords[0], coords[1]
            passed = isinstance(x, int) and isinstance(y, int) and 0 <= x <= 1200 and 0 <= y <= 800
            detail = f'x={x!r}, y={y!r}'
        else:
            passed = False
            detail = f'coordinates missing or invalid: {coords!r}'
        checks.append({'name': 'coordinates', 'passed': bool(passed), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'coordinates', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': passed_count / total if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()