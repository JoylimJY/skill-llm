import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9/_.\-\s]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def contains_fuzzy(text: str, phrases):
    nt = norm(text)
    return all(norm(p) in nt for p in phrases)


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # AGENTS.md
    try:
        agents_path = ws / 'AGENTS.md'
        if not agents_path.exists():
            checks.append({'name': 'AGENTS.md exists', 'passed': False, 'detail': 'AGENTS.md is missing'})
        else:
            txt, err = safe_read(agents_path)
            if txt is None:
                checks.append({'name': 'AGENTS.md readable', 'passed': False, 'detail': f'Could not read AGENTS.md: {err}'})
            else:
                passed = contains_fuzzy(txt, ['build', 'test', 'lint']) and contains_fuzzy(txt, ['docs/auth.md']) and contains_fuzzy(txt, ['docs/db-schema.md'])
                detail = 'Contains build/test/lint and key docs references' if passed else 'Missing one or more required items'
                checks.append({'name': 'AGENTS.md content', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'AGENTS.md content', 'passed': False, 'detail': f'Error: {e}'})

    # llms.txt
    try:
        llms_path = ws / 'llms.txt'
        if not llms_path.exists():
            checks.append({'name': 'llms.txt exists', 'passed': False, 'detail': 'llms.txt is missing'})
        else:
            txt, err = safe_read(llms_path)
            if txt is None:
                checks.append({'name': 'llms.txt readable', 'passed': False, 'detail': f'Could not read llms.txt: {err}'})
            else:
                passed = contains_fuzzy(txt, ['authentication']) and contains_fuzzy(txt, ['database']) and ('auth.md' in txt.lower()) and ('db-schema.md' in txt.lower())
                detail = 'llms.txt includes expected sections and links' if passed else 'Missing expected index entries'
                checks.append({'name': 'llms.txt content', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'llms.txt content', 'passed': False, 'detail': f'Error: {e}'})

    # No invented files check: referenced files should exist
    try:
        expected_files = [ws / 'docs' / 'auth.md', ws / 'docs' / 'db-schema.md', ws / 'references' / 'style.md']
        missing = [str(p.relative_to(ws)) for p in expected_files if not p.exists()]
        passed = len(missing) == 0
        detail = 'All referenced input docs exist' if passed else f'Missing input docs: {missing}'
        checks.append({'name': 'input docs available', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input docs available', 'passed': False, 'detail': f'Error: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
