import json
import os
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s):
    if s is None:
        return ''
    return ''.join(ch.lower() for ch in s if ch.isalnum())


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)

    expected_files = [
        'skill/SKILL.md',
        'docs/marker.txt',
    ]
    for rel in expected_files:
        p = ws / rel
        try:
            exists = p.exists()
            content, err = (safe_read(p) if exists else (None, 'missing'))
            marker_ok = False
            if content:
                marker_ok = 'marker_trinity_compression_7f3a2c' in norm(content)
            passed = exists and marker_ok
            detail = 'ok' if passed else f"exists={exists}; error={err if not exists else 'marker missing'}"
        except Exception as e:
            passed = False
            detail = str(e)
        checks.append({'name': f'input file {rel}', 'passed': passed, 'detail': detail})

    # Task-specific output expectations
    out1 = ws / 'trinity-compress.config.json'
    out2 = ws / 'scripts' / 'trinity-compress.sh'
    out3 = ws / 'scripts' / 'install.sh'
    out4 = ws / 'scripts' / 'install.ps1'
    out5 = ws / '.gitignore'
    out6 = ws / 'Makefile'

    try:
        cfg_ok = False
        if out1.exists():
            txt, err = safe_read(out1)
            if txt:
                cfg_ok = 'trinity' in norm(txt) and 'compress' in norm(txt)
        checks.append({'name': 'config created', 'passed': cfg_ok, 'detail': 'ok' if cfg_ok else 'missing or invalid'})
    except Exception as e:
        checks.append({'name': 'config created', 'passed': False, 'detail': str(e)})

    try:
        sh_ok = out2.exists() and os.access(out2, os.X_OK)
        checks.append({'name': 'compress script executable', 'passed': sh_ok, 'detail': 'ok' if sh_ok else 'missing or not executable'})
    except Exception as e:
        checks.append({'name': 'compress script executable', 'passed': False, 'detail': str(e)})

    try:
        install_ok = False
        if out3.exists() and out4.exists():
            sh_txt, _ = safe_read(out3)
            ps_txt, _ = safe_read(out4)
            install_ok = bool(sh_txt and ps_txt and ('jq' in norm(sh_txt) or 'jq' in norm(ps_txt)))
        checks.append({'name': 'installers created', 'passed': install_ok, 'detail': 'ok' if install_ok else 'missing or invalid installers'})
    except Exception as e:
        checks.append({'name': 'installers created', 'passed': False, 'detail': str(e)})

    try:
        git_ok = False
        if out5.exists():
            txt, _ = safe_read(out5)
            git_ok = '*.bak' in (txt or '')
        checks.append({'name': 'gitignore updated', 'passed': git_ok, 'detail': 'ok' if git_ok else 'missing *.bak ignore'})
    except Exception as e:
        checks.append({'name': 'gitignore updated', 'passed': False, 'detail': str(e)})

    try:
        make_ok = False
        if out6.exists():
            txt, _ = safe_read(out6)
            if txt:
                low = txt.lower()
                make_ok = ('optimize-prompts' in low) and ('optimize-undo' in low)
        checks.append({'name': 'makefile snippet added', 'passed': make_ok, 'detail': 'ok' if make_ok else 'missing targets'})
    except Exception as e:
        checks.append({'name': 'makefile snippet added', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    result = {'passed': passed_count == total, 'score': passed_count / total if total else 0.0, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
