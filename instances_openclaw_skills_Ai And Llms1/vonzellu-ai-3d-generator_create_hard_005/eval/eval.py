import json
import os
import re
import sys
from pathlib import Path

checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, f"read failed: {e}"


def fuzzy_contains(text, needles):
    if text is None:
        return False
    norm = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return all(re.sub(r"[^a-z0-9]+", " ", n.lower()).strip() in norm for n in needles)


def main():
    try:
        workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    except Exception:
        workspace = Path('.')

    try:
        out = workspace / 'sci_fi_cargo_drone.stl'
        if out.exists():
            size = out.stat().st_size
            add_check('stl_exists', True, f'found {out.name} ({size} bytes)')
        else:
            add_check('stl_exists', False, 'sci_fi_cargo_drone.stl is missing')
    except Exception as e:
        add_check('stl_exists', False, f'error while checking file: {e}')

    try:
        marker_path = workspace / 'inputs' / 'task_marker.json'
        if marker_path.exists():
            txt = marker_path.read_text(encoding='utf-8', errors='replace')
            ok = fuzzy_contains(txt, ['OPENCLAW', 'MARKER', '1337'])
            add_check('marker_input_present', ok, 'marker file contains expected embedded marker content' if ok else 'marker content not detected')
        else:
            add_check('marker_input_present', False, 'inputs/task_marker.json is missing')
    except Exception as e:
        add_check('marker_input_present', False, f'error while checking marker file: {e}')

    try:
        py_files = list(workspace.glob('**/*.py'))
        found = False
        detail = 'no python file matched'
        for p in py_files:
            try:
                txt = p.read_text(encoding='utf-8', errors='replace')
                if fuzzy_contains(txt, ['trimesh', 'export', 'create_model']):
                    found = True
                    detail = f'found likely generator script: {p.name}'
                    break
            except Exception:
                continue
        add_check('generator_script_present', found, detail)
    except Exception as e:
        add_check('generator_script_present', False, f'error while scanning python files: {e}')

    try:
        valid = False
        detail = 'unable to inspect STL'
        if out.exists():
            try:
                data = out.read_bytes()
                if len(data) > 84:
                    header = data[:80]
                    tri_count = int.from_bytes(data[80:84], byteorder='little', signed=False)
                    valid = len(data) >= 84 + tri_count * 50
                    detail = f'header ok, triangles={tri_count}, size={len(data)}'
                else:
                    detail = f'file too small ({len(data)} bytes)'
            except Exception as e:
                detail = f'could not parse STL: {e}'
        add_check('stl_parseable', valid, detail)
    except Exception as e:
        add_check('stl_parseable', False, f'error while parsing STL: {e}')

    try:
        score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
        passed = all(c['passed'] for c in checks) if checks else False
        result = {"passed": passed, "score": float(score), "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()
