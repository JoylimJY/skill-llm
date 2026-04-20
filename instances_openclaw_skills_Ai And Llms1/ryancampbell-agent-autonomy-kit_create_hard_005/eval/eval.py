import json
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    q = (workspace / 'tasks' / 'QUEUE.md').read_text(encoding='utf-8')
    text = q.lower()
    has_ready = '## ready' in text and ('[ ]' in text)
    has_inprogress = '## in progress' in text
    has_blocked = '## blocked' in text
    has_done = '## done today' in text
    add_check('queue_sections', has_ready and has_inprogress and has_blocked and has_done, 'found required queue sections' if (has_ready and has_inprogress and has_blocked and has_done) else 'missing one or more required sections')
except Exception as e:
    add_check('queue_sections', False, f'read/parse failed: {e}')

try:
    q = (workspace / 'tasks' / 'QUEUE.md').read_text(encoding='utf-8')
    ready_lines = [ln.strip() for ln in q.splitlines() if re.search(r'^-\s*\[\s*\]\s*', ln)]
    completed_lines = [ln.strip() for ln in q.splitlines() if re.search(r'^-\s*\[x\]\s*', ln, re.I)]
    has_example_done = any('example marker task completed' in ln.lower() for ln in completed_lines)
    has_blocked_reason = 'ryan' in q.lower() or 'blocked' in q.lower()
    add_check('queue_content_balance', len(ready_lines) >= 1 and len(completed_lines) >= 1 and has_example_done and has_blocked_reason, f'ready={len(ready_lines)}, done={len(completed_lines)}, example_done={has_example_done}')
except Exception as e:
    add_check('queue_content_balance', False, f'read/parse failed: {e}')

try:
    hb = (workspace / 'HEARTBEAT.md').read_text(encoding='utf-8').lower()
    priorities = ['human', 'urgent', 'ready task', 'update status', 'daily memory']
    score_hits = sum(1 for p in priorities if p in hb)
    add_check('heartbeat_routine_quality', score_hits >= 4, f'matched {score_hits}/5 priority terms')
except Exception as e:
    add_check('heartbeat_routine_quality', False, f'read/parse failed: {e}')

try:
    mem = (workspace / 'memory' / '2025-05-01.md').read_text(encoding='utf-8').lower()
    marker_ok = 'autonomy-memory-01' in mem
    mentions_progress = 'completed' in mem and 'investigated' in mem
    add_check('daily_memory_marker', marker_ok and mentions_progress, f'marker_ok={marker_ok}, mentions_progress={mentions_progress}')
except Exception as e:
    add_check('daily_memory_marker', False, f'read/parse failed: {e}')

try:
    cron = (workspace / 'cron_plan.json').read_text(encoding='utf-8')
    data = json.loads(cron)
    jobs = data.get('jobs', []) if isinstance(data, dict) else []
    names = ' '.join(str(j.get('name', '')).lower() for j in jobs)
    has_daily = 'daily progress report' in names
    has_morning = 'morning kickoff' in names
    has_overnight = 'overnight work' in names
    add_check('cron_plan_jobs', len(jobs) >= 3 and has_daily and has_morning and has_overnight, f'jobs={len(jobs)}')
except Exception as e:
    add_check('cron_plan_jobs', False, f'read/parse failed: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks) and len(checks) > 0, 'score': score, 'checks': checks}
print(json.dumps(result))
