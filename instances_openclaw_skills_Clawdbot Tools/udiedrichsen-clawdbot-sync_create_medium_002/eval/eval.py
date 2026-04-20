import json
import os
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    total = 0
    passed = 0

    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    
    # Check if workspace is nested (common in container setups)
    if (workspace / 'workspace').exists():
        workspace = workspace / 'workspace'

    def add_check(name, ok, detail):
        nonlocal total, passed
        total += 1
        if ok:
            passed += 1
        checks.append({"name": name, "passed": bool(ok), "detail": detail})

    try:
        peers_path = workspace / 'memory' / 'clawdbot-sync' / 'peers.json'
        if peers_path.exists():
            try:
                data = json.loads(peers_path.read_text(encoding='utf-8', errors='replace'))
                peers = data.get('peers', []) if isinstance(data, dict) else []
                found = False
                for p in peers:
                    if not isinstance(p, dict):
                        continue
                    text = ' '.join(str(v) for v in p.values()).lower()
                    if 'lab-mac' in text and '100.64.18.22' in text and 'clawdbot' in text:
                        found = True
                        break
                add_check('peer_saved', found, 'Found matching peer entry.' if found else 'No peer entry matching lab-mac / 100.64.18.22 / clawdbot was found.')
            except Exception as e:
                add_check('peer_saved', False, f'Could not parse peers.json: {e}')
        else:
            add_check('peer_saved', False, 'peers.json is missing.')
    except Exception as e:
        add_check('peer_saved', False, f'Unexpected error checking peers.json: {e}')

    try:
        history_path = workspace / 'memory' / 'clawdbot-sync' / 'history.json'
        if history_path.exists():
            try:
                data = json.loads(history_path.read_text(encoding='utf-8', errors='replace'))
                entries = data.get('entries', []) if isinstance(data, dict) else []
                ok = False
                detail = 'No history entry found.'
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    s = ' '.join(f'{k}:{v}' for k, v in entry.items()).lower()
                    if 'lab-mac' in s and ('bootstrap' in s or 'sync' in s):
                        ok = True
                        detail = 'History contains a relevant entry.'
                        break
                add_check('history_present', ok, detail)
            except Exception as e:
                add_check('history_present', False, f'Could not parse history.json: {e}')
        else:
            add_check('history_present', False, 'history.json is missing.')
    except Exception as e:
        add_check('history_present', False, f'Unexpected error checking history.json: {e}')

    try:
        readme = workspace / 'README.txt'
        if readme.exists():
            try:
                text = readme.read_text(encoding='utf-8', errors='replace').lower()
                ok = 'task-workspace-marker-9001' in text
                add_check('workspace_marker', ok, 'Workspace marker present.' if ok else 'Workspace marker missing.')
            except Exception as e:
                add_check('workspace_marker', False, f'Could not read README.txt: {e}')
        else:
            add_check('workspace_marker', False, 'README.txt is missing.')
    except Exception as e:
        add_check('workspace_marker', False, f'Unexpected error checking workspace marker: {e}')

    score = (passed / total) if total else 0.0
    result = {"passed": passed == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()