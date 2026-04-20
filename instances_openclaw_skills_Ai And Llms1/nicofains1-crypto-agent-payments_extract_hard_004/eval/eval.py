import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'failed to read {path.name}: {e}'
    return None, 'unreachable'


def normalize_ws(s: str) -> str:
    return re.sub(r'\s+', ' ', s or '').strip()


def norm_token(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out_path = workspace / 'summary.json'

    # Check 1: output exists
    try:
        exists = out_path.exists()
        checks.append({
            'name': 'summary_exists',
            'passed': bool(exists),
            'detail': 'summary.json found' if exists else 'summary.json is missing'
        })
    except Exception as e:
        checks.append({'name': 'summary_exists', 'passed': False, 'detail': f'exception while checking existence: {e}'})

    # Check 2: valid JSON and expected structure
    data = None
    try:
        if out_path.exists():
            raw = out_path.read_text(encoding='utf-8')
            data = json.loads(raw)
            passed = isinstance(data, dict)
            checks.append({'name': 'summary_is_json_object', 'passed': passed, 'detail': 'parsed JSON object' if passed else 'summary.json is not a JSON object'})
        else:
            checks.append({'name': 'summary_is_json_object', 'passed': False, 'detail': 'cannot parse because summary.json is missing'})
    except Exception as e:
        checks.append({'name': 'summary_is_json_object', 'passed': False, 'detail': f'failed to parse JSON: {e}'})

    # Expected source marker file
    target_file = workspace / 'notes_b.txt'
    marker_ok = False
    marker_detail = ''
    try:
        text = target_file.read_text(encoding='utf-8')
        marker_ok = 'ONLYSWAPS-CASE-ALPHA' in text
        marker_detail = 'marker found in notes_b.txt' if marker_ok else 'marker missing from notes_b.txt'
    except Exception as e:
        marker_detail = f'failed to read notes_b.txt: {e}'
    checks.append({'name': 'source_marker_present', 'passed': marker_ok, 'detail': marker_detail})

    # Check extracted fields fuzzily
    expected = {
        'source_file': 'notes_b.txt',
        'chain_name': 'ARBITRUM',
        'chain_id': 42161,
        'recipient_address': '0x1111111111111111111111111111111111111111',
        'token_symbol': 'ETH',
        'amount': '2',
        'wallet_label': 'alpha-batch-9',
        'amount_kind': 'whole'
    }

    def get_field(obj, key):
        try:
            return obj.get(key)
        except Exception:
            return None

    field_specs = [
        ('source_file', lambda v: norm_token(str(v)) == norm_token(expected['source_file'])),
        ('chain_name', lambda v: norm_token(str(v)) == norm_token(expected['chain_name'])),
        ('chain_id', lambda v: str(v).strip() == str(expected['chain_id'])),
        ('recipient_address', lambda v: norm_token(str(v)) == norm_token(expected['recipient_address'])),
        ('token_symbol', lambda v: norm_token(str(v)) == norm_token(expected['token_symbol'])),
        ('amount', lambda v: normalize_ws(str(v)) == normalize_ws(expected['amount'])),
        ('wallet_label', lambda v: norm_token(str(v)) == norm_token(expected['wallet_label'])),
        ('amount_kind', lambda v: norm_token(str(v)) == norm_token(expected['amount_kind'])),
    ]

    field_results = []
    if isinstance(data, dict):
        for field, predicate in field_specs:
            try:
                value = get_field(data, field)
                passed = predicate(value)
                field_results.append(passed)
                checks.append({
                    'name': f'field_{field}',
                    'passed': passed,
                    'detail': f'expected fuzzy match for {field}; got {value!r}'
                })
            except Exception as e:
                field_results.append(False)
                checks.append({'name': f'field_{field}', 'passed': False, 'detail': f'error checking {field}: {e}'})
    else:
        for field, _ in field_specs:
            checks.append({'name': f'field_{field}', 'passed': False, 'detail': 'summary.json is not available as an object'})
            field_results.append(False)

    # Final aggregate check
    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / total if total else 0.0
        passed = all(c.get('passed') for c in checks)
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result, indent=2))
    except Exception as e:
        fallback = {
            'passed': False,
            'score': 0.0,
            'checks': checks + [{'name': 'finalization', 'passed': False, 'detail': f'failed to finalize result: {e}'}]
        }
        print(json.dumps(fallback, indent=2))


if __name__ == '__main__':
    main()
