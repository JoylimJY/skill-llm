import json
import os
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(text):
    try:
        import re
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-z0-9_\- .]+', '', text)
        return text.strip()
    except Exception:
        return ''


def main(workspace_dir):
    checks = []
    total = 0
    passed_count = 0

    def add_check(name, passed, detail):
        nonlocal total, passed_count
        total += 1
        if passed:
            passed_count += 1
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    ws = Path(workspace_dir)
    try:
        out_path = ws / 'output.txt'
        if out_path.exists():
            content = safe_read(out_path)
            if isinstance(content, tuple):
                add_check('output_exists_and_readable', False, f'output.txt exists but could not be read: {content[1]}')
            else:
                txt = content
                ok = len(txt.strip()) > 0
                add_check('output_exists_and_nonempty', ok, 'output.txt contains text' if ok else 'output.txt is empty')
        else:
            add_check('output_exists_and_nonempty', False, 'output.txt is missing')
    except Exception as e:
        add_check('output_exists_and_nonempty', False, f'Unexpected error: {e}')

    try:
        prompt_path = ws / 'prompt.txt'
        if prompt_path.exists():
            content = safe_read(prompt_path)
            if isinstance(content, tuple):
                add_check('prompt_marker_present', False, f'prompt.txt unreadable: {content[1]}')
            else:
                ok = 'marker_prompt' in normalize(content)
                add_check('prompt_marker_present', ok, 'Found marker content in prompt.txt' if ok else 'Missing MARKER_PROMPT in prompt.txt')
        else:
            add_check('prompt_marker_present', False, 'prompt.txt is missing')
    except Exception as e:
        add_check('prompt_marker_present', False, f'Unexpected error: {e}')

    try:
        system_path = ws / 'system.txt'
        if system_path.exists():
            content = safe_read(system_path)
            if isinstance(content, tuple):
                add_check('system_marker_present', False, f'system.txt unreadable: {content[1]}')
            else:
                ok = 'marker_system' in normalize(content)
                add_check('system_marker_present', ok, 'Found marker content in system.txt' if ok else 'Missing MARKER_SYSTEM in system.txt')
        else:
            add_check('system_marker_present', False, 'system.txt is missing')
    except Exception as e:
        add_check('system_marker_present', False, f'Unexpected error: {e}')

    try:
        md_path = ws / 'metadata.json'
        if md_path.exists():
            content = safe_read(md_path)
            if isinstance(content, tuple):
                add_check('metadata_json_valid', False, f'metadata.json unreadable: {content[1]}')
            else:
                try:
                    obj = json.loads(content)
                    ok = obj.get('marker') == 'MARKER_META_7F3A'
                    add_check('metadata_json_valid', ok, 'metadata marker verified' if ok else 'metadata marker mismatch')
                except Exception as e:
                    add_check('metadata_json_valid', False, f'Invalid JSON: {e}')
        else:
            add_check('metadata_json_valid', False, 'metadata.json is missing')
    except Exception as e:
        add_check('metadata_json_valid', False, f'Unexpected error: {e}')

    score = (passed_count / total) if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    main(workspace)