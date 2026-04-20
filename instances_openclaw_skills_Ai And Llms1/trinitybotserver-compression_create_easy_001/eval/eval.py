import json
import os
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def check_exists(path, label):
    try:
        p = Path(path)
        return p.exists(), f'{label}: {'exists' if p.exists() else 'missing'}'
    except Exception as e:
        return False, f'{label}: error {e}'

workspace = Path(__file__).resolve().parent if '__file__' in globals() else Path.cwd()
# The harness passes workspace directory as argv[1]; preserve robustness.
import sys
if len(sys.argv) > 1:
    workspace = Path(sys.argv[1])

checks = []

required = [
    'trinity-compress.config.json',
    'scripts/trinity-compress.sh',
    'scripts/install.ps1',
    'scripts/install.sh',
    'Makefile',
    '.gitignore'
]

for rel in required:
    try:
        p = workspace / rel
        ok = p.exists()
        checks.append({'name': f'exists:{rel}', 'passed': ok, 'detail': 'found' if ok else 'missing'})
    except Exception as e:
        checks.append({'name': f'exists:{rel}', 'passed': False, 'detail': f'error: {e}'})

# config content
try:
    p = workspace / 'trinity-compress.config.json'
    if p.exists():
        data = json.loads(p.read_text(encoding='utf-8'))
        targets = str(data.get('targets', '')).lower()
        ok = 'prompt' in targets or 'skill' in targets or 'agent' in targets or len(data) > 0
        checks.append({'name': 'config-json', 'passed': ok, 'detail': f'keys={list(data.keys())}'})
    else:
        checks.append({'name': 'config-json', 'passed': False, 'detail': 'missing'})
except Exception as e:
    checks.append({'name': 'config-json', 'passed': False, 'detail': f'error: {e}'})

# script markers
script_expectations = {
    'scripts/trinity-compress.sh': 'trinity-compress',
    'scripts/install.sh': 'install',
    'scripts/install.ps1': 'install',
}
for rel, needle in script_expectations.items():
    try:
        p = workspace / rel
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='ignore').lower()
            ok = needle in text
            checks.append({'name': f'content:{rel}', 'passed': ok, 'detail': 'contains marker' if ok else 'marker not found'})
        else:
            checks.append({'name': f'content:{rel}', 'passed': False, 'detail': 'missing'})
    except Exception as e:
        checks.append({'name': f'content:{rel}', 'passed': False, 'detail': f'error: {e}'})

# Makefile and gitignore fuzzy checks
try:
    mf = workspace / 'Makefile'
    if mf.exists():
        text = mf.read_text(encoding='utf-8', errors='ignore').lower()
        ok = ('optimize-prompts' in text) or ('optimize-undo' in text) or ('trinity-compress' in text)
        checks.append({'name': 'makefile-targets', 'passed': ok, 'detail': 'target names found' if ok else 'expected targets missing'})
    else:
        checks.append({'name': 'makefile-targets', 'passed': False, 'detail': 'missing'})
except Exception as e:
    checks.append({'name': 'makefile-targets', 'passed': False, 'detail': f'error: {e}'})

try:
    gi = workspace / '.gitignore'
    if gi.exists():
        text = gi.read_text(encoding='utf-8', errors='ignore').lower().replace(' ', '')
        ok = '*.bak' in text or '.bak' in text
        checks.append({'name': 'gitignore-bak', 'passed': ok, 'detail': 'bak ignored' if ok else 'bak rule missing'})
    else:
        checks.append({'name': 'gitignore-bak', 'passed': False, 'detail': 'missing'})
except Exception as e:
    checks.append({'name': 'gitignore-bak', 'passed': False, 'detail': f'error: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
passed = all(c.get('passed') for c in checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
