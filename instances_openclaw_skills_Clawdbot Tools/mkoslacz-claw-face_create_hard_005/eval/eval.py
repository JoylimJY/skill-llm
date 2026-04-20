import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

# Check 1: input marker exists
try:
    marker_path = workspace / 'inputs' / 'marker.json'
    if marker_path.exists():
        data = json.loads(marker_path.read_text(encoding='utf-8'))
        marker_ok = 'CLAWFACE_DETERMINISTIC_MARKER_7F3A' in str(data)
        add_check('input_marker_present', marker_ok, 'Marker file found and marker verified.' if marker_ok else 'Marker file found but marker content did not match.')
    else:
        add_check('input_marker_present', False, 'Missing inputs/marker.json.')
except Exception as e:
    add_check('input_marker_present', False, f'Error reading marker file: {e}')

# Helper: find JSON files recursively
def find_json_files(base_path):
    json_files = []
    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.endswith('.json'):
                json_files.append(Path(root) / f)
    return json_files

# Check 2: avatar state file exists OR demo script exists
try:
    json_files = find_json_files(workspace)
    state_path = None
    
    for f in json_files:
        name_lower = f.name.lower()
        if any(term in name_lower for term in ['avatar', 'state', 'demo', 'output', 'clawface']):
            state_path = f
            break
    
    demo_script = None
    for f in workspace.glob('*.py'):
        if 'clawface' in f.name.lower() or 'demo' in f.name.lower():
            demo_script = f
            break
    
    if state_path:
        add_check('avatar_state_exists', True, f'Found avatar state file at {state_path}')
    elif demo_script:
        add_check('avatar_state_exists', True, f'Found demo script at {demo_script} (output not yet generated)')
    else:
        add_check('avatar_state_exists', False, 'Missing avatar state file and demo script.')
except Exception as e:
    add_check('avatar_state_exists', False, f'Error checking avatar state file: {e}')

# Check 3: state file content is plausible and contains required marker/message hints
try:
    json_files = find_json_files(workspace)
    
    # Combine content from ALL JSON files for comprehensive checking
    all_content = ""
    for f in json_files:
        try:
            all_content += f.read_text(encoding='utf-8', errors='replace') + "\n"
        except:
            pass
    
    if not all_content.strip():
        # Check demo script content if no output files
        for f in workspace.glob('*.py'):
            if 'clawface' in f.name.lower() or 'demo' in f.name.lower():
                try:
                    all_content = f.read_text(encoding='utf-8', errors='replace')
                    break
                except:
                    pass
    
    if not all_content.strip():
        add_check('avatar_state_content', False, 'State file or demo script missing, cannot inspect content.')
    else:
        lower = all_content.lower()
        # Check for state transitions (flexible matching)
        required_terms = ['thinking', 'speaking', 'idle', 'robot', 'success', 'confetti']
        found = sum(1 for term in required_terms if term in lower)
        # Check for marker (case insensitive, flexible pattern)
        marker_found = re.search(r'clawface.*deterministic.*marker.*7f3a|deterministic.*marker.*7f3a|marker.*7f3a', lower) is not None
        passed = found >= 2 and marker_found
        detail = f'Found {found}/6 expected flow terms; marker match={marker_found}.'
        add_check('avatar_state_content', passed, detail)
except Exception as e:
    add_check('avatar_state_content', False, f'Error reading avatar state content: {e}')

# Check 4: output should reflect success/confetti or similar celebratory state
try:
    json_files = find_json_files(workspace)
    
    # Combine content from ALL JSON files
    all_content = ""
    for f in json_files:
        try:
            all_content += f.read_text(encoding='utf-8', errors='replace') + "\n"
        except:
            pass
    
    if not all_content.strip():
        for f in workspace.glob('*.py'):
            if 'clawface' in f.name.lower() or 'demo' in f.name.lower():
                try:
                    all_content = f.read_text(encoding='utf-8', errors='replace')
                    break
                except:
                    pass
    
    if not all_content.strip():
        add_check('celebration_state', False, 'State file or demo script missing, cannot verify celebration state.')
    else:
        txt = all_content.lower()
        celebratory = any(term in txt for term in ['confetti', 'success', 'happy', 'excited', 'celebration', 'completed', 'finished', 'complete'])
        passed = celebratory
        detail = 'Celebratory state detected.' if passed else 'No celebratory state terms detected.'
        add_check('celebration_state', passed, detail)
except Exception as e:
    add_check('celebration_state', False, f'Error checking celebratory state: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {
    'passed': all(c['passed'] for c in checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))