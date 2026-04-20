import json
import re
import sys
from pathlib import Path


def norm(s):
    try:
        s = s.lower()
        s = re.sub(r'[^a-z0-9]+', '', s)
        return s
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # TASK.md
    try:
        p = workspace / 'TASK.md'
        if not p.exists():
            add_check('TASK.md exists', False, 'TASK.md is missing')
        else:
            text = p.read_text(encoding='utf-8', errors='replace')
            text_n = norm(text)
            ok = 'lighthouse' in text_n and ('done' in text_n or 'completed' in text_n)
            add_check('TASK.md content', ok, 'Contains project name and completed/done markers' if ok else 'Missing project name or completion markers')
    except Exception as e:
        add_check('TASK.md content', False, f'Error reading TASK.md: {e}')

    # CHANGELOG.md
    try:
        p = workspace / 'CHANGELOG.md'
        if not p.exists():
            add_check('CHANGELOG.md exists', False, 'CHANGELOG.md is missing')
        else:
            text = p.read_text(encoding='utf-8', errors='replace')
            tn = norm(text)
            ok = ('#docs' in text.lower()) and ('#sync' in text.lower()) and ('byopal' in tn or 'byop' in tn) and ('lighthouse' in tn)
            add_check('CHANGELOG.md tags', ok, 'Has required tags and identity' if ok else 'Missing required tags or identity')
    except Exception as e:
        add_check('CHANGELOG.md tags', False, f'Error reading CHANGELOG.md: {e}')

    # CONTEXT.md
    try:
        p = workspace / 'CONTEXT.md'
        if not p.exists():
            add_check('CONTEXT.md exists', False, 'CONTEXT.md is missing')
        else:
            text = p.read_text(encoding='utf-8', errors='replace')
            tn = norm(text)
            ok = ('documentdrivensync' in tn or 'document-driven sync' in text.lower()) and ('qmd' in text.lower())
            add_check('CONTEXT.md decision record', ok, 'Contains sync decision and QMD reference' if ok else 'Missing decision record or QMD reference')
    except Exception as e:
        add_check('CONTEXT.md decision record', False, f'Error reading CONTEXT.md: {e}')

    # WEEKLY-REPORT.md
    try:
        p = workspace / 'WEEKLY-REPORT.md'
        if not p.exists():
            add_check('WEEKLY-REPORT.md exists', False, 'WEEKLY-REPORT.md is missing')
        else:
            text = p.read_text(encoding='utf-8', errors='replace')
            tl = text.lower()
            ok1 = 'pattern discovery' in tl
            ok2 = '#docs' in tl and '#sync' in tl
            ok3 = 'candidate skill' in tl or 'candidate skill pool' in tl
            add_check('WEEKLY-REPORT.md sections', ok1 and ok2 and ok3, 'Includes pattern discovery, tag aggregation, and candidate skill note' if ok1 and ok2 and ok3 else 'Missing one or more required weekly report sections')
    except Exception as e:
        add_check('WEEKLY-REPORT.md sections', False, f'Error reading WEEKLY-REPORT.md: {e}')

    # llms.txt
    try:
        p = workspace / 'llms.txt'
        if not p.exists():
            add_check('llms.txt exists', False, 'llms.txt is missing')
        else:
            text = p.read_text(encoding='utf-8', errors='replace')
            tl = text.lower()
            ok = 'TASK.md' in text and 'CHANGELOG.md' in text and 'CONTEXT.md' in text and 'WEEKLY-REPORT.md' in text and 'lighthouse' in tl
            add_check('llms.txt index', ok, 'Contains required file references and project name' if ok else 'Missing required references')
    except Exception as e:
        add_check('llms.txt index', False, f'Error reading llms.txt: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    result = {'passed': passed == total, 'score': passed / total if total else 0.0, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
