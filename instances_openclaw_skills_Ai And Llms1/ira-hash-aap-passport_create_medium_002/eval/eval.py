import json
import os
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

# Check 1: summary file exists and has useful content
try:
    # Check for attestation_summary.json or output.txt
    summary_candidates = [
        workspace / 'attestation_summary.json',
        workspace / 'output.txt',
        workspace / 'summary.json',
        workspace / 'result.json'
    ]
    summary_path = next((p for p in summary_candidates if p.exists()), None)
    
    if summary_path is None:
        add_check('output_exists', False, 'output.txt or attestation_summary.json is missing')
    else:
        text = summary_path.read_text(encoding='utf-8', errors='replace')
        lowered = text.lower()
        has_public = 'publicid' in lowered or 'public id' in lowered or 'public_id' in lowered
        has_token = 'sessiontoken' in lowered or 'session token' in lowered or 'session_token' in lowered or ('token' in lowered and 'session' in lowered)
        has_verification = 'verified' in lowered or 'success' in lowered or 'verification' in lowered
        passed = has_public and has_token and has_verification
        detail = 'found expected summary terms' if passed else f'missing terms: public={has_public}, token={has_token}, verification={has_verification}'
        add_check('output_exists', passed, detail)
except Exception as e:
    add_check('output_exists', False, f'error reading output file: {e}')

# Check 2: server file exists and references AAP settings
try:
    server_candidates = [workspace / 'server.js', workspace / 'index.js', workspace / 'app.js']
    server_path = next((p for p in server_candidates if p.exists()), None)
    if server_path is None:
        add_check('server_file', False, 'no expected server entry file found')
    else:
        text = server_path.read_text(encoding='utf-8', errors='replace').lower()
        # Check for AAP path and signature/verification related terms
        has_aap = 'aap' in text
        has_path = '/aap' in text
        has_signature = 'signature' in text or 'sign' in text or 'verify' in text or 'require' in text
        passed = has_aap and has_path and has_signature
        add_check('server_file', passed, 'server mentions AAP, /aap, and signature/verification' if passed else 'server does not clearly configure AAP path/signature')
except Exception as e:
    add_check('server_file', False, f'error reading server file: {e}')

# Check 3: client file exists and references verification flow
try:
    client_candidates = [workspace / 'client.js', workspace / 'client.mjs', workspace / 'verify.js']
    client_path = next((p for p in client_candidates if p.exists()), None)
    if client_path is None:
        add_check('client_file', False, 'no expected client entry file found')
    else:
        text = client_path.read_text(encoding='utf-8', errors='replace').lower()
        # Check for verification/connection related terms - be more flexible
        has_verify = 'verify' in text or 'verification' in text or 'attest' in text or 'signature' in text
        has_connect = 'connect' in text or 'connection' in text or 'websocket' in text or 'ws://' in text
        has_aap = 'aap' in text or 'attestation' in text or 'attest' in text
        passed = has_verify and has_connect and has_aap
        add_check('client_file', passed, 'client appears to connect and verify' if passed else 'client does not clearly implement AAP verification')
except Exception as e:
    add_check('client_file', False, f'error reading client file: {e}')

# Check 4: marker file is present and preserved
try:
    marker_path = workspace / 'marker.json'
    if not marker_path.exists():
        add_check('marker_file', False, 'marker.json missing')
    else:
        data = json.loads(marker_path.read_text(encoding='utf-8', errors='replace'))
        marker = str(data.get('marker', '')).lower()
        passed = 'aap_task_marker_7f3a' in marker
        add_check('marker_file', passed, 'marker content verified' if passed else 'marker value mismatch')
except Exception as e:
    add_check('marker_file', False, f'error parsing marker.json: {e}')

score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
result = {
    'passed': all(c['passed'] for c in checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))