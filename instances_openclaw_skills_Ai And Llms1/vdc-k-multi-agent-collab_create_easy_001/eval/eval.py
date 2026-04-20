import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read {path.name}: {e}'

try:
    # 1) TASK.md exists
    p = workspace / 'TASK.md'
    try:
        exists = p.exists()
        add_check('TASK.md exists', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check('TASK.md exists', False, f'error checking existence: {e}')

    # 2) CHANGELOG.md exists
    p = workspace / 'CHANGELOG.md'
    try:
        exists = p.exists()
        add_check('CHANGELOG.md exists', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check('CHANGELOG.md exists', False, f'error checking existence: {e}')

    # 3) CONTEXT.md exists
    p = workspace / 'CONTEXT.md'
    try:
        exists = p.exists()
        add_check('CONTEXT.md exists', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check('CONTEXT.md exists', False, f'error checking existence: {e}')

    # 4) llms.txt exists
    p = workspace / 'llms.txt'
    try:
        exists = p.exists()
        add_check('llms.txt exists', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check('llms.txt exists', False, f'error checking existence: {e}')

    # 5) WEEKLY-REPORT.md exists
    p = workspace / 'WEEKLY-REPORT.md'
    try:
        exists = p.exists()
        add_check('WEEKLY-REPORT.md exists', exists, 'found' if exists else 'missing')
    except Exception as e:
        add_check('WEEKLY-REPORT.md exists', False, f'error checking existence: {e}')

    # 6) TASK.md mentions kickoff/new project
    try:
        text = (workspace / 'TASK.md').read_text(encoding='utf-8')
        norm = re.sub(r'[^a-z0-9]+', ' ', text.lower())
        ok = ('kickoff' in norm) or ('initial' in norm) or ('fresh project' in norm) or ('project' in norm and 'task' in norm)
        add_check('TASK.md content looks like kickoff', ok, 'contains kickoff-related wording' if ok else 'does not clearly indicate kickoff')
    except Exception as e:
        add_check('TASK.md content looks like kickoff', False, f'read/parsing failed: {e}')

    # 7) CHANGELOG.md mentions a tag or identity
    try:
        text = (workspace / 'CHANGELOG.md').read_text(encoding='utf-8')
        norm = text.lower()
        ok = ('#' in norm) or ('by ' in norm) or ('identity' in norm) or ('agent' in norm)
        add_check('CHANGELOG.md has tag or identity', ok, 'has #tag/identity-like content' if ok else 'missing tag/identity markers')
    except Exception as e:
        add_check('CHANGELOG.md has tag or identity', False, f'read/parsing failed: {e}')

    # 8) seed marker files created correctly
    try:
        note = (workspace / 'seed_note.txt').read_text(encoding='utf-8') if (workspace / 'seed_note.txt').exists() else ''
        proj = (workspace / 'project_name.txt').read_text(encoding='utf-8') if (workspace / 'project_name.txt').exists() else ''
        ok = ('marker_seed=42' in note.lower()) and ('marker_project=agent-sync-demo' in proj.lower())
        add_check('generated marker files present', ok, 'seed markers verified' if ok else 'missing or incorrect marker content')
    except Exception as e:
        add_check('generated marker files present', False, f'read/parsing failed: {e}')

except Exception as e:
    add_check('global evaluator safety', False, f'unexpected evaluator error handled: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
