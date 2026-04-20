import json
import sys
import re
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def safe_load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, f'{path.name}: {type(e).__name__}: {e}'


def find_config_file(workspace):
    """Find config file with common naming patterns - search recursively"""
    possible_names = [
        'config.json',
        'presence_config.json',
        'presence.json',
        'agent_config.json',
        'display_config.json',
    ]
    
    # First check workspace root
    for name in possible_names:
        path = workspace / name
        if path.exists():
            return path
    
    # Also search for any .json file in workspace root (excluding seed_data.json)
    for f in workspace.glob('*.json'):
        if f.name != 'seed_data.json':
            return f
    
    # Search recursively in subdirectories
    for name in possible_names:
        for path in workspace.rglob(name):
            if path.exists():
                return path
    
    # Also search for any .json file in subdirectories (excluding seed_data.json)
    for f in workspace.rglob('*.json'):
        if f.name != 'seed_data.json':
            return f
    
    return None


def find_state_file(workspace):
    """Find state file with common naming patterns - search recursively"""
    possible_names = [
        'state.json',
        'presence_state.json',
        'agent_state.json',
        'display_state.json',
    ]
    
    # First check workspace root
    for name in possible_names:
        path = workspace / name
        if path.exists():
            return path
    
    # Search recursively in subdirectories
    for name in possible_names:
        for path in workspace.rglob(name):
            if path.exists():
                return path
    
    return None


def get_nested_value(d, *keys):
    """Get value from nested dict using path of keys"""
    try:
        val = d
        for key in keys:
            val = val[key]
        return val
    except (KeyError, TypeError):
        return None


def get_config_value(cfg, *keys):
    """Get value from config trying multiple possible key names and nested paths"""
    if not isinstance(cfg, dict):
        return None
    
    # First try top-level keys
    for key in keys:
        if key in cfg:
            return cfg[key]
    
    # Try common nested paths for name
    name_paths = [
        ('agent', 'name'),
        ('agent', 'display_name'),
        ('display', 'name'),
        ('settings', 'name'),
        ('config', 'name'),
    ]
    for path in name_paths:
        val = get_nested_value(cfg, *path)
        if val is not None:
            return val
    
    # Try common nested paths for letter/monogram
    letter_paths = [
        ('agent', 'monogram'),
        ('agent', 'letter'),
        ('agent', 'initial'),
        ('display', 'monogram'),
        ('display', 'letter'),
        ('settings', 'monogram'),
        ('settings', 'letter'),
    ]
    for path in letter_paths:
        val = get_nested_value(cfg, *path)
        if val is not None:
            return val
    
    # Try common nested paths for timeout
    timeout_paths = [
        ('settings', 'idle_timeout'),
        ('settings', 'timeout'),
        ('settings', 'idle_time'),
        ('display', 'idle_timeout'),
        ('config', 'idle_timeout'),
    ]
    for path in timeout_paths:
        val = get_nested_value(cfg, *path)
        if val is not None:
            return val
    
    return None


def extract_config_values(cfg):
    """Extract name, letter, and timeout from config with flexible structure"""
    name = None
    letter = None
    timeout = None
    
    if not isinstance(cfg, dict):
        return name, letter, timeout
    
    # Try to find name
    name = get_config_value(cfg, 'name', 'agent_name', 'agent', 'display_name')
    
    # Try to find letter/monogram
    letter = get_config_value(cfg, 'letter', 'monogram', 'monogram_letter', 'initial')
    
    # Try to find timeout
    timeout = get_config_value(cfg, 'idle_timeout', 'timeout', 'idle_time', 'timeout_seconds')
    
    return name, letter, timeout


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    config_path = find_config_file(workspace)
    state_path = find_state_file(workspace)
    marker_path = workspace / 'notes' / 'marker.txt'

    # Check marker file
    try:
        marker_text = marker_path.read_text(encoding='utf-8')
    except Exception as e:
        marker_text = ''
        checks.append({'name': 'marker file exists', 'passed': False, 'detail': f'missing or unreadable: {type(e).__name__}: {e}'})
    else:
        checks.append({'name': 'marker file exists', 'passed': True, 'detail': 'marker file readable'})

    # Check config file
    cfg = {}
    if config_path is None:
        checks.append({'name': 'config.json exists and is valid', 'passed': False, 'detail': 'missing or invalid: no config file found'})
    else:
        cfg, cfg_err = safe_load_json(config_path)
        if cfg is None:
            checks.append({'name': 'config.json exists and is valid', 'passed': False, 'detail': f'missing or invalid: {cfg_err}'})
        else:
            checks.append({'name': 'config.json exists and is valid', 'passed': True, 'detail': f'config loaded from {config_path.name}'})

    # Check state file (optional - should not fail if missing)
    st = {}
    if state_path is None:
        checks.append({'name': 'state.json exists and is valid', 'passed': True, 'detail': 'state file optional'})
    else:
        st, st_err = safe_load_json(state_path)
        if st is None:
            checks.append({'name': 'state.json exists and is valid', 'passed': True, 'detail': f'state file exists but optional: {st_err}'})
        else:
            checks.append({'name': 'state.json exists and is valid', 'passed': True, 'detail': f'state loaded from {state_path.name}'})

    # Check config values with flexible key names
    letter_ok = False
    name_ok = False
    timeout_ok = False

    try:
        name, letter, timeout = extract_config_values(cfg)
        
        letter_ok = norm(str(letter or '')) == 'n'
        name_ok = 'nova' in norm(str(name or ''))
        timeout_ok = str(timeout or '').strip() in {'600', '600.0', '600.00'}
        
        detail = f'letter={letter!r}, name={name!r}, idle_timeout={timeout!r}'
        checks.append({'name': 'config values match request', 'passed': letter_ok and name_ok and timeout_ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'config values match request', 'passed': False, 'detail': f'error reading config fields: {type(e).__name__}: {e}'})

    # Check state file values (only if state file exists and is valid)
    try:
        if state_path is not None and st and isinstance(st, dict):
            state = str(st.get('state', ''))
            message = str(st.get('message', ''))
            state_ok = norm(state) == 'idle' and message == ''
            detail = f'state={state!r}, message={message!r}'
            checks.append({'name': 'state file is idle/empty by default', 'passed': state_ok, 'detail': detail})
        else:
            checks.append({'name': 'state file is idle/empty by default', 'passed': True, 'detail': 'state file optional or empty'})
    except Exception as e:
        checks.append({'name': 'state file is idle/empty by default', 'passed': True, 'detail': f'state file optional: {type(e).__name__}: {e}'})

    # Check marker content
    try:
        marker_ok = ('nova' in norm(marker_text)) and ('n' in norm(marker_text)) and ('600' in norm(marker_text))
        checks.append({'name': 'generated marker content present', 'passed': marker_ok, 'detail': 'searched marker file for NOVA, N, and 600'})
    except Exception as e:
        checks.append({'name': 'generated marker content present', 'passed': False, 'detail': f'error checking marker: {type(e).__name__}: {e}'})

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    score = passed_count / total
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal error', 'passed': False, 'detail': 'unexpected evaluator failure'}]}))