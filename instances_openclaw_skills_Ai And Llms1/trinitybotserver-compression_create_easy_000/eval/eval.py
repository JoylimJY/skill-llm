import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    cfg = workspace / 'trinity-compress.config.json'
    if cfg.exists():
        txt = cfg.read_text(encoding='utf-8', errors='replace')
        ok = 'balanced' in txt.lower() or 'targets' in txt.lower()
        add_check('config_exists', True, 'Found trinity-compress.config.json')
        add_check('config_content', ok, 'Config contains expected rule/target markers' if ok else 'Config content missing expected markers')
    else:
        add_check('config_exists', False, 'Missing trinity-compress.config.json')
        add_check('config_content', False, 'Cannot inspect missing config')
except Exception as e:
    add_check('config_exists', False, f'Error checking config: {e}')
    add_check('config_content', False, f'Error checking config: {e}')

try:
    script = workspace / 'scripts' / 'trinity-compress.sh'
    if script.exists():
        txt = script.read_text(encoding='utf-8', errors='replace').lower()
        ok = 'backup' in txt or '.bak' in txt or 'balanced' in txt
        add_check('compress_script_exists', True, 'Found scripts/trinity-compress.sh')
        add_check('compress_script_content', ok, 'Compression script has expected behavior markers' if ok else 'Compression script content missing expected markers')
    else:
        add_check('compress_script_exists', False, 'Missing scripts/trinity-compress.sh')
        add_check('compress_script_content', False, 'Cannot inspect missing compression script')
except Exception as e:
    add_check('compress_script_exists', False, f'Error checking compression script: {e}')
    add_check('compress_script_content', False, f'Error checking compression script: {e}')

for fname, label in [('scripts/install.sh', 'install_sh_exists'), ('scripts/install.ps1', 'install_ps1_exists')]:
    try:
        p = workspace / fname
        add_check(label, p.exists(), f'Found {fname}' if p.exists() else f'Missing {fname}')
    except Exception as e:
        add_check(label, False, f'Error checking {fname}: {e}')

try:
    mf = workspace / 'Makefile'
    if mf.exists():
        txt = mf.read_text(encoding='utf-8', errors='replace').lower()
        ok = 'optimize-prompts' in txt and 'optimize-undo' in txt
        add_check('makefile_exists', True, 'Found Makefile')
        add_check('makefile_targets', ok, 'Makefile contains optimize-prompts and optimize-undo' if ok else 'Makefile missing expected targets')
    else:
        add_check('makefile_exists', False, 'Missing Makefile')
        add_check('makefile_targets', False, 'Cannot inspect missing Makefile')
except Exception as e:
    add_check('makefile_exists', False, f'Error checking Makefile: {e}')
    add_check('makefile_targets', False, f'Error checking Makefile: {e}')

try:
    gi = workspace / '.gitignore'
    if gi.exists():
        txt = gi.read_text(encoding='utf-8', errors='replace')
        ok = '*.bak' in txt
        add_check('gitignore_exists', True, 'Found .gitignore')
        add_check('gitignore_bak_rule', ok, 'Contains *.bak ignore rule' if ok else 'Missing *.bak ignore rule')
    else:
        add_check('gitignore_exists', False, 'Missing .gitignore')
        add_check('gitignore_bak_rule', False, 'Cannot inspect missing .gitignore')
except Exception as e:
    add_check('gitignore_exists', False, f'Error checking .gitignore: {e}')
    add_check('gitignore_bak_rule', False, f'Error checking .gitignore: {e}')

try:
    marker = workspace / 'input_marker.txt'
    if marker.exists():
        txt = marker.read_text(encoding='utf-8', errors='replace')
        ok = 'TRINITY_COMPRESS_MARKER' in txt
        add_check('marker_present', ok, 'Input marker content present' if ok else 'Marker missing or altered')
    else:
        add_check('marker_present', False, 'Missing input marker file')
except Exception as e:
    add_check('marker_present', False, f'Error checking marker: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
