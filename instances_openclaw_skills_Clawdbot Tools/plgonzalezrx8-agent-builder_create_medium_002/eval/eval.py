import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def read_text_safe(path):
    try:
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def contains_fuzzy(text, needles):
    if not text:
        return False
    low = re.sub(r'\s+', ' ', text.lower())
    return all(n.lower() in low for n in needles)

# Required files
required = [
    'IDENTITY.md', 'SOUL.md', 'AGENTS.md', 'USER.md', 'HEARTBEAT.md', 'memory/2025-01-15.md'
]
for rel in required:
    p = workspace / rel
    try:
        ok = p.exists() and p.is_file()
        add_check(f'file_exists:{rel}', ok, 'present' if ok else 'missing')
    except Exception as e:
        add_check(f'file_exists:{rel}', False, f'error: {e}')

# Content checks
try:
    txt, err = read_text_safe(workspace / 'IDENTITY.md')
    if txt is None:
        add_check('identity_content', False, f'read error: {err}')
    else:
        ok = contains_fuzzy(txt, ['name', 'harbor'])
        add_check('identity_content', ok, 'contains Harbor' if ok else 'does not contain Harbor')
except Exception as e:
    add_check('identity_content', False, f'error: {e}')

try:
    txt, err = read_text_safe(workspace / 'SOUL.md')
    if txt is None:
        add_check('soul_content', False, f'read error: {err}')
    else:
        ok = contains_fuzzy(txt, ['calm']) and contains_fuzzy(txt, ['concise']) and contains_fuzzy(txt, ['destructive'])
        add_check('soul_content', ok, 'has calm/concise/destructive boundary' if ok else 'missing one or more expected traits')
except Exception as e:
    add_check('soul_content', False, f'error: {e}')

try:
    txt, err = read_text_safe(workspace / 'AGENTS.md')
    if txt is None:
        add_check('agents_content', False, f'read error: {err}')
    else:
        ok = contains_fuzzy(txt, ['group chats']) and contains_fuzzy(txt, ['sub-agents']) and contains_fuzzy(txt, ['stop on cli usage errors'])
        add_check('agents_content', ok, 'has group chat, sub-agent, and cli error guidance' if ok else 'missing operating rules')
except Exception as e:
    add_check('agents_content', False, f'error: {e}')

try:
    txt, err = read_text_safe(workspace / 'USER.md')
    if txt is None:
        add_check('user_content', False, f'read error: {err}')
    else:
        ok = contains_fuzzy(txt, ['alex']) and contains_fuzzy(txt, ['utc'])
        add_check('user_content', ok, 'contains Alex and UTC' if ok else 'missing user metadata')
except Exception as e:
    add_check('user_content', False, f'error: {e}')

try:
    txt, err = read_text_safe(workspace / 'HEARTBEAT.md')
    if txt is None:
        add_check('heartbeat_content', False, f'read error: {err}')
    else:
        ok = len(txt.strip()) > 0 and 'heartbeat' in txt.lower()
        add_check('heartbeat_content', ok, 'non-empty heartbeat file present' if ok else 'heartbeat missing content')
except Exception as e:
    add_check('heartbeat_content', False, f'error: {e}')

try:
    txt, err = read_text_safe(workspace / 'memory' / '2025-01-15.md')
    if txt is None:
        add_check('memory_log', False, f'read error: {err}')
    else:
        # Flexible check for agent initialization/creation in memory log
        init_patterns = ['agent created', 'agent initialized', 'agent setup', 'harbor initialized', 'harbor created', 'agent started']
        low = txt.lower()
        ok = any(pattern in low for pattern in init_patterns)
        add_check('memory_log', ok, 'contains agent initialization marker' if ok else 'missing initialization marker')
except Exception as e:
    add_check('memory_log', False, f'error: {e}')

# Score
passed_count = sum(1 for c in checks if c['passed'])
total = len(checks) if checks else 1
score = passed_count / total
result = {
    'passed': passed_count == total,
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))