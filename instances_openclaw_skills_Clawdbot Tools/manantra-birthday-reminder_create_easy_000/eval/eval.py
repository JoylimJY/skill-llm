import json
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', str(s).lower())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    data_dir = workspace / 'data'
    
    # Find birthday file (accept both .txt and .md extensions)
    birthday_file = None
    if data_dir.exists():
        for f in data_dir.iterdir():
            if f.is_file() and f.name.lower().startswith('birthday'):
                birthday_file = f
                break
    
    try:
        exists = birthday_file is not None
        checks.append({
            'name': 'birthday file exists',
            'passed': bool(exists),
            'detail': f'Found {birthday_file.name}' if exists else 'Missing birthday file in data/'
        })
    except Exception as e:
        checks.append({
            'name': 'birthday file exists',
            'passed': False,
            'detail': f'Error checking file existence: {e}'
        })

    try:
        content = birthday_file.read_text(encoding='utf-8') if birthday_file else ''
        n = norm(content)
        # Check for valentina, date (with or without dots), and age info (turning/wird)
        has_valentina = 'valentina' in n
        has_date = '14022000' in n or '14.02.2000' in content or '14-02-2000' in content
        has_age_info = 'turning' in n or 'wird' in n or re.search(r'\d{2}', content)
        ok = has_valentina and has_date and has_age_info
        checks.append({
            'name': 'contains valentina entry with age info',
            'passed': bool(ok),
            'detail': 'Valentina entry with date and age info detected' if ok else 'Could not find expected Valentina birthday entry with age info'
        })
    except Exception as e:
        checks.append({
            'name': 'contains valentina entry with age info',
            'passed': False,
            'detail': f'Error reading/parsing birthday file: {e}'
        })

    try:
        marker = workspace / 'data' / 'marker.txt'
        mcontent = marker.read_text(encoding='utf-8') if marker.exists() else ''
        ok = 'BIRTHDAY_REMINDER_MARKER_7F3A2C' in mcontent
        checks.append({
            'name': 'input marker preserved',
            'passed': bool(ok),
            'detail': 'Marker file contains expected deterministic token' if ok else 'Marker token missing or changed'
        })
    except Exception as e:
        checks.append({
            'name': 'input marker preserved',
            'passed': False,
            'detail': f'Error checking marker file: {e}'
        })

    try:
        total = len(checks)
        passed_count = sum(1 for c in checks if c.get('passed'))
        score = passed_count / total if total else 0.0
        passed = passed_count == total
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()