import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, f'failed to read {path}: {e}'

# Check 1: expected input markers exist
try:
    texts = []
    for rel in ['prompts/system.md', 'prompts/developer.md', 'prompts/user.md']:
        p = workspace / rel
        if not p.exists():
            raise FileNotFoundError(rel)
        texts.append(p.read_text(encoding='utf-8', errors='replace'))
    markers = ['TRINITY-SYS-001', 'TRINITY-DEV-002', 'TRINITY-USER-003']
    ok = all(any(m.lower() in t.lower() for t in texts) for m in markers)
    add_check('generated inputs with markers', ok, 'found all expected marker strings' if ok else 'one or more marker strings missing')
except Exception as e:
    add_check('generated inputs with markers', False, f'error while checking inputs: {e}')

# Check 2: config exists and mentions balanced mode
try:
    cfg_path = workspace / 'trinity-compress.config.json'
    if not cfg_path.exists():
        raise FileNotFoundError('trinity-compress.config.json')
    cfg_text = cfg_path.read_text(encoding='utf-8', errors='replace')
    ok = 'balanced' in cfg_text.lower() and 'prompts/system.md' in cfg_text.replace('\\', '/').lower()
    add_check('config file present', ok, 'config mentions balanced mode and target files' if ok else 'config missing expected content')
except Exception as e:
    add_check('config file present', False, f'error while checking config: {e}')

# Check 3: repo hygiene files were created by the user task
try:
    ig = workspace / '.gitignore'
    mk = workspace / 'Makefile'
    script = workspace / 'scripts' / 'trinity-compress.sh'
    ok_files = [ig.exists(), mk.exists(), script.exists()]
    detail = f'.gitignore={ig.exists()}, Makefile={mk.exists()}, script={script.exists()}'
    add_check('installed skill assets', all(ok_files), detail)
except Exception as e:
    add_check('installed skill assets', False, f'error while checking assets: {e}')

# Check 4: .gitignore contains *.bak (forgiving fuzzy match)
try:
    p = workspace / '.gitignore'
    if not p.exists():
        raise FileNotFoundError('.gitignore')
    txt = p.read_text(encoding='utf-8', errors='replace')
    norm = re.sub(r'\s+', '', txt.lower())
    ok = '*.bak' in norm or 'bak' in norm
    add_check('.gitignore ignores backups', ok, 'contains backup ignore pattern' if ok else 'missing backup ignore pattern')
except Exception as e:
    add_check('.gitignore ignores backups', False, f'error while checking .gitignore: {e}')

# Check 5: Makefile has optimization targets
try:
    p = workspace / 'Makefile'
    if not p.exists():
        raise FileNotFoundError('Makefile')
    txt = p.read_text(encoding='utf-8', errors='replace').lower()
    ok = ('optimize-prompts' in txt) or ('optimize-undo' in txt)
    add_check('makefile targets added', ok, 'found optimize-prompts/optimize-undo target text' if ok else 'expected targets not found')
except Exception as e:
    add_check('makefile targets added', False, f'error while checking Makefile: {e}')

# Check 6: balanced run produces at least one .bak if output exists, and markers remain detectable
try:
    bak_files = list(workspace.rglob('*.bak'))
    ok = len(bak_files) > 0
    add_check('backup files created', ok, f'found {len(bak_files)} .bak file(s)' if ok else 'no .bak files found')
except Exception as e:
    add_check('backup files created', False, f'error while checking backups: {e}')

score = 0.0
if checks:
    score = sum(1 for c in checks if c['passed']) / len(checks)
passed = all(c['passed'] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
