import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"Could not read {path.name}: {e}"

try:
    queue_path = workspace / 'tasks' / 'QUEUE.md'
    heartbeat_path = workspace / 'HEARTBEAT.md'
    memory_path = workspace / 'memory' / '2025-05-15.md'

    try:
        queue_text = queue_path.read_text(encoding='utf-8')
        ready_ok = bool(re.search(r'(?is)##\s*Ready.*?-\s*\[\s*\]\s*Review\s+team\s+handoff\s+notes', queue_text)) or ('ready' in queue_text.lower() and 'review team handoff notes' in queue_text.lower())
        add_check('queue_exists_and_has_ready_task', queue_path.exists() and ready_ok, 'Queue file exists and contains a plausible Ready task.' if queue_path.exists() and ready_ok else 'Queue file missing or Ready task not detected.')
    except Exception as e:
        add_check('queue_exists_and_has_ready_task', False, f'Failed to inspect queue: {e}')

    try:
        hb_text = heartbeat_path.read_text(encoding='utf-8')
        hb_ok = ('work mode' in hb_text.lower()) and ('tasks/queue.md' in hb_text.lower()) and ('memory/2025-05-15.md' in hb_text.lower())
        add_check('heartbeat_is_proactive', heartbeat_path.exists() and hb_ok, 'Heartbeat mentions work mode, queue, and memory logging.' if heartbeat_path.exists() and hb_ok else 'Heartbeat missing or not proactive enough.')
    except Exception as e:
        add_check('heartbeat_is_proactive', False, f'Failed to inspect heartbeat: {e}')

    try:
        mem_text = memory_path.read_text(encoding='utf-8')
        marker_ok = 'autonomy demo ready' in mem_text.lower()
        next_ok = ('next' in mem_text.lower()) and ('blocked' in mem_text.lower() or 'queue' in mem_text.lower())
        add_check('daily_memory_contains_marker_and_next_steps', memory_path.exists() and marker_ok and next_ok, 'Memory note includes marker phrase and next steps.' if memory_path.exists() and marker_ok and next_ok else 'Memory note missing marker phrase or next steps.')
    except Exception as e:
        add_check('daily_memory_contains_marker_and_next_steps', False, f'Failed to inspect memory note: {e}')

    try:
        sk_path = workspace / 'SKILL.md'
        sk_text = sk_path.read_text(encoding='utf-8') if sk_path.exists() else ''
        skill_ok = 'agent-autonomy-kit' in sk_text.lower()
        add_check('skill_file_present', sk_path.exists() and skill_ok, 'SKILL.md is present and looks like the target skill.' if sk_path.exists() and skill_ok else 'SKILL.md missing or unexpected.')
    except Exception as e:
        add_check('skill_file_present', False, f'Failed to inspect SKILL.md: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total_count = len(checks)
    score = (passed_count / total_count) if total_count else 0.0
    result = {"passed": passed_count == total_count, "score": score, "checks": checks}
    print(json.dumps(result))
except Exception as e:
    fallback_checks = [{"name": "eval_exception", "passed": False, "detail": f"Unexpected eval failure: {e}"}]
    print(json.dumps({"passed": False, "score": 0.0, "checks": fallback_checks}))
