import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

# Check 1: summary exists
summary_path = workspace / 'context' / 'current-summary.md'
try:
    summary_text = summary_path.read_text(encoding='utf-8')
    add_check('summary_exists', True, 'context/current-summary.md is present')
except Exception as e:
    summary_text = ''
    add_check('summary_exists', False, f'Missing or unreadable summary: {e}')

# Check 2: pending tasks file exists
pending_path = workspace / 'context' / 'pending-tasks.md'
try:
    pending_text = pending_path.read_text(encoding='utf-8')
    add_check('pending_file_exists', True, 'context/pending-tasks.md is present')
except Exception as e:
    pending_text = ''
    add_check('pending_file_exists', False, f'Missing or unreadable pending tasks file: {e}')

# Check 3: summary mentions key planning thread and Itaú
try:
    s = summary_text.lower()
    ok = ('2026' in s or 'plano' in s) and ('itaú' in s or 'itau' in s)
    detail = 'Summary mentions 2026 planning and Itaú requirement' if ok else 'Summary missing 2026 planning thread or Itaú requirement'
    add_check('summary_mentions_core_topics', ok, detail)
except Exception as e:
    add_check('summary_mentions_core_topics', False, f'Failed to inspect summary: {e}')

# Check 4: summary contains recent-turns section with up to 4 items, not inventing obvious extra tasks
try:
    lines = [ln.strip() for ln in summary_text.splitlines() if ln.strip()]
    recent_idx = next((i for i, ln in enumerate(lines) if 'últimos turnos' in ln.lower() or 'last turns' in ln.lower()), None)
    if recent_idx is None:
        add_check('recent_turns_section', False, 'No Recent Turns/Últimos turnos section found')
    else:
        bullets = []
        for ln in lines[recent_idx + 1: recent_idx + 10]:
            if ln.startswith('-'):
                bullets.append(ln)
        ok = len(bullets) <= 4 and len(bullets) >= 1
        add_check('recent_turns_section', ok, f'Found {len(bullets)} bullet(s) in recent-turns section')
except Exception as e:
    add_check('recent_turns_section', False, f'Failed to inspect recent turns: {e}')

# Check 5: pending tasks file is focused on pending items, not a full copy of the summary
try:
    p = pending_text.lower()
    has_pending_hint = ('pending' in p or 'pend' in p or 'next' in p or 'próxim' in p or 'proxim' in p)
    too_long = len(pending_text.splitlines()) > 20
    ok = has_pending_hint and not too_long
    detail = 'Pending tasks file appears concise and task-focused' if ok else 'Pending tasks file missing pending cues or is too long'
    add_check('pending_tasks_focused', ok, detail)
except Exception as e:
    add_check('pending_tasks_focused', False, f'Failed to inspect pending file: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
