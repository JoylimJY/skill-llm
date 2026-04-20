import json
import os
import re
from pathlib import Path
import sys


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def find_json_in_text(text, marker):
    """Search for marker anywhere in JSON text (fuzzy search)"""
    text_lower = text.lower()
    marker_lower = marker.lower()
    return marker_lower in text_lower


def find_server_log(workspace):
    """Recursively search for server log files in workspace"""
    candidates = []
    
    # Search recursively for files with 'server' or 'log' in name
    for f in workspace.rglob('*'):
        if f.is_file():
            name_lower = f.name.lower()
            if 'server' in name_lower or 'log' in name_lower:
                candidates.append(f)
    
    # Also check common log file extensions
    for ext in ['.log', '.txt', '.json']:
        for f in workspace.rglob(f'*{ext}'):
            if f.is_file():
                name_lower = f.name.lower()
                if 'server' in name_lower or 'log' in name_lower:
                    if f not in candidates:
                        candidates.append(f)
    
    return candidates


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: marker file exists and contains marker text
    try:
        p = workspace / 'input_marker.txt'
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='replace')
            passed = 'aap-deterministic-marker-42' in text.lower()
            detail = 'marker found' if passed else 'marker missing from input_marker.txt'
        else:
            passed = False
            detail = 'input_marker.txt is missing'
    except Exception as e:
        passed = False
        detail = f'error reading marker file: {e}'
    checks.append({'name': 'marker_file', 'passed': passed, 'detail': detail})

    # Check 2: summary file exists and is valid JSON with verification-related fields
    try:
        p = workspace / 'verification-summary.json'
        if not p.exists():
            passed = False
            detail = 'verification-summary.json is missing'
        else:
            try:
                data = json.loads(p.read_text(encoding='utf-8', errors='replace'))
                # Flexible check: look for verification-related content
                if isinstance(data, dict):
                    # Check for any verification status field
                    has_status = any('verified' in str(v).lower() for v in data.values())
                    has_identity = any('identity' in str(k).lower() or 'id' in str(k).lower() 
                                      for k in data.keys())
                    has_payload = any('payload' in str(k).lower() or 'proof' in str(k).lower() 
                                      for k in data.keys())
                    passed = has_status and (has_identity or has_payload)
                    detail = 'summary json structure looks valid' if passed else 'summary json missing required keys'
                else:
                    passed = False
                    detail = 'summary json is not a valid object'
            except Exception as e:
                passed = False
                detail = f'invalid JSON in verification-summary.json: {e}'
    except Exception as e:
        passed = False
        detail = f'error checking summary file: {e}'
    checks.append({'name': 'summary_json', 'passed': passed, 'detail': detail})

    # Check 3: payload contains deterministic marker anywhere in the JSON
    try:
        p = workspace / 'verification-summary.json'
        if not p.exists():
            passed = False
            detail = 'verification-summary.json missing for payload check'
        else:
            try:
                text = p.read_text(encoding='utf-8', errors='replace')
                # Search for marker anywhere in the file content
                passed = 'aap-deterministic-marker-42' in text.lower()
                detail = 'deterministic marker present in payload' if passed else 'deterministic marker not found in payload'
            except Exception as e:
                passed = False
                detail = f'payload parsing failed: {e}'
    except Exception as e:
        passed = False
        detail = f'error checking payload: {e}'
    checks.append({'name': 'payload_marker', 'passed': passed, 'detail': detail})

    # Check 4: server log file exists and contains expected content
    try:
        # Recursively search for server log files
        log_files = find_server_log(workspace)
        
        if not log_files:
            passed = False
            detail = 'no server log file found'
        else:
            found = None
            for p in log_files:
                try:
                    text = p.read_text(encoding='utf-8', errors='replace').lower()
                    # Flexible check: look for server-started OR aap/websocket indicators
                    has_server_started = 'server-started' in text
                    has_aap = 'aap' in text
                    has_ws = 'ws://' in text or 'websocket' in text or 'ws:' in text
                    
                    # Pass if server-started is present OR if aap and websocket indicators are present
                    if has_server_started or (has_aap and has_ws):
                        found = p
                        passed = True
                        detail = f'log inspected: {p.name}'
                        break
                except Exception:
                    continue
            
            if not found:
                passed = False
                detail = 'server log does not contain expected content'
    except Exception as e:
        passed = False
        detail = f'error checking server log: {e}'
    checks.append({'name': 'server_log', 'passed': passed, 'detail': detail})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()