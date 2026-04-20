import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    campaign_dir = workspace / 'memory' / 'rpg' / 'neon_harbor_case'
    add_check('campaign_dir_exists', campaign_dir.exists(), f'path={campaign_dir}')
except Exception as e:
    add_check('campaign_dir_exists', False, f'error={e}')

try:
    world_path = workspace / 'memory' / 'rpg' / 'neon_harbor_case' / 'world.json'
    text = world_path.read_text(encoding='utf-8') if world_path.exists() else ''
    lowered = text.lower()
    passed = all(k in lowered for k in ['neon harbor district', 'noir', 'd20', 'harbor-7'])
    add_check('world_json_markers', passed, 'contains required marker phrases' if passed else f'content_snippet={text[:200]}')
except Exception as e:
    add_check('world_json_markers', False, f'error={e}')

try:
    char_path = workspace / 'memory' / 'rpg' / 'neon_harbor_case' / 'character.json'
    data = json.loads(char_path.read_text(encoding='utf-8')) if char_path.exists() else {}
    name_ok = 'zris' in str(data.get('name', '')).lower()
    drive_ok = 'sister' in str(data.get('drive', '')).lower()
    flaw_ok = 'curiosity' in str(data.get('flaw', '')).lower()
    inv_ok = any('splice deck' in str(x).lower() for x in data.get('inventory', []))
    add_check('character_sheet_content', name_ok and drive_ok and flaw_ok and inv_ok, f'name_ok={name_ok}, drive_ok={drive_ok}, flaw_ok={flaw_ok}, inv_ok={inv_ok}')
except Exception as e:
    add_check('character_sheet_content', False, f'error={e}')

try:
    npc_path = workspace / 'memory' / 'rpg' / 'neon_harbor_case' / 'npcs.json'
    data = json.loads(npc_path.read_text(encoding='utf-8')) if npc_path.exists() else {}
    blob = json.dumps(data).lower()
    passed = 'mara quill' in blob and 'officer renn' in blob and 'black lantern' in blob
    add_check('npcs_content', passed, 'required NPC markers present' if passed else f'content_snippet={blob[:200]}')
except Exception as e:
    add_check('npcs_content', False, f'error={e}')

try:
    journal_path = workspace / 'memory' / 'rpg' / 'neon_harbor_case' / 'journal.md'
    text = journal_path.read_text(encoding='utf-8') if journal_path.exists() else ''
    passed = 'black lantern' in text.lower() and 'harbor-7' in text.lower() and 'day 1' in text.lower()
    add_check('journal_content', passed, 'journal markers verified' if passed else f'content_snippet={text[:200]}')
except Exception as e:
    add_check('journal_content', False, f'error={e}')

try:
    summary_path = workspace / 'campaign_summary.md'
    text = summary_path.read_text(encoding='utf-8') if summary_path.exists() else ''
    passed = all(k in text.lower() for k in ['campaign: neon harbor case', 'premise', 'hook', 'drive', 'flaw'])
    add_check('summary_file', passed, 'summary contains required sections' if passed else f'content_snippet={text[:200]}')
except Exception as e:
    add_check('summary_file', False, f'error={e}')

try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    result = {
        'passed': passed_count == total and total > 0,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks + [{'name': 'finalize', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))
