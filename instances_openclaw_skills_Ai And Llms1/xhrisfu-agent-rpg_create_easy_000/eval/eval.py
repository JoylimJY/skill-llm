import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read file: {e}'

try:
    world_path = workspace / 'memory' / 'rpg' / 'neon_dream' / 'world.json'
    char_path = workspace / 'memory' / 'rpg' / 'neon_dream' / 'character.json'
    journal_path = workspace / 'memory' / 'rpg' / 'neon_dream' / 'journal.md'

    # world.json
    try:
        txt = world_path.read_text(encoding='utf-8')
        data = json.loads(txt)
        ok = True
        detail_parts = []
        if 'neon_dream' not in str(data).lower():
            ok = False
            detail_parts.append('missing campaign name')
        if 'cyberpunk' not in str(data).lower():
            ok = False
            detail_parts.append('missing setting')
        if 'gritty' not in str(data).lower():
            ok = False
            detail_parts.append('missing tone')
        if 'd20' not in str(data).lower():
            ok = False
            detail_parts.append('missing system')
        if 'session_zero_started' in data and data.get('session_zero_started') is not False:
            ok = False
            detail_parts.append('session_zero_started should be false')
        add_check('world.json content', ok, '; '.join(detail_parts) if detail_parts else 'ok')
    except Exception as e:
        add_check('world.json content', False, f'error: {e}')

    # character.json
    try:
        txt = char_path.read_text(encoding='utf-8')
        data = json.loads(txt)
        ok = True
        detail_parts = []
        if 'zris' not in str(data).lower():
            ok = False
            detail_parts.append('missing character name')
        if 'hacker' not in str(data).lower():
            ok = False
            detail_parts.append('missing archetype')
        if 'data shard' not in str(data).lower():
            ok = False
            detail_parts.append('missing inventory item')
        add_check('character.json content', ok, '; '.join(detail_parts) if detail_parts else 'ok')
    except Exception as e:
        add_check('character.json content', False, f'error: {e}')

    # journal.md
    try:
        txt = journal_path.read_text(encoding='utf-8').lower()
        ok = 'marker_neon_dream_001' in txt and 'session zero has not started yet' in txt
        detail = 'ok' if ok else 'missing marker or status note'
        add_check('journal marker', ok, detail)
    except Exception as e:
        add_check('journal marker', False, f'error: {e}')

except Exception as e:
    add_check('overall exception', False, f'error: {e}')

passed = all(c['passed'] for c in checks) if checks else False
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
