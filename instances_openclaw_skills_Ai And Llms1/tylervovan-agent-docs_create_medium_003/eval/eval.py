import json
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text):
    if text is None:
        return ''
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-z0-9\-_/ .:]+', '', text)
    return text.strip()


def main():
    checks = []
    workspace = Path(sys.argv[1])

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        target = workspace / 'AGENTS.md'
        if not target.exists():
            add_check('AGENTS.md exists', False, 'AGENTS.md is missing')
        else:
            text = target.read_text(encoding='utf-8', errors='replace')
            n = normalize(text)
            has_critical = 'critical' in n and 'do not' in n
            has_index = 'docs index' in n or 'docs map' in n or 'documentation map' in n
            has_build = 'build' in n and 'test' in n and 'lint' in n
            has_constraints = 'app/' in n and 'no secrets' in n
            add_check('AGENTS.md exists', True, 'AGENTS.md found')
            add_check('Governance and constraints', has_critical and has_constraints, 'Checks for critical rules, app/ usage, and no-secrets guidance')
            add_check('Docs index and commands', has_index and has_build, 'Checks for docs index and build/test/lint command guidance')
            add_check('Concise agent-friendly structure', len(text) > 0 and len(text) < 8000, f'Length {len(text)} characters')
    except Exception as e:
        add_check('AGENTS.md check', False, f'Error: {e}')

    try:
        target = workspace / 'llms.txt'
        if not target.exists():
            add_check('llms.txt exists', False, 'llms.txt is missing')
        else:
            text = target.read_text(encoding='utf-8', errors='replace')
            n = normalize(text)
            has_project = 'project' in n or 'acme' in n
            has_links = '.md' in n and '[' in text and ']' in text
            has_summary = 'one-line' in n or 'description' in n
            add_check('llms.txt exists', True, 'llms.txt found')
            add_check('llms.txt machine-readable index', has_project and has_links and has_summary, 'Checks for project header, linked sections, and short descriptions')
    except Exception as e:
        add_check('llms.txt check', False, f'Error: {e}')

    try:
        target = workspace / 'references' / 'advanced-patterns.md'
        if not target.exists():
            add_check('Referenced advanced patterns file exists', False, 'references/advanced-patterns.md is missing')
        else:
            text = target.read_text(encoding='utf-8', errors='replace')
            n = normalize(text)
            has_marker = 'adv-pattern-4d11' in n
            has_constraints = 'no direct database queries' in n or 'no secrets' in n or 'constraints' in n
            add_check('Referenced advanced patterns file exists', True, 'advanced patterns file found')
            add_check('Advanced patterns content preserved', has_marker and has_constraints, 'Checks for embedded marker and constraint language')
    except Exception as e:
        add_check('Referenced file check', False, f'Error: {e}')

    try:
        manifest = workspace / 'manifest.json'
        if not manifest.exists():
            add_check('Manifest exists', False, 'manifest.json is missing')
        else:
            data = json.loads(manifest.read_text(encoding='utf-8', errors='replace'))
            markers = ' '.join(map(str, data.get('markers', [])))
            ok = all(m in markers for m in ['AUTH-INDEX-7F3A', 'DB-SCHEMA-91C2', 'ADV-PATTERN-4D11'])
            add_check('Manifest exists', True, 'manifest.json found')
            add_check('Manifest markers present', ok, 'Checks deterministic marker inventory')
    except Exception as e:
        add_check('Manifest check', False, f'Error: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    result = {
        'passed': passed == total and total > 0,
        'score': (passed / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()
