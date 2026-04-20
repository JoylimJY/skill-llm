import json
import os
import re
from pathlib import Path


def normalize(text):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    except Exception:
        return ''


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        output_path = workspace / 'output.txt'
        if not output_path.exists():
            add_check('output_exists', False, 'output.txt is missing')
            content = ''
        else:
            content = output_path.read_text(encoding='utf-8', errors='replace')
            add_check('output_exists', True, 'output.txt found')
    except Exception as e:
        content = ''
        add_check('output_exists', False, f'Could not read output.txt: {e}')

    try:
        json_path = workspace / 'summary.json'
        if not json_path.exists():
            add_check('summary_exists', False, 'summary.json is missing')
            summary = None
        else:
            summary = json.loads(json_path.read_text(encoding='utf-8', errors='replace'))
            add_check('summary_exists', True, 'summary.json found')
    except Exception as e:
        summary = None
        add_check('summary_exists', False, f'Could not parse summary.json: {e}')

    # Bullet count and content checks
    try:
        lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
        bullets = [ln for ln in lines if ln.startswith(('-', '*', '•'))]
        passed = len(bullets) >= 6
        add_check('six_bullets', passed, f'Found {len(bullets)} bullet-like lines')
    except Exception as e:
        add_check('six_bullets', False, f'Bullet parsing failed: {e}')

    expected_phrases = [
        'ask permission',
        'use tools',
        'search first',
        'fix',
        'idle',
        'act first and report second',
    ]
    try:
        ncontent = normalize(content)
        found = sum(1 for p in expected_phrases if normalize(p) in ncontent)
        add_check('key_phrases', found >= 5, f'Found {found}/{len(expected_phrases)} expected themes')
    except Exception as e:
        add_check('key_phrases', False, f'Phrase matching failed: {e}')

    try:
        if isinstance(summary, dict):
            title_ok = isinstance(summary.get('title'), str) and len(summary.get('title', '').strip()) > 0
            highlights = summary.get('highlights')
            arr_ok = isinstance(highlights, list) and len(highlights) == 3 and all(isinstance(x, str) and x.strip() for x in highlights)
            add_check('summary_schema', title_ok and arr_ok, 'summary.json has required keys and 3 non-empty highlights')
        else:
            add_check('summary_schema', False, 'summary.json is not a JSON object')
    except Exception as e:
        add_check('summary_schema', False, f'Schema check failed: {e}')

    try:
        marker_path = workspace / 'input_marker.txt'
        marker_text = marker_path.read_text(encoding='utf-8', errors='replace') if marker_path.exists() else ''
        marker_ok = 'ARK-5429' in marker_text
        add_check('input_marker_present', marker_ok, 'Marker ARK-5429 verified in input_marker.txt' if marker_ok else 'Marker missing from input_marker.txt')
    except Exception as e:
        add_check('input_marker_present', False, f'Marker check failed: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    result = {
        'passed': total > 0 and passed == total,
        'score': (passed / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
