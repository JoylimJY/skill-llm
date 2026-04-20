from pathlib import Path
import json
import os
import re
import sys


def normalize(text):
    try:
        return re.sub(r'\s+', ' ', text.lower()).strip()
    except Exception:
        return ''


def find_file_in_workspace(workspace, filename):
    """Find file in workspace or subdirectories"""
    # Check workspace root first
    p = Path(workspace, filename)
    if p.is_file():
        return p
    
    # Check common subdirectories
    for subdir in ['src', 'lib', 'app', 'examples', 'demo', 'node_modules/.bin']:
        p = Path(workspace, subdir, filename)
        if p.is_file():
            return p
    
    return None


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    checks = []

    # Check 1: input marker exists
    try:
        p = Path(workspace, 'input_marker.txt')
        ok = p.is_file()
        detail = 'input_marker.txt present' if ok else 'input_marker.txt missing'
        checks.append({'name': 'input marker present', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input marker present', 'passed': False, 'detail': f'error: {e}'})

    # Check 2: server.js exists and has required server configuration
    try:
        p = find_file_in_workspace(workspace, 'server.js')
        if not p:
            checks.append({'name': 'server.js created', 'passed': False, 'detail': 'server.js missing'})
        else:
            txt = p.read_text(encoding='utf-8')
            txt_lower = txt.lower()
            
            # Check for WebSocket server (ws library or similar) - more flexible
            has_websocket = bool(
                'websocket' in txt_lower or 
                'wsserver' in txt_lower or
                'require(\'ws\')' in txt or
                'require("ws")' in txt or
                'from \'ws\'' in txt or
                'from "ws"' in txt or
                'import.*ws' in txt_lower or
                'createServer' in txt_lower
            )
            
            # Check for path /aap - more flexible
            has_path = bool(
                '/aap' in txt or 
                re.search(r'["\']?/aap["\']?', txt) or
                re.search(r'path.*=.*["\']?/aap', txt, re.IGNORECASE)
            )
            
            # Check for requireSignature (case insensitive)
            has_require_sig = bool(re.search(r'requiresignature', txt, re.IGNORECASE))
            
            # Check for port 3000
            has_port = bool('3000' in txt)
            
            # Check for logging public IDs - more flexible
            has_log_public_id = bool(
                'publicid' in txt_lower or 
                'public id' in txt_lower or
                'verified' in txt_lower or
                'console.log' in txt_lower or
                'console\.log' in txt
            )
            
            ok = has_websocket and has_path and has_require_sig and has_port and has_log_public_id
            checks.append({'name': 'server.js created', 'passed': ok, 'detail': 'server.js contains expected WebSocket server setup' if ok else 'server.js content does not match expected setup'})
    except Exception as e:
        checks.append({'name': 'server.js created', 'passed': False, 'detail': f'error reading server.js: {e}'})

    # Check 3: client.js exists and has required client configuration
    try:
        p = find_file_in_workspace(workspace, 'client.js')
        if not p:
            checks.append({'name': 'client.js created', 'passed': False, 'detail': 'client.js missing'})
        else:
            txt = p.read_text(encoding='utf-8')
            txt_lower = txt.lower()
            
            # Check for WebSocket client (ws library or similar) - more flexible
            has_websocket_client = bool(
                'websocket' in txt_lower or 
                'new websocket' in txt_lower or
                'require(\'ws\')' in txt or
                'require("ws")' in txt or
                'from \'ws\'' in txt or
                'from "ws"' in txt or
                'import.*ws' in txt_lower or
                'new WebSocket' in txt or
                'new websocket' in txt_lower
            )
            
            # Check for ws://localhost:3000/aap - more flexible
            has_url = bool(
                'ws://localhost:3000/aap' in txt or 
                re.search(r'ws://localhost:3000/aap', txt) or
                ('localhost' in txt_lower and '3000' in txt and '/aap' in txt)
            )
            
            # Check for verify or solver - more flexible
            has_verify = bool(
                re.search(r'verify|solver', txt, re.IGNORECASE) or
                'verification' in txt_lower or
                'verify' in txt_lower
            )
            
            ok = has_websocket_client and has_url and has_verify
            checks.append({'name': 'client.js created', 'passed': ok, 'detail': 'client.js contains expected WebSocket client setup' if ok else 'client.js content does not match expected setup'})
    except Exception as e:
        checks.append({'name': 'client.js created', 'passed': False, 'detail': f'error reading client.js: {e}'})

    # Check 4: output marker is referenced somewhere in outputs or files
    try:
        marker_ok = False
        for fname in ['server.js', 'client.js', 'README.md', 'notes.txt', 'index.js', 'app.js']:
            fp = find_file_in_workspace(workspace, fname)
            if fp:
                try:
                    txt = fp.read_text(encoding='utf-8')
                    txt_lower = txt.lower()
                    if 'aap' in txt_lower and ('3000' in txt or 'ws://localhost:3000/aap' in txt):
                        marker_ok = True
                        break
                except Exception:
                    pass
        checks.append({'name': 'references core demo details', 'passed': marker_ok, 'detail': 'found expected AAP demo references' if marker_ok else 'expected demo references not found'})
    except Exception as e:
        checks.append({'name': 'references core demo details', 'passed': False, 'detail': f'error during scan: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = (passed_count / total) if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Absolute fallback to avoid traceback
        result = {'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal error', 'passed': False, 'detail': f'unexpected evaluator failure: {str(e)}'}]}
        print(json.dumps(result, ensure_ascii=False))