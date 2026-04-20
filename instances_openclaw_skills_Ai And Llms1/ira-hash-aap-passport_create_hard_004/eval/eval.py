import json
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, e


# Check 1: output exists and is parseable
out_path = workspace / 'output.json'
try:
    if not out_path.exists():
        add_check('output_exists', False, 'output.json is missing')
        data = None
    else:
        content, err = safe_read(out_path)
        if err:
            add_check('output_exists', False, f'output.json could not be read: {err}')
            data = None
        else:
            data = json.loads(content)
            add_check('output_exists', True, 'output.json found and parsed')
except Exception as e:
    data = None
    add_check('output_exists', False, f'output.json could not be parsed: {e}')

# Check 2: marker used
try:
    marker_path = workspace / 'marker.txt'
    marker_text, err = safe_read(marker_path)
    marker_text = marker_text if marker_text else ''
    out_text, err = safe_read(out_path)
    out_text = out_text if out_text else ''
    marker_norm = ''.join(ch.lower() for ch in marker_text if ch.isalnum())
    out_norm = ''.join(ch.lower() for ch in out_text if ch.isalnum())
    passed = bool(marker_norm) and marker_norm in out_norm
    add_check('marker_preserved', passed, 'marker content referenced in output' if passed else 'marker not found in output')
except Exception as e:
    add_check('marker_preserved', False, f'error while checking marker: {e}')

# Check 3: required fields present and reasonable
try:
    if isinstance(data, dict):
        # Check for publicId or publicIdentity at root or in verified object
        public_id = data.get('publicId') or data.get('publicIdentity') or (data.get('verified', {}).get('publicIdentity') if isinstance(data.get('verified'), dict) else None)
        session_token = data.get('sessionToken') or (data.get('verified', {}).get('sessionToken') if isinstance(data.get('verified'), dict) else None)
        summary = data.get('summary') or data.get('handshake')
        
        missing = []
        if not public_id:
            missing.append('publicId')
        if not session_token:
            missing.append('sessionToken')
        if not summary:
            missing.append('summary')
        
        passed = not missing
        add_check('required_fields', passed, 'all required fields present' if passed else f'missing fields: {missing}')
    else:
        add_check('required_fields', False, 'output is not a JSON object')
except Exception as e:
    add_check('required_fields', False, f'error while checking fields: {e}')

# Check 4: publicId fuzzy match
try:
    expected = 'agent-echo-42'
    public_id = data.get('publicId') or data.get('publicIdentity') or (data.get('verified', {}).get('publicIdentity') if isinstance(data.get('verified'), dict) else None)
    got = str(public_id) if public_id else ''
    passed = expected.lower().replace('-', '') in got.lower().replace('-', '')
    add_check('publicId_match', passed, f'expected similar to {expected}, got {got}')
except Exception as e:
    add_check('publicId_match', False, f'error while checking publicId: {e}')

# Check 5: session token fuzzy match
try:
    expected = 'sess_tok_91c0d1'
    session_token = data.get('sessionToken') or (data.get('verified', {}).get('sessionToken') if isinstance(data.get('verified'), dict) else None)
    got = str(session_token) if session_token else ''
    passed = expected.lower().replace('_', '') in got.lower().replace('_', '')
    add_check('sessionToken_match', passed, f'expected similar to {expected}, got {got}')
except Exception as e:
    add_check('sessionToken_match', False, f'error while checking sessionToken: {e}')

# Check 6: summary mentions signature and 7 challenges
try:
    summary = data.get('summary') or data.get('handshake')
    if isinstance(summary, dict):
        summary_str = json.dumps(summary)
    else:
        summary_str = str(summary) if summary else ''
    norm = summary_str.lower()
    passed = ('signature' in norm) and ('7' in norm or 'seven' in norm) and ('challenge' in norm)
    add_check('summary_quality', passed, 'summary mentions signature and seven challenges' if passed else f'bad summary: {summary_str}')
except Exception as e:
    add_check('summary_quality', False, f'error while checking summary: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))