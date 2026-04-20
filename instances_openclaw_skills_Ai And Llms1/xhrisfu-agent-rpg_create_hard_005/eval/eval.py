import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

try:
    target = workspace / 'memory' / 'rpg' / 'black_sun_protocol'
    checks.append({
        'name': 'campaign_directory_exists',
        'passed': target.exists(),
        'detail': f'path={target}'
    })
except Exception as e:
    checks.append({'name': 'campaign_directory_exists', 'passed': False, 'detail': f'error={e}'})

files = ['world.json', 'character.json', 'npcs.json', 'journal.md']
for fname in files:
    try:
        p = workspace / 'memory' / 'rpg' / 'black_sun_protocol' / fname
        checks.append({
            'name': f'{fname}_exists',
            'passed': p.exists(),
            'detail': f'path={p}'
        })
    except Exception as e:
        checks.append({'name': f'{fname}_exists', 'passed': False, 'detail': f'error={e}'})

try:
    p = workspace / 'memory' / 'rpg' / 'black_sun_protocol' / 'journal.md'
    txt = p.read_text(encoding='utf-8') if p.exists() else ''
    ok = 'synth-1337' in txt.lower() and 'neon chapel' in txt.lower()
    checks.append({'name': 'journal_marker_content', 'passed': ok, 'detail': 'marker and setting phrases checked case-insensitively'})
except Exception as e:
    checks.append({'name': 'journal_marker_content', 'passed': False, 'detail': f'error={e}'})

try:
    p = workspace / 'memory' / 'rpg' / 'black_sun_protocol' / 'world.json'
    data = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    ok = str(data.get('system_mode', '')).lower() == 'd20' or 'd20' in str(data.get('system_mode', '')).lower()
    ok = ok and 'acid rain' in str(data.get('weather', '')).lower()
    checks.append({'name': 'world_json_properties', 'passed': ok, 'detail': 'system mode and weather verified fuzzily'})
except Exception as e:
    checks.append({'name': 'world_json_properties', 'passed': False, 'detail': f'error={e}'})

try:
    p = workspace / 'memory' / 'rpg' / 'black_sun_protocol' / 'character.json'
    data = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    inv = ' '.join(map(str, data.get('inventory', []))).lower()
    ok = 'plasma pistol' in inv and 'access keycard' in inv
    checks.append({'name': 'character_inventory', 'passed': ok, 'detail': 'inventory contains key items'})
except Exception as e:
    checks.append({'name': 'character_inventory', 'passed': False, 'detail': f'error={e}'})

try:
    p = workspace / 'memory' / 'rpg' / 'black_sun_protocol' / 'npcs.json'
    data = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    boss = str(data.get('boss', {}).get('name', '')).lower()
    rival = str(data.get('rival', {}).get('name', '')).lower()
    ok = 'sister vale' in boss and 'morrow' in rival
    checks.append({'name': 'npcs_json_names', 'passed': ok, 'detail': 'npc names verified'})
except Exception as e:
    checks.append({'name': 'npcs_json_names', 'passed': False, 'detail': f'error={e}'})

try:
    p = workspace / 'marker.txt'
    ok = p.exists() and 'black_sun_protocol' in p.read_text(encoding='utf-8').lower()
    checks.append({'name': 'root_marker_file', 'passed': ok, 'detail': 'root marker checked'})
except Exception as e:
    checks.append({'name': 'root_marker_file', 'passed': False, 'detail': f'error={e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))
