import json
import os
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return ''.join(ch.lower() for ch in s if ch.isalnum())
    except Exception:
        return ''


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        p = ws / 'input' / 'prompt.txt'
        txt, err = safe_read(p)
        if txt is None:
            add_check('prompt file exists and readable', False, f'missing or unreadable: {err}')
        else:
            ok = 'marker_prompt_alpha' in txt.lower()
            add_check('prompt marker present', ok, 'found marker' if ok else 'marker_prompt_alpha not found')
    except Exception as e:
        add_check('prompt marker present', False, f'exception: {e}')

    try:
        p = ws / 'input' / 'sample_request.json'
        txt, err = safe_read(p)
        if txt is None:
            add_check('sample request exists and readable', False, f'missing or unreadable: {err}')
        else:
            try:
                data = json.loads(txt)
                model = normalize(str(data.get('model', '')))
                msgs = data.get('messages', [])
                ok = model == 'llama38b8192' or 'llama38b8192' in model
                ok = ok and isinstance(msgs, list) and len(msgs) > 0
                content = ''
                if msgs and isinstance(msgs[0], dict):
                    content = str(msgs[0].get('content', ''))
                ok = ok and 'marker_request_beta' in content.lower()
                add_check('sample request structure', ok, 'json parsed and marker checked' if ok else 'json structure or marker mismatch')
            except Exception as e:
                add_check('sample request structure', False, f'json parse error: {e}')
    except Exception as e:
        add_check('sample request structure', False, f'exception: {e}')

    try:
        p = ws / 'input' / 'notes.txt'
        txt, err = safe_read(p)
        if txt is None:
            add_check('notes file exists and readable', False, f'missing or unreadable: {err}')
        else:
            ok = 'marker_notes_gamma' in txt.lower()
            add_check('notes marker present', ok, 'found marker' if ok else 'marker_notes_gamma not found')
    except Exception as e:
        add_check('notes marker present', False, f'exception: {e}')

    passed = all(c['passed'] for c in checks) if checks else False
    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')