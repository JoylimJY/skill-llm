import json
import re
from pathlib import Path
import sys

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, e


def find_value_in_dict(d, keys, default=None):
    """Recursively search for a value in nested dict using multiple possible key names."""
    if not isinstance(d, dict):
        return default
    for key in keys:
        if key in d:
            return d[key]
    for value in d.values():
        if isinstance(value, dict):
            result = find_value_in_dict(value, keys, default)
            if result is not None:
                return result
    return default


def find_text_in_dict(d, search_terms, default=""):
    """Recursively search for text containing any of the search terms in dict values."""
    if not isinstance(d, dict):
        return default
    for key, value in d.items():
        if isinstance(value, str):
            for term in search_terms:
                if term.lower() in value.lower():
                    return value
        elif isinstance(value, dict):
            result = find_text_in_dict(value, search_terms, default)
            if result:
                return result
    return default


# Check 1: aap-summary.md exists and mentions key protocol properties
try:
    p = workspace / 'aap-summary.md'
    if not p.exists():
        add_check('summary_exists', False, 'aap-summary.md is missing')
    else:
        text = p.read_text(encoding='utf-8', errors='replace')
        t = re.sub(r'\s+', ' ', text.lower())
        passed = all(x in t for x in ['aap', 'challenge', '7', '6000', 'signature'])
        add_check('summary_content', passed, 'Found required protocol keywords' if passed else 'Missing one or more required concepts')
except Exception as e:
    add_check('summary_content', False, f'Error reading summary: {e}')

# Check 2: aap-config.json exists and has expected defaults
try:
    p = workspace / 'aap-config.json'
    if not p.exists():
        add_check('config_exists', False, 'aap-config.json is missing')
    else:
        data = json.loads(p.read_text(encoding='utf-8'))
        checks2 = []
        
        # Check challenge_count (7) - search in nested structures
        challenge_val = find_value_in_dict(data, ['challengeCount', 'challenge_count', 'count'])
        checks2.append(('challenge_count', str(challenge_val).strip() == '7' if challenge_val is not None else False))
        
        # Check total_time_ms (6000) - search in nested structures
        time_val = find_value_in_dict(data, ['totalTimeMs', 'total_time_ms', 'time_limit_ms', 'timeLimitMs', 'time_limit', 'timeLimit'])
        checks2.append(('total_time_ms', str(time_val).strip() == '6000' if time_val is not None else False))
        
        # Check require_signature (true) - search in nested structures
        req_sig = find_value_in_dict(data, ['requireSignature', 'require_signature', 'signature_required', 'signatureRequired'])
        checks2.append(('require_signature', str(req_sig).lower() in ['true', '1', 'yes'] if req_sig is not None else False))
        
        # Check signature format mentions secp256k1 - search text in nested structures
        signature_text = find_text_in_dict(data, ['secp256k1', 'json.stringify'])
        checks2.append(('signature_format', bool(signature_text)))
        
        passed = all(v for _, v in checks2)
        detail = '; '.join([f'{k}={v}' for k, v in checks2])
        add_check('config_content', passed, detail)
except Exception as e:
    add_check('config_content', False, f'Error parsing config: {e}')

# Check 3: input marker file exists and contains marker
try:
    p = workspace / 'aap_reference.json'
    if not p.exists():
        add_check('marker_exists', False, 'aap_reference.json is missing')
    else:
        data = json.loads(p.read_text(encoding='utf-8'))
        marker = str(data.get('marker', ''))
        passed = 'AAP_MARKER_7F3A'.lower() in marker.lower()
        add_check('marker_content', passed, f'marker={marker}' if marker else 'marker missing')
except Exception as e:
    add_check('marker_content', False, f'Error reading marker file: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))