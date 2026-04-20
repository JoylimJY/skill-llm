import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, e


def normalize(s):
    return re.sub(r'[^a-z0-9]+', ' ', s.lower()).strip()

try:
    agents_path = workspace / 'AGENTS.md'
    if agents_path.exists():
        text = agents_path.read_text(encoding='utf-8')
        n = normalize(text)
        has_top = 'critical' in n and ('no secrets' in n or 'do not use secrets' in n)
        has_index = 'docs index' in n and ('read_file' in n or 'docs/auth/llms txt' in n)
        has_cmds = 'build' in n and 'test' in n and 'lint' in n
        add_check('AGENTS.md exists', True, 'AGENTS.md found')
        add_check('Top governance present', has_top, 'Looks for critical governance and no-secrets rule')
        add_check('Docs index present', has_index, 'Looks for a docs index pointing to auth/db references')
        add_check('Commands listed', has_cmds, 'Looks for build/test/lint commands in the top section')
    else:
        add_check('AGENTS.md exists', False, 'AGENTS.md missing')
        add_check('Top governance present', False, 'Cannot inspect missing file')
        add_check('Docs index present', False, 'Cannot inspect missing file')
        add_check('Commands listed', False, 'Cannot inspect missing file')
except Exception as e:
    add_check('AGENTS.md inspection', False, f'Error: {e}')

try:
    ref_path = workspace / 'references' / 'advanced-patterns.md'
    if ref_path.exists():
        text = ref_path.read_text(encoding='utf-8')
        n = normalize(text)
        add_check('Reference file exists', True, 'references/advanced-patterns.md found')
        add_check('Reference covers advanced patterns', all(k in n for k in ['compressed index', 'llms txt', 'security hardening']), 'Expected advanced patterns content detected')
    else:
        add_check('Reference file exists', False, 'references/advanced-patterns.md missing')
        add_check('Reference covers advanced patterns', False, 'Cannot inspect missing file')
except Exception as e:
    add_check('Reference inspection', False, f'Error: {e}')

try:
    auth_path = workspace / 'docs' / 'auth' / 'llms.txt'
    db_path = workspace / 'docs' / 'db' / 'schema.md'
    auth_ok = False
    db_ok = False
    if auth_path.exists():
        auth_text = auth_path.read_text(encoding='utf-8')
        a = normalize(auth_text)
        auth_ok = 'session' in a and 'middleware' in a and 'environment vars' in a
    if db_path.exists():
        db_text = db_path.read_text(encoding='utf-8')
        d = normalize(db_text)
        db_ok = 'users' in d and 'sessions' in d and 'payments' in d
    add_check('Auth doc exists', auth_path.exists(), 'docs/auth/llms.txt should exist')
    add_check('DB doc exists', db_path.exists(), 'docs/db/schema.md should exist')
    add_check('Auth doc content', auth_ok, 'Auth doc should mention env vars, session handling, and middleware')
    add_check('DB doc content', db_ok, 'DB doc should mention users, sessions, and payments')
except Exception as e:
    add_check('Supporting docs inspection', False, f'Error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
total = len(checks)
score = passed_count / total if total else 0.0
passed = total > 0 and passed_count == total
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
