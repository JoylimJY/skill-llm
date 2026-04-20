import json
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'failed to read {path.name}: {e}'


def norm(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' '.join(s.split())


def contains_all(text: str, snippets):
    ntext = norm(text)
    return all(norm(snippet) in ntext for snippet in snippets)

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

try:
    agents = workspace / 'AGENTS.md'
    if agents.exists():
        txt, err = safe_read(agents)
        if txt is None:
            checks.append({'name': 'AGENTS.md readable', 'passed': False, 'detail': err})
        else:
            reqs = ['agent docs', 'critical', 'docs index', 'build', 'test', 'auth', 'db']
            passed = contains_all(txt, reqs)
            checks.append({'name': 'AGENTS.md content', 'passed': passed, 'detail': 'contains required sections and references' if passed else 'missing one or more required ideas'})
    else:
        checks.append({'name': 'AGENTS.md exists', 'passed': False, 'detail': 'AGENTS.md file is missing'})
except Exception as e:
    checks.append({'name': 'AGENTS.md check', 'passed': False, 'detail': f'error: {e}'})

try:
    auth = workspace / 'docs' / 'auth' / 'llms.txt'
    txt, err = safe_read(auth)
    if txt is None:
        checks.append({'name': 'auth doc marker', 'passed': False, 'detail': err})
    else:
        passed = contains_all(txt, ['AUTH-LOCK-17', 'server-side session checks'])
        checks.append({'name': 'auth doc marker', 'passed': passed, 'detail': 'auth marker found' if passed else 'expected auth marker missing'})
except Exception as e:
    checks.append({'name': 'auth doc marker', 'passed': False, 'detail': f'error: {e}'})

try:
    db = workspace / 'docs' / 'db' / 'schema.md'
    txt, err = safe_read(db)
    if txt is None:
        checks.append({'name': 'db doc marker', 'passed': False, 'detail': err})
    else:
        passed = contains_all(txt, ['DB-SCHEMA-42', 'users', 'sessions', 'audit logs'])
        checks.append({'name': 'db doc marker', 'passed': passed, 'detail': 'db marker found' if passed else 'expected db marker missing'})
except Exception as e:
    checks.append({'name': 'db doc marker', 'passed': False, 'detail': f'error: {e}'})

try:
    ref = workspace / 'references' / 'advanced-patterns.md'
    txt, err = safe_read(ref)
    if txt is None:
        checks.append({'name': 'reference marker', 'passed': False, 'detail': err})
    else:
        passed = contains_all(txt, ['ADV-RAG-09', 'security hardening'])
        checks.append({'name': 'reference marker', 'passed': passed, 'detail': 'reference marker found' if passed else 'expected reference marker missing'})
except Exception as e:
    checks.append({'name': 'reference marker', 'passed': False, 'detail': f'error: {e}'})

try:
    readme = workspace / 'README.md'
    passed = readme.exists()
    checks.append({'name': 'repo has README', 'passed': passed, 'detail': 'README.md exists' if passed else 'README.md missing'})
except Exception as e:
    checks.append({'name': 'repo has README', 'passed': False, 'detail': f'error: {e}'})

score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
result = {'passed': all(c.get('passed') for c in checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
