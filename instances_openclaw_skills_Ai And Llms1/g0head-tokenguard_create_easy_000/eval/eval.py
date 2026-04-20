import json
import os
import re
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    return ''.join(ch.lower() for ch in s if ch.isalnum() or ch.isspace())


def find_json_files(directory: Path):
    """Find all JSON files in a directory"""
    if not directory.exists():
        return []
    return [f for f in directory.iterdir() if f.suffix == '.json']


def main():
    import sys
    workspace = Path(sys.argv[1])
    checks = []

    marker_path = workspace / 'markers' / 'task_marker.json'
    try:
        marker = json.loads(marker_path.read_text(encoding='utf-8'))
        required_limit = float(marker.get('required_limit', 25.0))
    except Exception as e:
        marker = {}
        required_limit = 25.0
        checks.append({
            'name': 'marker file readable',
            'passed': False,
            'detail': f'Could not read marker file: {e}'
        })

    tokenguard_dir = workspace / '.tokenguard'
    
    # Find all JSON files in .tokenguard directory
    json_files = find_json_files(tokenguard_dir)
    
    # Check 1: limit file exists and contains a usable limit value
    limit_found = False
    limit_data = None
    for json_file in json_files:
        try:
            content = json_file.read_text(encoding='utf-8')
            data = json.loads(content)
            if isinstance(data, dict):
                # Check for limit value in various key names
                for key in ['limit', 'default_limit', 'spending_limit', 'amount', 'budget_limit']:
                    if key in data:
                        try:
                            val = float(data[key])
                            if abs(val - required_limit) < 0.01:
                                limit_found = True
                                limit_data = data
                                break
                        except Exception:
                            pass
                if limit_found:
                    break
                # Fallback: check if limit value appears in the JSON text
                text = normalize(content)
                if str(int(required_limit)) in text or str(required_limit) in text:
                    limit_found = True
                    limit_data = data
                    break
        except Exception:
            continue
    
    if not limit_found:
        checks.append({'name': 'limit file exists', 'passed': False, 'detail': 'Missing .tokenguard/limit.json or budget_limit.json with $25 value'})
    else:
        checks.append({'name': 'limit file exists', 'passed': True, 'detail': f'Found limit file with $25 value'})

    # Check 2: session file exists and is clean/empty-ish
    session_found = False
    session_clean = False
    session_data = None
    
    for json_file in json_files:
        try:
            content = json_file.read_text(encoding='utf-8')
            data = json.loads(content)
            if isinstance(data, dict):
                # Check for session/clean-start indicators
                has_session = any(key in data for key in ['session', 'session_name', 'session_id'])
                has_usage = any(key in data for key in ['usage', 'spent', 'total_spent', 'cost', 'tokens'])
                
                if has_session or has_usage:
                    session_found = True
                    session_data = data
                    
                    # Check if session is clean (zero usage)
                    spent = data.get('spent', data.get('total_spent', data.get('cost', 0)))
                    tokens = data.get('tokens', 0)
                    entries = data.get('entries', data.get('logs', []))
                    
                    try:
                        spent_ok = abs(float(spent)) < 1e-9
                    except Exception:
                        spent_ok = False
                    
                    try:
                        tokens_ok = int(tokens) == 0
                    except Exception:
                        tokens_ok = False
                    
                    entries_ok = isinstance(entries, list) and len(entries) == 0
                    
                    session_clean = spent_ok and tokens_ok and entries_ok
                    break
        except Exception:
            continue
    
    if not session_found:
        checks.append({'name': 'session file exists', 'passed': False, 'detail': 'Missing .tokenguard/session.json or session info in budget file'})
    elif not session_clean:
        checks.append({'name': 'session starts clean', 'passed': False, 'detail': f'Session not clean: {session_data}'})
    else:
        checks.append({'name': 'session starts clean', 'passed': True, 'detail': 'Session initialized with zero usage'})

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()