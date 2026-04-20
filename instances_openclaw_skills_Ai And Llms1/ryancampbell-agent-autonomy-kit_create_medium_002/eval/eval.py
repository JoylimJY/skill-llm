import json
import os
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def fuzzy_contains(text: str, needle: str) -> bool:
    try:
        return norm(needle) in norm(text)
    except Exception:
        return False


def count_markers(text: str, marker: str) -> int:
    try:
        return len(re.findall(re.escape(marker), text, flags=re.IGNORECASE))
    except Exception:
        return 0

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

# Check 1: QUEUE.md exists and has required sections/tasks
try:
    queue_path = workspace / 'tasks' / 'QUEUE.md'
    if not queue_path.exists():
        checks.append({'name': 'queue_exists', 'passed': False, 'detail': 'tasks/QUEUE.md is missing'})
    else:
        queue_text, err = safe_read(queue_path)
        if queue_text is None:
            checks.append({'name': 'queue_exists', 'passed': False, 'detail': f'Could not read tasks/QUEUE.md: {err}'})
        else:
            ready = len(re.findall(r'^\s*[-*]\s*\[\s*\]\s*', queue_text, flags=re.MULTILINE))
            in_progress = fuzzy_contains(queue_text, 'In Progress')
            blocked = fuzzy_contains(queue_text, 'Blocked')
            done = fuzzy_contains(queue_text, 'Done Today')
            passed = ready >= 3 and in_progress and blocked and done
            detail = f'ready_items={ready}, in_progress={in_progress}, blocked={blocked}, done_today={done}'
            checks.append({'name': 'queue_structure', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'queue_structure', 'passed': False, 'detail': f'Unexpected error: {e}'})

# Check 2: HEARTBEAT.md exists and is proactive
try:
    hb_path = workspace / 'HEARTBEAT.md'
    if not hb_path.exists():
        checks.append({'name': 'heartbeat_exists', 'passed': False, 'detail': 'HEARTBEAT.md is missing'})
    else:
        hb_text, err = safe_read(hb_path)
        if hb_text is None:
            checks.append({'name': 'heartbeat_exists', 'passed': False, 'detail': f'Could not read HEARTBEAT.md: {err}'})
        else:
            must_have = [
                'task queue',
                'work mode',
                'pull from',
                'update queue',
                'log progress'
            ]
            hits = sum(1 for term in must_have if fuzzy_contains(hb_text, term))
            passed = hits >= 4
            checks.append({'name': 'heartbeat_content', 'passed': passed, 'detail': f'found_terms={hits}/{len(must_have)}'})
except Exception as e:
    checks.append({'name': 'heartbeat_content', 'passed': False, 'detail': f'Unexpected error: {e}'})

# Check 3: today memory note exists with marker/tomorrow plan
try:
    mem_dir = workspace / 'memory'
    candidates = []
    if mem_dir.exists():
        try:
            candidates = sorted([p for p in mem_dir.iterdir() if p.is_file()])
        except Exception:
            candidates = []
    target = None
    for p in candidates:
        txt, _ = safe_read(p)
        if txt and (fuzzy_contains(txt, 'tomorrow') or fuzzy_contains(txt, 'next heartbeat') or fuzzy_contains(txt, 'plan')):
            target = p
            break
    if target is None:
        checks.append({'name': 'memory_note', 'passed': False, 'detail': 'No memory note file with a next-step/tomorrow plan was found in memory/'})
    else:
        txt, err = safe_read(target)
        if txt is None:
            checks.append({'name': 'memory_note', 'passed': False, 'detail': f'Could not read {target.name}: {err}'})
        else:
            marker_ok = fuzzy_contains(txt, 'AUK-SEED-2025-05') or fuzzy_contains(txt, 'agent autonomy kit')
            next_ok = fuzzy_contains(txt, 'next') or fuzzy_contains(txt, 'tomorrow') or fuzzy_contains(txt, 'heartbeat')
            checks.append({'name': 'memory_note', 'passed': marker_ok and next_ok, 'detail': f'file={target.name}, marker_ok={marker_ok}, next_step_ok={next_ok}'})
except Exception as e:
    checks.append({'name': 'memory_note', 'passed': False, 'detail': f'Unexpected error: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
total = len(checks) if checks else 1
result = {
    'passed': passed_count == total,
    'score': passed_count / total,
    'checks': checks,
}
print(json.dumps(result))
