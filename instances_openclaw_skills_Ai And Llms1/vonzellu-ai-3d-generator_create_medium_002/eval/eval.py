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
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, f"read failed: {e}"


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower()) if isinstance(s, str) else ''

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
output_dir = workspace / 'output'
marker_path = workspace / 'input' / 'marker.json'

expected_stl = output_dir / 'ember_keep.stl'
expected_obj = output_dir / 'ember_keep_preview.obj'

# Check 1: STL exists and is non-empty
try:
    if expected_stl.exists() and expected_stl.stat().st_size > 0:
        add_check('stl_exists', True, f'Found {expected_stl.name} ({expected_stl.stat().st_size} bytes)')
    else:
        add_check('stl_exists', False, f'Missing or empty file: {expected_stl}')
except Exception as e:
    add_check('stl_exists', False, f'error: {e}')

# Check 2: marker-derived filename / output presence
try:
    if expected_obj.exists() and expected_obj.stat().st_size > 0:
        add_check('preview_obj_exists', True, f'Found {expected_obj.name} ({expected_obj.stat().st_size} bytes)')
    else:
        add_check('preview_obj_exists', False, f'Missing or empty preview OBJ: {expected_obj}')
except Exception as e:
    add_check('preview_obj_exists', False, f'error: {e}')

# Check 3: marker text handled in some output text file or notes file
try:
    marker = None
    try:
        marker_txt = Path(marker_path).read_text(encoding='utf-8')
        marker = json.loads(marker_txt)
    except Exception as e:
        add_check('marker_file_readable', False, f'could not read/parse marker.json: {e}')
    if marker:
        target = norm(marker.get('marker_text', ''))
        found = False
        detail = 'marker text not found'
        for p in [workspace / 'output' / 'build.log', workspace / 'output' / 'notes.txt', workspace / 'README.txt']:
            try:
                if p.exists():
                    content = p.read_text(encoding='utf-8', errors='ignore')
                    if target and target in norm(content):
                        found = True
                        detail = f'Found marker text in {p.name}'
                        break
            except Exception:
                continue
        add_check('marker_text_embedded', found, detail)
except Exception as e:
    add_check('marker_text_embedded', False, f'error: {e}')

# Check 4: basic STL plausibility via header/size, forgiving
try:
    ok = False
    detail = 'unreadable STL'
    if expected_stl.exists():
        with open(expected_stl, 'rb') as f:
            head = f.read(80)
            f.seek(0, os.SEEK_END)
            size = f.tell()
        # Binary STL can start with anything; require reasonable size
        if size > 84:
            ok = True
            detail = f'STL size looks plausible ({size} bytes)'
    add_check('stl_plausible', ok, detail)
except Exception as e:
    add_check('stl_plausible', False, f'error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
