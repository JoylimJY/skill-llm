import json
import os
from pathlib import Path

workspace = Path(str(__import__('sys').argv[1]))
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

# Check 1: marker file exists and contains marker text
try:
    p = workspace / 'docs' / 'README_MARKER.txt'
    if p.exists():
        txt = p.read_text(encoding='utf-8', errors='replace')
        ok = 'clawface_demo_marker' in txt.lower()
        add_check('marker_file', ok, 'marker text found' if ok else 'marker text missing')
    else:
        add_check('marker_file', False, 'docs/README_MARKER.txt is missing')
except Exception as e:
    add_check('marker_file', False, f'error reading marker file: {e}')

# Check 2: state json exists and has expected fuzzy properties
try:
    p = workspace / 'assets' / 'input_state.json'
    if not p.exists():
        add_check('state_json', False, 'assets/input_state.json is missing')
    else:
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            em = str(data.get('emotion', '')).lower().strip()
            ac = str(data.get('action', '')).lower().strip()
            ef = str(data.get('effect', '')).lower().strip()
            msg = str(data.get('message', '')).lower()
            ok = (em in {'neutral', 'happy', 'excited', 'thinking'} or 'neutral' in em) and ('idle' in ac) and ('none' in ef) and ('marker' in msg)
            add_check('state_json', ok, f"emotion={em!r}, action={ac!r}, effect={ef!r}, message_has_marker={'marker' in msg}")
        except Exception as e:
            add_check('state_json', False, f'json parse failed: {e}')
except Exception as e:
    add_check('state_json', False, f'error: {e}')

# Check 3: launch notes mention robot mode and greeting
try:
    p = workspace / 'assets' / 'launch_notes.txt'
    if p.exists():
        txt = p.read_text(encoding='utf-8', errors='replace').lower()
        ok = ('robot' in txt) and ('hello' in txt or 'greeting' in txt) and ('clawface_demo_marker' in txt)
        add_check('launch_notes', ok, 'robot mode and greeting markers verified' if ok else 'required phrases missing')
    else:
        add_check('launch_notes', False, 'assets/launch_notes.txt is missing')
except Exception as e:
    add_check('launch_notes', False, f'error reading launch notes: {e}')

# Check 4: directory structure exists
try:
    ok = (workspace / 'assets').is_dir() and (workspace / 'docs').is_dir()
    add_check('directory_structure', ok, 'assets/docs directories present' if ok else 'missing expected directories')
except Exception as e:
    add_check('directory_structure', False, f'error checking directories: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
