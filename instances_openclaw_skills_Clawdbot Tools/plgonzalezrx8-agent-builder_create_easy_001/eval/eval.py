import json
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def contains_any(text, patterns):
    """Check if text contains any of the patterns (case-insensitive)"""
    if not text:
        return False
    low = text.lower()
    for pattern in patterns:
        if re.search(pattern.lower(), low):
            return True
    return False


def check_file_exists(workspace, name):
    p = Path(workspace) / name
    try:
        return p.exists(), f'found' if p.exists() else 'missing'
    except Exception as e:
        return False, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    files = {
        'IDENTITY.md': [
            r'harbor',
            r'assistant',
            r'agent',
            r'identity',
            r'name'
        ],
        'SOUL.md': [
            r'permission',
            r'destructive',
            r'message',
            r'approval',
            r'safety'
        ],
        'AGENTS.md': [
            r'agent',
            r'memory',
            r'error',
            r'delegat',
            r'protocol'
        ],
        'USER.md': [
            r'user',
            r'context',
            r'interaction'
        ],
        'HEARTBEAT.md': [
            r'checklist',
            r'heartbeat',
            r'status',
            r'check'
        ],
    }

    for fname, required_patterns in files.items():
        try:
            exists = (workspace / fname).exists()
            detail = 'exists' if exists else 'missing'
            passed = exists
            if exists and required_patterns:
                text, err = safe_read(workspace / fname)
                if text is None:
                    passed = False
                    detail = f'read error: {err}'
                else:
                    matched = [p for p in required_patterns if re.search(p.lower(), text.lower())]
                    passed = len(matched) >= 1
                    detail = f'matched {len(matched)}/{len(required_patterns)} patterns' if passed else f'no patterns matched'
            checks.append({'name': fname, 'passed': passed, 'detail': detail})
        except Exception as e:
            checks.append({'name': fname, 'passed': False, 'detail': str(e)})

    try:
        hb = workspace / 'HEARTBEAT.md'
        passed = False
        detail = 'missing'
        if hb.exists():
            text, err = safe_read(hb)
            if text is None:
                detail = f'read error: {err}'
            else:
                # allow either empty/comment-only or a tiny checklist
                lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
                passed = len(lines) <= 20  # tiny checklist should be short
                detail = f'{len(lines)} non-comment lines'
        checks.append({'name': 'heartbeat_tiny_or_empty', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'heartbeat_tiny_or_empty', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed_n = sum(1 for c in checks if c['passed'])
    score = passed_n / total if total else 0.0
    result = {'passed': passed_n == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()