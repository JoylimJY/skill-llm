import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

try:
    # Check avatar state file
    state_path = workspace / 'avatar_state.json'
    
    if state_path.exists():
        try:
            data = json.loads(state_path.read_text(encoding='utf-8'))
            marker_ok = 'emotion' in data and 'action' in data and 'effect' in data and 'message' in data
            # Accept cheerful, happy, excited, proud as valid cheerful emotions
            emotion_val = str(data.get('emotion', '')).lower()
            cheerful = emotion_val in {'happy', 'excited', 'proud', 'cheerful', 'joyful'}
            add_check('avatar_state_present_and_valid', marker_ok and cheerful, f"keys={sorted(list(data.keys())) if isinstance(data, dict) else 'non-dict'}, emotion={data.get('emotion') if isinstance(data, dict) else 'n/a'}")
        except Exception as e:
            add_check('avatar_state_present_and_valid', False, f'Could not parse avatar_state.json: {e}')
    else:
        add_check('avatar_state_present_and_valid', False, 'avatar_state.json is missing')

    # Check for launch note - accept any .txt or .md file with launch instructions
    note_found = False
    note_valid = False
    note_detail = 'No launch note file found'
    
    for filepath in workspace.iterdir():
        if filepath.suffix.lower() in ['.txt', '.md'] and filepath.name != 'README_INPUT.txt':
            try:
                text = filepath.read_text(encoding='utf-8')
                # Check for keywords indicating launch instructions
                has_demo = 'demo' in text.lower()
                has_clawface = 'clawface' in text.lower()
                has_launch = 'launch' in text.lower() or 'start' in text.lower() or 'run' in text.lower()
                
                if has_demo and (has_clawface or has_launch):
                    note_found = True
                    note_valid = True
                    note_detail = f'{filepath.name} exists and contains required launch guidance'
                    break
            except Exception as e:
                continue
    
    add_check('launch_note_present', note_valid, note_detail)

    # Check input marker
    expected_input = workspace / 'README_INPUT.txt'
    if expected_input.exists():
        try:
            txt = expected_input.read_text(encoding='utf-8')
            add_check('input_marker_exists', 'clawface_marker' in txt.lower(), 'Deterministic marker found in README_INPUT.txt' if 'clawface_marker' in txt.lower() else 'Marker not found in README_INPUT.txt')
        except Exception as e:
            add_check('input_marker_exists', False, f'Could not read README_INPUT.txt: {e}')
    else:
        add_check('input_marker_exists', False, 'README_INPUT.txt is missing')
except Exception as e:
    add_check('evaluation_bootstrap', False, f'Unexpected evaluation error: {e}')

passed = all(c['passed'] for c in checks)
score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))