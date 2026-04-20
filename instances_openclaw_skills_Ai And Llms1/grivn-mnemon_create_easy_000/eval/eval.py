import json
import os
from pathlib import Path


def normalize(text):
    try:
        return ''.join(ch.lower() for ch in str(text) if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def safe_read(path):
    try:
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        return content, None
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    try:
        mem_dir = workspace / 'inputs'
        manifest_path = mem_dir / 'manifest.json'
        ok = manifest_path.exists()
        detail = 'manifest found' if ok else 'manifest missing'
        checks.append({'name': 'input manifest exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input manifest exists', 'passed': False, 'detail': f'error: {e}'})

    try:
        expected_marker = 'MNEMON_MARKER_ALPHA_2025'
        all_found = True
        missing = []
        for fname in ['memory1.txt', 'memory2.txt', 'memory3.txt']:
            p = workspace / 'inputs' / fname
            content, err = safe_read(p)
            if content is None:
                all_found = False
                missing.append(f'{fname}: {err}')
                continue
            if normalize(expected_marker) not in normalize(content):
                all_found = False
                missing.append(f'{fname}: marker not found')
        checks.append({'name': 'input files contain marker', 'passed': all_found, 'detail': '; '.join(missing) if missing else 'all markers present'})
    except Exception as e:
        checks.append({'name': 'input files contain marker', 'passed': False, 'detail': f'error: {e}'})

    try:
        # Check for mnemon default store in common locations
        possible_stores = [
            workspace / '.mnemon',
            Path('/root/.cache/mnemon'),
            Path(os.path.expanduser('~/.cache/mnemon')),
            Path(os.path.expanduser('~/.mnemon'))
        ]
        found_store = None
        for store_path in possible_stores:
            if store_path.exists():
                found_store = store_path
                break
        
        ok = found_store is not None
        detail = f'store found at {found_store}' if ok else 'mnemon store directory not found'
        checks.append({'name': 'mnemon config directory exists', 'passed': ok, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'mnemon config directory exists', 'passed': False, 'detail': f'error: {e}'})

    try:
        total = len(checks)
        passed = sum(1 for c in checks if c['passed'])
        score = (passed / total) if total else 0.0
        result = {'passed': passed == total, 'score': score, 'checks': checks}
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}))


if __name__ == '__main__':
    main()