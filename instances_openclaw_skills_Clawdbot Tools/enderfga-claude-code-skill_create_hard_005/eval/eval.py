import json
import os
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: seed_data.json exists and contains marker
try:
    p = workspace / 'seed_data.json'
    if not p.exists():
        add_check('seed_data_exists', False, 'seed_data.json is missing')
    else:
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            marker = str(data.get('marker', '')).lower()
            ok = 'openclaw_deterministic_marker_7f3a' in marker
            add_check('seed_data_marker', ok, f"marker={'present' if ok else 'missing or different'}")
        except Exception as e:
            add_check('seed_data_marker', False, f'could not parse seed_data.json: {e}')
except Exception as e:
    add_check('seed_data_exists', False, f'error checking seed_data.json: {e}')

# Check 2: source_note.txt contains marker text
try:
    p = workspace / 'source_note.txt'
    if not p.exists():
        add_check('source_note_exists', False, 'source_note.txt is missing')
    else:
        try:
            text = p.read_text(encoding='utf-8', errors='ignore').lower()
            ok = 'openclaw_deterministic_marker_7f3a' in text
            add_check('source_note_marker', ok, f"marker={'present' if ok else 'missing'}")
        except Exception as e:
            add_check('source_note_marker', False, f'could not read source_note.txt: {e}')
except Exception as e:
    add_check('source_note_exists', False, f'error checking source_note.txt: {e}')

# Check 3: expected_config_template.json matches key structure fuzzily
try:
    p = workspace / 'expected_config_template.json'
    if not p.exists():
        add_check('config_template_exists', False, 'expected_config_template.json is missing')
    else:
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            servers = data.get('mcpServers', {})
            fs = servers.get('filesystem', {})
            gh = servers.get('github', {})
            fs_ok = 'filesystem' in servers and str(fs.get('command', '')).lower() == 'npx' and any('server-filesystem' in str(a).lower() for a in fs.get('args', []))
            gh_ok = 'github' in servers and str(gh.get('command', '')).lower() == 'npx' and any('server-github' in str(a).lower() for a in gh.get('args', []))
            add_check('config_template_structure', fs_ok and gh_ok, f'filesystem_ok={fs_ok}, github_ok={gh_ok}')
        except Exception as e:
            add_check('config_template_structure', False, f'could not parse expected_config_template.json: {e}')
except Exception as e:
    add_check('config_template_exists', False, f'error checking expected_config_template.json: {e}')

# Check 4: output README-style note if present
try:
    candidates = [workspace / 'README.md', workspace / 'readme.md', workspace / 'NOTE.txt', workspace / 'note.txt']
    found = None
    for c in candidates:
        if c.exists():
            found = c
            break
    if not found:
        add_check('readme_note_exists', False, 'No README-style note file found')
    else:
        try:
            text = found.read_text(encoding='utf-8', errors='ignore').lower()
            ok = ('mcp' in text) and ('filesystem' in text) and ('github' in text) and ('session' in text or 'sync' in text)
            add_check('readme_note_content', ok, f'found={found.name}, content_looks_right={ok}')
        except Exception as e:
            add_check('readme_note_content', False, f'could not read {found}: {e}')
except Exception as e:
    add_check('readme_note_exists', False, f'error checking note files: {e}')

# Score
try:
    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = (passed / total) if total else 0.0
    result = {"passed": passed == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
except Exception:
    print('{"passed": false, "score": 0.0, "checks": []}')
