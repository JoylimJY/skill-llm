import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        s = s.strip().lower()
        s = re.sub(r'\s+', ' ', s)
        return s
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    out_path = workspace / 'output.json'
    input_path = workspace / 'support_notes.txt'

    try:
        exists = out_path.exists()
    except Exception as e:
        exists = False
        err = str(e)
    else:
        err = ''
    checks.append({'name': 'output_file_exists', 'passed': bool(exists), 'detail': err or ('found' if exists else 'missing')})

    try:
        expected_raw, read_err = safe_read_text(input_path)
        if expected_raw is None:
            checks.append({'name': 'input_readable', 'passed': False, 'detail': read_err})
        else:
            expected_notes = []
            seen = set()
            for line in expected_raw.splitlines():
                n = normalize(line)
                if n and n not in seen:
                    seen.add(n)
                    expected_notes.append(re.sub(r'\s+', ' ', line.strip()))
            checks.append({'name': 'input_has_markers', 'passed': len(expected_notes) >= 4, 'detail': f'unique_candidates={len(expected_notes)}'})
    except Exception as e:
        checks.append({'name': 'input_has_markers', 'passed': False, 'detail': str(e)})
        expected_notes = []

    try:
        if out_path.exists():
            try:
                data = json.loads(out_path.read_text(encoding='utf-8'))
                ok_json = True
                detail = 'parsed'
            except Exception as e:
                data = None
                ok_json = False
                detail = str(e)
        else:
            data = None
            ok_json = False
            detail = 'missing output.json'
        checks.append({'name': 'valid_json', 'passed': ok_json, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'valid_json', 'passed': False, 'detail': str(e)})
        data = None

    try:
        if isinstance(data, dict):
            source_ok = normalize(str(data.get('source_file', ''))).endswith('support_notes.txt')
            checks.append({'name': 'source_file_field', 'passed': source_ok, 'detail': str(data.get('source_file', ''))})
        else:
            checks.append({'name': 'source_file_field', 'passed': False, 'detail': 'output not parsed as object'})
    except Exception as e:
        checks.append({'name': 'source_file_field', 'passed': False, 'detail': str(e)})

    try:
        if isinstance(data, dict):
            notes = data.get('notes')
            if isinstance(notes, list):
                norm_notes = [normalize(str(x)) for x in notes if normalize(str(x))]
                unique_ok = len(norm_notes) == len(set(norm_notes))
                order_ok = True
                if expected_notes:
                    expected_norm = [normalize(x) for x in expected_notes]
                    order_ok = norm_notes == expected_norm
                count_ok = data.get('unique_notes_count') == len(norm_notes)
                checks.append({'name': 'notes_content', 'passed': bool(unique_ok and count_ok and order_ok), 'detail': f'count={data.get("unique_notes_count")}, actual={len(norm_notes)}, order_match={order_ok}'})
            else:
                checks.append({'name': 'notes_content', 'passed': False, 'detail': 'notes is not a list'})
        else:
            checks.append({'name': 'notes_content', 'passed': False, 'detail': 'output not parsed as object'})
    except Exception as e:
        checks.append({'name': 'notes_content', 'passed': False, 'detail': str(e)})

    try:
        total = len(checks)
        passed = sum(1 for c in checks if c.get('passed'))
        score = passed / total if total else 0.0
        result = {'passed': passed == total, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed": false, "score": 0.0, "checks": []}')


if __name__ == '__main__':
    main()