import json
import os
import re
import sys
from pathlib import Path


def norm_text(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', str(s).lower())
    except Exception:
        return ''


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return None


def read_text(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def get_config_value(cfg, *keys):
    """Get value from config trying multiple possible key names"""
    if not isinstance(cfg, dict):
        return None
    for key in keys:
        if key in cfg:
            return cfg[key]
    return None


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # 1) config file exists and matches expected values fuzzily
    # Accept multiple possible config filenames
    try:
        config_candidates = [
            workspace / 'config.json',
            workspace / 'clawd_config.json',
            workspace / 'presence_config.json',
            workspace / 'dashboard_config.json',
        ]
        cfg_path = None
        cfg = None
        for candidate in config_candidates:
            if candidate.exists():
                cfg_path = candidate
                cfg = read_json(cfg_path)
                break
        
        if cfg_path and isinstance(cfg, dict):
            # Accept multiple possible key names for each field
            letter_val = get_config_value(cfg, 'letter', 'monogram', 'monogram_file', 'monogram_name')
            name_val = get_config_value(cfg, 'name', 'agent_name', 'agentname')
            timeout_val = get_config_value(cfg, 'idle_timeout', 'timeout', 'idle_timeout_seconds')
            
            letter_ok = norm_text(str(letter_val or '')) == 'q'
            name_ok = 'quartz' in norm_text(str(name_val or ''))
            timeout_ok = str(timeout_val or '') == '420'
            
            passed = letter_ok and name_ok and timeout_ok
            detail = f"file={cfg_path.name}, letter={letter_val!r}, name={name_val!r}, idle_timeout={timeout_val!r}"
        else:
            passed = False
            detail = 'config file missing or malformed'
    except Exception as e:
        passed = False
        detail = f'error reading config: {e}'
    checks.append({'name': 'config.json configured', 'passed': passed, 'detail': detail})

    # 2) state.json exists and is idle/ready-ish (optional - not required by task)
    try:
        state_path = workspace / 'state.json'
        state = read_json(state_path)
        if isinstance(state, dict):
            state_ok = norm_text(state.get('state', '')) in {'idle', 'ready'}
            msg_ok = isinstance(state.get('message', ''), str)
            updated_ok = isinstance(state.get('updated', None), (int, float))
            passed = state_ok and msg_ok and updated_ok
            detail = f"state={state.get('state')!r}, message={state.get('message')!r}, updated={state.get('updated')!r}"
        else:
            # state.json is optional - pass if not present
            passed = True
            detail = 'state.json not required'
    except Exception as e:
        # state.json is optional - pass if error
        passed = True
        detail = f'state.json optional: {e}'
    checks.append({'name': 'state.json initialized', 'passed': passed, 'detail': detail})

    # 3) custom monogram file exists and contains expected marker pattern
    try:
        mono_path = workspace / 'assets' / 'monograms' / 'Q.txt'
        txt = read_text(mono_path)
        if isinstance(txt, str):
            norm = norm_text(txt)
            passed = 'qqqqq' in norm and 'q' in norm
            detail = f'length={len(txt)} chars'
        else:
            passed = False
            detail = 'assets/monograms/Q.txt missing or unreadable'
    except Exception as e:
        passed = False
        detail = f'error reading monogram: {e}'
    checks.append({'name': 'custom monogram present', 'passed': passed, 'detail': detail})

    # 4) presence helper scripts exist
    try:
        required = [workspace / 'scripts' / 'configure.py', workspace / 'scripts' / 'display.py', workspace / 'scripts' / 'status.py']
        missing = [str(p.name) for p in required if not p.exists()]
        passed = len(missing) == 0
        detail = 'missing=' + ', '.join(missing) if missing else 'all scripts present'
    except Exception as e:
        passed = False
        detail = f'error checking scripts: {e}'
    checks.append({'name': 'core scripts available', 'passed': passed, 'detail': detail})

    # 5) README note exists and mentions how to start display
    try:
        candidates = [workspace / 'README.md', workspace / 'readme.md', workspace / 'NOTES.md']
        found = None
        for p in candidates:
            if p.exists():
                found = p
                break
        if found:
            txt = read_text(found) or ''
            norm = norm_text(txt)
            passed = ('display' in norm) and ('configure' in norm) and ('status' in norm)
            detail = f'file={found.name}'
        else:
            passed = False
            detail = 'README note not found'
    except Exception as e:
        passed = False
        detail = f'error checking README note: {e}'
    checks.append({'name': 'usage note added', 'passed': passed, 'detail': detail})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': 'unexpected evaluator failure'}]}))