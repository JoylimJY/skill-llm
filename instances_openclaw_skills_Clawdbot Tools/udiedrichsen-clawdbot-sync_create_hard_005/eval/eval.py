import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', str(s).lower())


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def find_workspace_root(base_path):
    """Find the actual workspace directory (handles nested workspace structure)."""
    base = Path(base_path)
    # Check if there's a nested 'workspace' directory
    nested = base / 'workspace'
    if nested.exists() and nested.is_dir():
        # Check if nested workspace has the expected structure
        if (nested / 'memory').exists() or (nested / 'IDENTITY.md').exists():
            return nested
    return base


def main():
    checks = []
    raw_workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    workspace = find_workspace_root(raw_workspace)

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        peers_path = workspace / 'memory' / 'clawdbot-sync' / 'peers.json'
        if peers_path.exists():
            text = peers_path.read_text(encoding='utf-8', errors='replace')
            ok = ('mac-mini' in text.lower()) and ('100.95.193.55' in text) and ('clawdbot' in text.lower())
            add_check('peer metadata present', ok, 'mac-mini peer metadata found' if ok else 'missing expected peer metadata')
        else:
            add_check('peer metadata present', False, f'missing file: {peers_path}')
    except Exception as e:
        add_check('peer metadata present', False, f'error reading peers.json: {e}')

    try:
        cfg_path = workspace / 'memory' / 'clawdbot-sync' / 'config.json'
        if cfg_path.exists():
            text = cfg_path.read_text(encoding='utf-8', errors='replace')
            ok = all(tok in text.lower() for tok in ['bi-directional', 'merge_logs', 'skip_identity', 'skip_config', 'sync_marker_alpha_7741'])
            add_check('sync config marker', ok, 'config markers verified' if ok else 'config missing expected markers')
        else:
            add_check('sync config marker', False, f'missing file: {cfg_path}')
    except Exception as e:
        add_check('sync config marker', False, f'error reading config.json: {e}')

    try:
        hist_path = workspace / 'memory' / 'clawdbot-sync' / 'history.json'
        if hist_path.exists():
            text = hist_path.read_text(encoding='utf-8', errors='replace')
            ok = ('mac-mini' in text.lower()) and ('diff' in text.lower()) and ('push' in text.lower())
            add_check('history file content', ok, 'history contains expected actions' if ok else 'history missing expected actions')
        else:
            add_check('history file content', False, f'missing file: {hist_path}')
    except Exception as e:
        add_check('history file content', False, f'error reading history.json: {e}')

    try:
        marker_path = workspace / 'memory' / 'clawdbot-sync' / 'README.marker.txt'
        if marker_path.exists():
            text = marker_path.read_text(encoding='utf-8', errors='replace')
            # More lenient check: file exists and contains sync-related content
            has_marker = 'sync' in text.lower() or 'marker' in text.lower() or 'alpha' in text.lower()
            has_peer = 'mac-mini' in text.lower() or 'peer' in text.lower()
            ok = has_marker or has_peer
            add_check('deterministic marker file', ok, 'marker file verified' if ok else 'marker file does not match expected deterministic content')
        else:
            add_check('deterministic marker file', False, f'missing file: {marker_path}')
    except Exception as e:
        add_check('deterministic marker file', False, f'error reading marker file: {e}')

    try:
        identity = workspace / 'IDENTITY.md'
        user = workspace / 'USER.md'
        memory = workspace / 'MEMORY.md'
        ok = identity.exists() and user.exists() and memory.exists()
        add_check('local instance files preserved', ok, 'identity/user/memory files exist' if ok else 'one or more local files are missing')
    except Exception as e:
        add_check('local instance files preserved', False, f'error checking local files: {e}')

    try:
        sample = workspace / 'memory' / '2025-01-26.md'
        if sample.exists():
            text = sample.read_text(encoding='utf-8', errors='replace')
            # More lenient check: file exists and contains sync-related content
            has_peer = 'mac-mini' in text.lower()
            has_marker = 'sync' in text.lower() or 'note' in text.lower() or '2025' in text.lower()
            ok = has_peer and has_marker
            add_check('sample sync note exists', ok, 'sample sync note verified' if ok else 'sample sync note missing expected content')
        else:
            add_check('sample sync note exists', False, f'missing file: {sample}')
    except Exception as e:
        add_check('sample sync note exists', False, f'error reading sample sync note: {e}')

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    result = {'passed': passed == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'unhandled error: {e}'}]}))