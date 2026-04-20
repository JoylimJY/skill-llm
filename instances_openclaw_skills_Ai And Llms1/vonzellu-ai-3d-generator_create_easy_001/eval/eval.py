import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # Check input marker exists
    try:
        input_path = workspace / 'input.json'
        if input_path.exists():
            text = input_path.read_text(encoding='utf-8', errors='ignore')
            ok = 'GEAR_INPUT_MARKER_2025' in text
            add_check('input_marker', ok, 'marker found in input.json' if ok else 'marker missing from input.json')
        else:
            add_check('input_marker', False, 'input.json is missing')
    except Exception as e:
        add_check('input_marker', False, f'error reading input.json: {e}')

    # Check STL output exists
    try:
        stl_files = list(workspace.glob('*.stl')) + list((workspace / 'stl-exports').glob('*.stl') if (workspace / 'stl-exports').exists() else [])
        if stl_files:
            add_check('stl_exists', True, f'found {len(stl_files)} STL file(s)')
        else:
            add_check('stl_exists', False, 'no STL file found in workspace or stl-exports/')
    except Exception as e:
        add_check('stl_exists', False, f'error searching for STL files: {e}')

    # Check there is at least one non-empty STL file
    try:
        valid = False
        detail = 'no STL file inspected'
        for p in stl_files if 'stl_files' in locals() else []:
            try:
                if p.exists() and p.stat().st_size > 84:
                    valid = True
                    detail = f'{p.name} size={p.stat().st_size}'
                    break
            except Exception:
                continue
        add_check('stl_nonempty', valid, detail if valid else 'all STL files are missing or too small')
    except Exception as e:
        add_check('stl_nonempty', False, f'error validating STL size: {e}')

    # Check filename is reasonably gear-related (fuzzy)
    try:
        names = [p.name.lower() for p in stl_files if hasattr(p, 'name')] if 'stl_files' in locals() else []
        ok = any(('gear' in n or 'gear' in n.replace('_', '').replace('-', '')) for n in names)
        add_check('filename_hint', ok, 'a gear-related filename was found' if ok else 'no gear-related filename found')
    except Exception as e:
        add_check('filename_hint', False, f'error checking filenames: {e}')

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    result = {
        'passed': passed_count == total,
        'score': passed_count / total if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
