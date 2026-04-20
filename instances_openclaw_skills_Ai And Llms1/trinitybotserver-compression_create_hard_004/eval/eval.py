from pathlib import Path
import json
import os
import re
import sys


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        # Required install artifacts
        expected_files = [
            'trinity-compress.config.json',
            'scripts/trinity-compress.sh',
            'scripts/install.ps1',
            'scripts/install.sh',
            '.gitignore',
        ]
        for rel in expected_files:
            p = ws / rel
            add(f'file exists: {rel}', p.exists(), 'found' if p.exists() else 'missing')

        # Content checks (forgiving)
        cfg_text, cfg_err = safe_read(ws / 'trinity-compress.config.json')
        if cfg_text is None:
            add('config readable', False, f'read error: {cfg_err}')
        else:
            add('config contains rules/targets markers', 'targets' in cfg_text.lower() or 'rules' in cfg_text.lower(), 'mentions targets/rules' if ('targets' in cfg_text.lower() or 'rules' in cfg_text.lower()) else 'missing expected content')

        script_text, script_err = safe_read(ws / 'scripts' / 'trinity-compress.sh')
        if script_text is None:
            add('compress script readable', False, f'read error: {script_err}')
        else:
            lowered = script_text.lower()
            add('compress script supports balanced mode', 'balanced' in lowered, 'balanced mode referenced' if 'balanced' in lowered else 'balanced mode not found')
            add('compress script supports undo or backup handling', ('undo' in lowered) or ('.bak' in lowered), 'undo/.bak referenced' if ('undo' in lowered or '.bak' in lowered) else 'missing undo/backup references')

        gitignore_text, gitignore_err = safe_read(ws / '.gitignore')
        if gitignore_text is None:
            add('.gitignore readable', False, f'read error: {gitignore_err}')
        else:
            add('.gitignore ignores bak files', '*.bak' in gitignore_text or '.bak' in gitignore_text, 'bak ignore present' if ('*.bak' in gitignore_text or '.bak' in gitignore_text) else 'bak ignore missing')

        # Generated markers must still be present
        marker_checks = [
            ('prompts/main.prompt.txt', 'trinity_marker_alpha'),
            ('prompts/secondary.prompt.txt', 'trinity_marker_beta'),
            ('assets/sample.json', 'trinity_marker_json_42'),
        ]
        for rel, marker in marker_checks:
            txt, err = safe_read(ws / rel)
            if txt is None:
                add(f'marker present: {rel}', False, f'read error: {err}')
            else:
                add(f'marker present: {rel}', marker in txt.lower(), 'marker found' if marker in txt.lower() else f'marker {marker} missing')

        # Optional install scripts should mention copying/installing assets
        ps1_text, ps1_err = safe_read(ws / 'scripts' / 'install.ps1')
        if ps1_text is None:
            add('install.ps1 readable', False, f'read error: {ps1_err}')
        else:
            add('install.ps1 present', len(ps1_text.strip()) > 0, 'non-empty' if len(ps1_text.strip()) > 0 else 'empty')

        sh_text, sh_err = safe_read(ws / 'scripts' / 'install.sh')
        if sh_text is None:
            add('install.sh readable', False, f'read error: {sh_err}')
        else:
            add('install.sh present', len(sh_text.strip()) > 0, 'non-empty' if len(sh_text.strip()) > 0 else 'empty')

    except Exception as e:
        add('unexpected evaluator exception handled', False, f'{type(e).__name__}: {e}')

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    result = {'passed': passed_count == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
