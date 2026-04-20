import json
import re
import sys
from pathlib import Path


def normalize(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9\u00c0-\u017f]+', ' ', text)
        return ' '.join(text.split())
    except Exception:
        return ''


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    target = workspace / 'data' / 'birthdays.md'
    try:
        exists = target.exists()
        detail = 'birthday file exists' if exists else 'birthday file missing'
        checks.append({'name': 'file_exists', 'passed': exists, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'file_exists', 'passed': False, 'detail': f'error checking file existence: {e}'})
        exists = False

    content = ''
    try:
        if exists:
            content = target.read_text(encoding='utf-8', errors='replace')
        else:
            content = ''
        ok = 'valentina' in normalize(content) and '14 02 2000' in normalize(content)
        checks.append({'name': 'valentina_entry_present', 'passed': ok, 'detail': 'found Valentina with date 14.02.2000' if ok else 'Valentina entry or date not found'})
    except Exception as e:
        checks.append({'name': 'valentina_entry_present', 'passed': False, 'detail': f'error reading/parsing file: {e}'})

    try:
        n = normalize(content)
        age_ok = ('wird 26' in n) or ('26' in n and 'valentina' in n)
        checks.append({'name': 'turning_age_included', 'passed': age_ok, 'detail': 'turning age appears to be included' if age_ok else 'turning age 26 not found'})
    except Exception as e:
        checks.append({'name': 'turning_age_included', 'passed': False, 'detail': f'error checking age: {e}'})

    try:
        marker_ok = 'marker person' in normalize(content)
        checks.append({'name': 'marker_preserved', 'passed': marker_ok, 'detail': 'existing marker content preserved' if marker_ok else 'marker content missing'})
    except Exception as e:
        checks.append({'name': 'marker_preserved', 'passed': False, 'detail': f'error checking marker: {e}'})

    try:
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / len(checks) if checks else 0.0
        passed = all(c.get('passed') for c in checks)
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
