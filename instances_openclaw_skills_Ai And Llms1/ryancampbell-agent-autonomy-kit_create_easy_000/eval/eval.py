import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()
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
    queue_path = workspace / 'tasks' / 'QUEUE.md'

    try:
        if queue_path.exists():
            text, err = safe_read(queue_path)
            if text is None:
                checks.append({'name': 'queue file readable', 'passed': False, 'detail': f'Could not read tasks/QUEUE.md: {err}'})
            else:
                checks.append({'name': 'queue file exists', 'passed': True, 'detail': 'tasks/QUEUE.md exists'})

                n = norm(text)
                has_ready = 'ready' in n
                has_in_progress = 'in progress' in n or 'inprogress' in n
                has_blocked = 'blocked' in n
                has_done = 'done today' in n or 'done' in n
                checks.append({'name': 'queue sections present', 'passed': all([has_ready, has_in_progress, has_blocked, has_done]), 'detail': 'Looked for Ready, In Progress, Blocked, and Done Today sections'})

                marker_ok = 'marker queue 001' in n
                checks.append({'name': 'starter task marker present', 'passed': marker_ok, 'detail': 'Looked for marker content MARKER-QUEUE-001 in a normalized form'})

                ready_task_like = bool(re.search(r'\-\s*\[\s*\]\s*.*review.*autonomy.*improvement', text, re.I | re.S))
                checks.append({'name': 'starter task content', 'passed': ready_task_like, 'detail': 'Looked for a Ready task about reviewing the autonomy setup and identifying one quick improvement'})
        else:
            checks.append({'name': 'queue file exists', 'passed': False, 'detail': 'tasks/QUEUE.md is missing'})
            checks.append({'name': 'queue file readable', 'passed': False, 'detail': 'tasks/QUEUE.md cannot be read because it does not exist'})
            checks.append({'name': 'queue sections present', 'passed': False, 'detail': 'Cannot verify sections because file is missing'})
            checks.append({'name': 'starter task marker present', 'passed': False, 'detail': 'Cannot verify marker because file is missing'})
            checks.append({'name': 'starter task content', 'passed': False, 'detail': 'Cannot verify starter task because file is missing'})
    except Exception as e:
        checks.append({'name': 'evaluation error handling', 'passed': False, 'detail': f'Unexpected evaluator error: {e}'})

    total = len(checks) if checks else 1
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total
    passed = passed_count == total
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()
