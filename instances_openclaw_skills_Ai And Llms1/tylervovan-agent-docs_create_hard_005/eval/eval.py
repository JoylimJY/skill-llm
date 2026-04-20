import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def read_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, e


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower()) if isinstance(s, str) else ''

try:
    agents = workspace / 'AGENTS.md'
    llms = workspace / 'llms.txt'

    # Check 1: AGENTS.md exists and contains governance + marker-aware map
    try:
        txt = agents.read_text(encoding='utf-8')
        required_bits = ['critical', 'docs index', 'app/', 'no secrets', 'read_file']
        passed = all(norm(bit) in norm(txt) for bit in required_bits)
        detail = 'AGENTS.md includes governance and retrieval map' if passed else 'AGENTS.md missing one or more required themes'
    except Exception as e:
        passed = False
        detail = f'Could not read AGENTS.md: {e}'
    add_check('agents_exists_and_content', passed, detail)

    # Check 2: llms.txt exists and has concise index entries for auth/db
    try:
        txt = llms.read_text(encoding='utf-8')
        passed = all(norm(bit) in norm(txt) for bit in ['authentication', 'database', 'quickstart', 'setup', 'schema'])
        detail = 'llms.txt contains expected high-level sections' if passed else 'llms.txt missing expected sections or descriptions'
    except Exception as e:
        passed = False
        detail = f'Could not read llms.txt: {e}'
    add_check('llms_index_content', passed, detail)

    # Check 3: output should be compact and not reference nonexistent files
    try:
        txt = agents.read_text(encoding='utf-8') if agents.exists() else ''
        forbidden = ['pages/', 'nonexistent', 'marketing', 'welcome to']
        passed = not any(norm(bit) in norm(txt) for bit in forbidden)
        detail = 'AGENTS.md avoids forbidden or irrelevant references' if passed else 'AGENTS.md contains disallowed references'
    except Exception as e:
        passed = False
        detail = f'Error checking forbidden references: {e}'
    add_check('no_forbidden_references', passed, detail)

    # Check 4: referenced docs are discoverable via paths mentioned in docs
    try:
        txt = llms.read_text(encoding='utf-8') if llms.exists() else ''
        path_hits = [p for p in ['docs/auth/setup.md', 'docs/auth/server.md', 'docs/db/schema.md'] if norm(p) in norm(txt)]
        passed = len(path_hits) >= 2
        detail = f'Found referenced doc paths: {path_hits}' if passed else 'Too few referenced doc paths in llms.txt'
    except Exception as e:
        passed = False
        detail = f'Error checking doc paths: {e}'
    add_check('doc_path_references', passed, detail)

except Exception as outer_e:
    add_check('fatal_guard', False, f'Unexpected error: {outer_e}')

passed_all = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed_all, "score": score, "checks": checks}))
