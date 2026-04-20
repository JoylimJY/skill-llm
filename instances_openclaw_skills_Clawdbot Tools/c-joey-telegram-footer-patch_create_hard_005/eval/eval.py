import json
import os
import re
import sys
from pathlib import Path

FOOTER = '🧠 Model + 💭 Think + 📊 Context'
REPORT = Path('reports/patch_report.json')


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def is_backup_file(path):
    """Check if a file looks like a backup file based on common patterns."""
    name = path.name.lower()
    # Common backup patterns - expanded to be more flexible
    backup_patterns = [
        r'\.backup$',
        r'\.bak$',
        r'\.bak\.',
        r'\.backup\.',
        r'\.orig$',
        r'\.old$',
        r'~$',
        r'\.bck$',
        r'\.patched-backup$',
        r'\.backup-patched$',
        r'-backup$',
        r'-bak$',
        r'\.backup\.js$',
        r'\.bak\.js$',
        r'\.orig\.js$',
        r'\.old\.js$',
    ]
    for pattern in backup_patterns:
        if re.search(pattern, name):
            return True
    # Also check if filename contains backup-related keywords
    backup_keywords = ['backup', 'bak', 'orig', 'old', 'bck', 'saved', 'copy']
    for keyword in backup_keywords:
        if keyword in name and not name.endswith('.js'):
            return True
    return False


def main():
    workspace = Path(sys.argv[1])
    checks = []

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    # Check 1: report exists and is parseable
    try:
        if REPORT.exists():
            data = json.loads(REPORT.read_text(encoding='utf-8'))
            add('report_exists_and_parseable', True, f"report found with keys: {sorted(list(data.keys()))}")
        else:
            add('report_exists_and_parseable', False, 'reports/patch_report.json is missing')
    except Exception as e:
        add('report_exists_and_parseable', False, f'could not parse report: {e}')

    # Check 2: a bundle was patched with footer text
    patched = []
    try:
        for p in workspace.glob('dist/**/*.js'):
            try:
                txt = p.read_text(encoding='utf-8')
            except Exception:
                continue
            if norm(FOOTER) in norm(txt):
                patched.append(p)
        add('footer_embedded_in_some_dist_bundle', len(patched) > 0, f'patched files: {[str(p) for p in patched]}')
    except Exception as e:
        add('footer_embedded_in_some_dist_bundle', False, f'error scanning dist: {e}')

    # Check 3: primary expected bundle exists and either patched or clearly backed up/reported
    try:
        primary = workspace / 'dist' / 'agent-runner.runtime-BWpOtdxK.js'
        if primary.exists():
            txt = primary.read_text(encoding='utf-8')
            ok = norm(FOOTER) in norm(txt)
            add('primary_bundle_touched_or_patched', ok, 'primary bundle contains footer' if ok else 'primary bundle exists but footer not found')
        else:
            add('primary_bundle_touched_or_patched', False, 'primary bundle missing')
    except Exception as e:
        add('primary_bundle_touched_or_patched', False, f'error checking primary bundle: {e}')

    # Check 4: backup file exists for at least one js file (flexible pattern matching)
    try:
        backups = []
        # Look for backup files in dist directory with common backup patterns
        for p in workspace.glob('dist/**/*'):
            if p.is_file() and is_backup_file(p):
                backups.append(p)
        # Also check for backup files that might be named after the original JS files
        for p in workspace.glob('dist/**/*.js*'):
            if p.is_file() and is_backup_file(p):
                backups.append(p)
        # Remove duplicates
        backups = list(set(backups))
        add('backup_created', len(backups) > 0, f'backups: {[str(p) for p in backups]}')
    except Exception as e:
        add('backup_created', False, f'error scanning backups: {e}')

    # Check 5: output does not duplicate footer excessively in patched files
    try:
        dup_ok = True
        detail = []
        for p in patched:
            txt = p.read_text(encoding='utf-8')
            count = norm(txt).count(norm(FOOTER))
            detail.append(f'{p.name}:{count}')
            if count > 2:
                dup_ok = False
        add('no_excessive_duplicate_footer', dup_ok, '; '.join(detail) if detail else 'no patched files to inspect')
    except Exception as e:
        add('no_excessive_duplicate_footer', False, f'error checking duplicates: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()