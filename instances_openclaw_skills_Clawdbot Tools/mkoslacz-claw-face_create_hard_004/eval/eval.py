import json
import os
import re
from pathlib import Path

workspace = Path(__file__).resolve().parent
# The harness will pass the workspace path as argv[1]
import sys
if len(sys.argv) > 1:
    workspace = Path(sys.argv[1])

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    # Check for state file with flexible naming (search recursively)
    state_path = None
    possible_state_names = [
        'clawface_state.json', 'state.json', 'clawface_state.txt', 'avatar_state.json',
        'clawface_demo_output.json', 'demo_output.json', 'output.json', 'clawface_output.json'
    ]
    
    # Search workspace root first
    for name in possible_state_names:
        path = workspace / name
        if path.exists():
            state_path = path
            break
    
    # If not found, search recursively
    if not state_path:
        for root, dirs, files in os.walk(workspace):
            for name in possible_state_names:
                path = Path(root) / name
                if path.exists():
                    state_path = path
                    break
            if state_path:
                break
    
    # Also check for shell scripts that produce state sequences
    script_path = None
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.endswith('.sh') and 'clawface' in f.lower():
                script_path = Path(root) / f
                break
        if script_path:
            break
    
    if not state_path and not script_path:
        add_check('state file exists', False, 'Missing state file (clawface_state.json or similar) or demo script')
    else:
        if state_path:
            try:
                data = json.loads(state_path.read_text(encoding='utf-8'))
                has_sequence = 'state_sequence' in data or 'sequence' in data or 'states' in data
                has_states = any('state' in str(v).lower() for v in data.values())
                has_marker = 'marker' in data or 'clawface' in str(data).lower()
                ok = has_sequence or has_states or has_marker
                add_check('state file exists', True, f"Found state file: {state_path.name}")
                add_check('state json content', ok, f"has_sequence={has_sequence}, has_states={has_states}, has_marker={has_marker}")
            except Exception as e:
                add_check('state file exists', True, f"Found state file but parse error: {e}")
                add_check('state json content', False, f'Failed to parse state JSON: {e}')
        elif script_path:
            try:
                content = script_path.read_text(encoding='utf-8', errors='ignore').lower()
                has_sequence = any(term in content for term in ['thinking', 'searching', 'coding', 'success', 'state'])
                has_clawface = 'clawface' in content
                ok = has_sequence and has_clawface
                add_check('state file exists', True, f"Found demo script: {script_path.name}")
                add_check('state json content', ok, f"Script contains state sequence: {has_sequence}, clawface: {has_clawface}")
            except Exception as e:
                add_check('state file exists', True, f"Found script but read error: {e}")
                add_check('state json content', False, f'Failed to read script: {e}')

    # Check for usage note with flexible naming (search recursively)
    note_path = None
    possible_note_names = [
        'USAGE_NOTE.txt', 'CLAWFACE_USAGE.md', 'usage_notes.md', 'USAGE.md', 'README.md', 
        'usage_notes.txt', 'USAGE_NOTES.md', 'usage.md', 'CLAWFACE_README.md', 'USAGE_NOTES.txt'
    ]
    
    # Search workspace root first
    for name in possible_note_names:
        path = workspace / name
        if path.exists():
            note_path = path
            break
    
    # If not found, search recursively
    if not note_path:
        for root, dirs, files in os.walk(workspace):
            for name in possible_note_names:
                path = Path(root) / name
                if path.exists():
                    note_path = path
                    break
            if note_path:
                break
    
    # Also check for any .txt or .md file with usage-related content
    if not note_path:
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.endswith(('.txt', '.md')):
                    path = Path(root) / f
                    try:
                        content = path.read_text(encoding='utf-8', errors='ignore').lower()
                        if any(term in content for term in ['usage', 'demo', 'clawface', 'hook', 'thinking']):
                            note_path = path
                            break
                    except:
                        pass
            if note_path:
                break
    
    if not note_path:
        add_check('usage note exists', False, 'Missing usage note (USAGE_NOTE.txt, CLAWFACE_USAGE.md, or similar)')
    else:
        try:
            text = note_path.read_text(encoding='utf-8', errors='ignore').lower()
            required_terms = ['clawface', 'thinking', 'hook', 'avatar', 'demo']
            found = sum(1 for term in required_terms if term in text)
            add_check('usage note exists', True, f"Found usage note: {note_path.name}")
            add_check('usage note content', found >= 3, f'Found {found}/5 required terms')
        except Exception as e:
            add_check('usage note exists', True, f"Found note but read error: {e}")
            add_check('usage note content', False, f'Error reading usage note: {e}')

    # Check for input marker file
    try:
        marker_file = workspace / 'input_data' / 'clawface_markers.json'
        if not marker_file.exists():
            add_check('input marker file', False, 'Missing input_data/clawface_markers.json')
        else:
            obj = json.loads(marker_file.read_text(encoding='utf-8'))
            marker = str(obj.get('marker', ''))
            seq = obj.get('sequence', [])
            ok = 'clawface_marker_alpha_913' in marker.lower() and isinstance(seq, list) and len(seq) >= 4
            add_check('input marker file', ok, f'marker_present={"clawface_marker_alpha_913" in marker.lower()}, sequence_len={len(seq) if isinstance(seq, list) else "n/a"}')
    except Exception as e:
        add_check('input marker file', False, f'Error checking marker file: {e}')

except Exception as e:
    add_check('top-level eval failure', False, f'Unexpected eval error: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": all(c['passed'] for c in checks) if checks else False, "score": score, "checks": checks}
print(json.dumps(result, indent=2))