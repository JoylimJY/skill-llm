import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def has_any(text, keywords):
    t = norm(text)
    return any(norm(k) in t for k in keywords)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    expected_files = [
        ('press_release.md', ['lumadesk', 'press', 'launch']),
        ('fact_sheet.md', ['lumadesk', '12-hour', 'usb-c']),
        ('social_posts.json', ['lumadesk'])
    ]

    for fname, kws in expected_files:
        try:
            p = workspace / fname
            if not p.exists():
                checks.append({'name': f'file_exists:{fname}', 'passed': False, 'detail': 'missing file'})
                continue
            txt, err = safe_read(p)
            if txt is None:
                checks.append({'name': f'file_read:{fname}', 'passed': False, 'detail': err})
                continue
            passed = has_any(txt, kws)
            checks.append({'name': f'content:{fname}', 'passed': passed, 'detail': 'keywords found' if passed else 'required keywords not found'})
        except Exception as e:
            checks.append({'name': f'check:{fname}', 'passed': False, 'detail': str(e)})

    try:
        p = workspace / 'social_posts.json'
        if p.exists():
            raw, err = safe_read(p)
            if raw is None:
                checks.append({'name': 'json_validity', 'passed': False, 'detail': err})
            else:
                try:
                    data = json.loads(raw)
                    # Accept either a list of 5 posts or a dict with a "posts" key containing 5 items
                    if isinstance(data, list):
                        ok = len(data) == 5
                        detail = '5 posts present' if ok else f'expected 5-item list, got list length {len(data)}'
                    elif isinstance(data, dict) and 'posts' in data:
                        posts = data['posts']
                        ok = isinstance(posts, list) and len(posts) == 5
                        detail = '5 posts present' if ok else f'expected posts list with 5 items, got {type(posts).__name__} length {len(posts) if hasattr(posts, "__len__") else "n/a"}'
                    else:
                        ok = False
                        detail = f'expected list or dict with posts key, got {type(data).__name__}'
                    checks.append({'name': 'json_validity', 'passed': ok, 'detail': detail})
                except Exception as e:
                    checks.append({'name': 'json_validity', 'passed': False, 'detail': f'json parse error: {e}'})
        else:
            checks.append({'name': 'json_validity', 'passed': False, 'detail': 'social_posts.json missing'})
    except Exception as e:
        checks.append({'name': 'json_validity', 'passed': False, 'detail': str(e)})

    try:
        notes = workspace / 'notes.txt'
        if notes.exists():
            txt, _ = safe_read(notes)
            passed = txt is not None and 'MARKER:LAUNCH-42' in txt
            checks.append({'name': 'input_marker', 'passed': passed, 'detail': 'marker present' if passed else 'marker missing'})
        else:
            checks.append({'name': 'input_marker', 'passed': False, 'detail': 'notes.txt missing'})
    except Exception as e:
        checks.append({'name': 'input_marker', 'passed': False, 'detail': str(e)})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))