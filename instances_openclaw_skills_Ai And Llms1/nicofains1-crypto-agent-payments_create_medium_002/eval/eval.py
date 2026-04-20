import json
import re
from pathlib import Path
import sys


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    ws = Path(sys.argv[1])
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        wallet_path = ws / 'wallet_notes.txt'
        if wallet_path.exists():
            txt = wallet_path.read_text(encoding='utf-8')
            marker_ok = 'DEMO-WALLET-ALPHA-42' in txt.upper()
            add_check('wallet marker present', marker_ok, 'marker found' if marker_ok else 'marker missing')
        else:
            add_check('wallet marker present', False, 'wallet_notes.txt missing')
    except Exception as e:
        add_check('wallet marker present', False, f'error: {e}')

    try:
        csv_path = ws / 'transfer_plan.csv'
        if csv_path.exists():
            txt = csv_path.read_text(encoding='utf-8')
            ok = ('human' in txt.lower()) and ('12.5' in txt)
            add_check('transfer plan format', ok, 'human-readable amount detected' if ok else 'missing expected amount or format')
        else:
            add_check('transfer plan format', False, 'transfer_plan.csv missing')
    except Exception as e:
        add_check('transfer plan format', False, f'error: {e}')

    try:
        instr_path = ws / 'instructions.json'
        if instr_path.exists():
            data = json.loads(instr_path.read_text(encoding='utf-8'))
            fields = data.get('required_fields', []) if isinstance(data, dict) else []
            wanted = {'wallet_marker', 'chain', 'token', 'amount_format'}
            ok = all(any(norm(f) == norm(w) for f in fields) for w in wanted)
            add_check('instructions schema', ok, 'required fields present' if ok else f'fields were: {fields}')
        else:
            add_check('instructions schema', False, 'instructions.json missing')
    except Exception as e:
        add_check('instructions schema', False, f'error: {e}')

    try:
        expected_path = ws / 'expected_marker.txt'
        if expected_path.exists():
            txt = expected_path.read_text(encoding='utf-8')
            ok = 'DEMO-WALLET-ALPHA-42' in txt
            add_check('expected marker file', ok, 'expected marker file verified' if ok else 'marker not found in expected_marker.txt')
        else:
            add_check('expected marker file', False, 'expected_marker.txt missing')
    except Exception as e:
        add_check('expected marker file', False, f'error: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
