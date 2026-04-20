import json
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: output file exists
    try:
        output_path = workspace / 'output.json'
        exists = output_path.exists()
        checks.append({
            'name': 'output file exists',
            'passed': bool(exists),
            'detail': 'output.json found' if exists else 'output.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'output file exists', 'passed': False, 'detail': f'error checking existence: {e}'})
        output_path = workspace / 'output.json'

    # Check 2: JSON structure and fields
    parsed = None
    try:
        if output_path.exists():
            parsed = json.loads(output_path.read_text(encoding='utf-8', errors='ignore'))
            ok = isinstance(parsed, dict)
            checks.append({
                'name': 'output json parses',
                'passed': ok,
                'detail': 'parsed as JSON object' if ok else 'top level is not an object'
            })
        else:
            checks.append({'name': 'output json parses', 'passed': False, 'detail': 'cannot parse because file is missing'})
    except Exception as e:
        checks.append({'name': 'output json parses', 'passed': False, 'detail': f'json parse failed: {e}'})

    # Check 3: canonical URL present in any reasonable field
    try:
        target = 'https://clawhub.ai/xiwan/agent-linguo'
        found = False
        detail = 'canonical URL not found'
        if isinstance(parsed, dict):
            blob = json.dumps(parsed, ensure_ascii=False)
            found = normalize(target) in normalize(blob)
            detail = 'canonical URL matched fuzzily' if found else 'canonical URL missing or mismatched'
        checks.append({'name': 'canonical url', 'passed': bool(found), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'canonical url', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: security levels in priority order
    try:
        expected = ['P', 'B', 'E']
        passed = False
        detail = 'security levels not found'
        if isinstance(parsed, dict):
            val = parsed.get('security_levels') or parsed.get('security') or parsed.get('levels')
            if isinstance(val, str):
                vals = re.findall(r'[PBE]', val.upper())
                passed = vals[:3] == expected
            elif isinstance(val, list):
                vals = [str(x).strip().upper() for x in val]
                passed = vals[:3] == expected
            detail = f'found={val!r}'
        checks.append({'name': 'security priority order', 'passed': bool(passed), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'security priority order', 'passed': False, 'detail': f'error: {e}'})

    # Check 5: signature-required sample identified
    try:
        passed = False
        detail = 'sample identification missing'
        if isinstance(parsed, dict):
            txt = json.dumps(parsed, ensure_ascii=False).lower()
            # Accept variations that indicate the public post/comment sample
            keywords = ['public post', 'public posts', 'comment', 'signature required', 'signature-needed', 'requires signature']
            passed = any(k in txt for k in keywords)
            detail = 'matched one of the signature-related phrases' if passed else 'no signature-related phrase found'
        checks.append({'name': 'signature required sample', 'passed': bool(passed), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'signature required sample', 'passed': False, 'detail': f'error: {e}'})

    # Check 6: session ID extracted
    try:
        expected = 's123456'
        found = None
        detail = 'session id missing'
        if isinstance(parsed, dict):
            blob = json.dumps(parsed, ensure_ascii=False)
            m = re.search(r'\bs\d{3,}\b', blob, flags=re.I)
            if m:
                found = m.group(0)
            passed = bool(found) and normalize(found) == normalize(expected)
            detail = f'found={found!r}'
        else:
            passed = False
        checks.append({'name': 'session id', 'passed': bool(passed), 'detail': detail})
    except Exception as e:
        checks.append({'name': 'session id', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
