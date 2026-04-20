import json
import re
from pathlib import Path
import sys


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def fuzzy_contains(text, needle):
    try:
        if text is None:
            return False
        norm_text = re.sub(r'[^a-z0-9]+', ' ', text.lower())
        norm_needle = re.sub(r'[^a-z0-9]+', ' ', needle.lower())
        return norm_needle.strip() in norm_text
    except Exception:
        return False


def main():
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    required = ['TASK.md', 'CHANGELOG.md', 'CONTEXT.md', 'WEEKLY-REPORT.md', 'llms.txt']
    for name in required:
        try:
            p = ws / name
            exists = p.exists()
            checks.append({
                'name': f'{name} exists',
                'passed': exists,
                'detail': 'found' if exists else 'missing'
            })
        except Exception as e:
            checks.append({'name': f'{name} exists', 'passed': False, 'detail': str(e)})

    try:
        task, err = safe_read(ws / 'TASK.md')
        passed = fuzzy_contains(task, 'alpha-notes') and fuzzy_contains(task, 'task')
        checks.append({'name': 'TASK.md content', 'passed': passed, 'detail': 'contains project name and task context' if passed else f'unexpected or unreadable: {err}'})
    except Exception as e:
        checks.append({'name': 'TASK.md content', 'passed': False, 'detail': str(e)})

    try:
        changelog, err = safe_read(ws / 'CHANGELOG.md')
        has_tag = bool(re.search(r'#[A-Za-z0-9_-]+', changelog or ''))
        has_identity = fuzzy_contains(changelog, 'by')
        passed = has_tag and has_identity
        checks.append({'name': 'CHANGELOG.md tagged identity entry', 'passed': passed, 'detail': 'tag and identity found' if passed else f'missing tag or identity: {err}'})
    except Exception as e:
        checks.append({'name': 'CHANGELOG.md tagged identity entry', 'passed': False, 'detail': str(e)})

    try:
        llms, err = safe_read(ws / 'llms.txt')
        passed = fuzzy_contains(llms, 'alpha-notes') or fuzzy_contains(llms, 'agent sync')
        checks.append({'name': 'llms.txt index', 'passed': passed, 'detail': 'index text found' if passed else f'not found or unreadable: {err}'})
    except Exception as e:
        checks.append({'name': 'llms.txt index', 'passed': False, 'detail': str(e)})

    try:
        marker, err = safe_read(ws / 'seed_marker.txt')
        passed = fuzzy_contains(marker, 'AGENT_SYNC_MARKER')
        checks.append({'name': 'input marker present', 'passed': passed, 'detail': 'marker verified' if passed else f'missing marker: {err}'})
    except Exception as e:
        checks.append({'name': 'input marker present', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
