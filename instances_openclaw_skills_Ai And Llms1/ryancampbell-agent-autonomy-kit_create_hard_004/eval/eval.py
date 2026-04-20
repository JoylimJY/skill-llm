import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def read_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"Could not read {path.name}: {e}"


def norm(s):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()

# 1) Required files exist
required = [
    workspace / 'tasks' / 'QUEUE.md',
    workspace / 'HEARTBEAT.md',
    workspace / 'memory' / '2025-05-17.md',
    workspace / 'memory' / 'metrics.md',
]
all_exist = True
missing = []
for p in required:
    if not p.exists():
        all_exist = False
        missing.append(str(p.relative_to(workspace)))
add_check('required_files_exist', all_exist, 'Missing: ' + ', '.join(missing) if missing else 'All required files present')

# 2) Marker content appears in at least one output file
marker_ok = False
marker_detail = 'Marker not found'
try:
    texts = []
    for p in required:
        if p.exists():
            try:
                texts.append(p.read_text(encoding='utf-8'))
            except Exception:
                pass
    joined = '\n'.join(texts)
    marker_ok = 'autonomy-seed-7' in joined.lower()
    marker_detail = 'Marker AUTONOMY-SEED-7 found' if marker_ok else 'Marker AUTONOMY-SEED-7 missing'
except Exception as e:
    marker_detail = f'Error while searching marker: {e}'
add_check('marker_present', marker_ok, marker_detail)

# 3) Queue structure and content
queue_path = workspace / 'tasks' / 'QUEUE.md'
queue_ok = False
queue_detail = ''
try:
    if queue_path.exists():
        text = queue_path.read_text(encoding='utf-8')
        ntext = norm(text)
        sections = [norm('Ready'), norm('In Progress'), norm('Blocked'), norm('Done Today')]
        has_sections = all(s in ntext for s in sections)
        has_agent = 'kai' in ntext and 'in progress' in ntext
        has_followup = ('follow up' in ntext or 'follow-up' in ntext) and ('metrics' in ntext or 'daily metrics' in ntext)
        has_task_checkbox = '- [ ]' in text or '* [ ]' in text
        queue_ok = has_sections and has_agent and has_followup and has_task_checkbox
        queue_detail = f'sections={has_sections}, agent={has_agent}, followup={has_followup}, checkbox={has_task_checkbox}'
    else:
        queue_detail = 'QUEUE.md missing'
except Exception as e:
    queue_detail = f'Error checking queue: {e}'
add_check('queue_content', queue_ok, queue_detail)

# 4) Heartbeat content
heartbeat_ok = False
heartbeat_detail = ''
try:
    p = workspace / 'HEARTBEAT.md'
    if p.exists():
        text = p.read_text(encoding='utf-8')
        ntext = norm(text)
        required_phrases = ['quick checks', 'work mode', 'task queue', 'log progress']
        has_phrases = all(norm(phrase) in ntext for phrase in required_phrases)
        proactive = ('do meaningful work' in ntext) or ('pick the highest priority' in ntext) or ('pull from task queue' in ntext)
        heartbeat_ok = has_phrases and proactive
        heartbeat_detail = f'phrases={has_phrases}, proactive={proactive}'
    else:
        heartbeat_detail = 'HEARTBEAT.md missing'
except Exception as e:
    heartbeat_detail = f'Error checking heartbeat: {e}'
add_check('heartbeat_content', heartbeat_ok, heartbeat_detail)

# 5) Memory report consistency
memory_ok = False
memory_detail = ''
try:
    p = workspace / 'memory' / '2025-05-17.md'
    if p.exists():
        text = p.read_text(encoding='utf-8')
        ntext = norm(text)
        has_completed = any(norm(item) in ntext for item in [
            'Reviewed heartbeat flow for proactive work',
            'Shipped initial queue scaffolding',
        ])
        has_in_progress = 'handoff' in ntext or 'in progress' in ntext
        has_blocked = 'blocked' in ntext
        memory_ok = has_completed and has_in_progress and has_blocked
        memory_detail = f'completed={has_completed}, in_progress={has_in_progress}, blocked={has_blocked}'
    else:
        memory_detail = 'Daily memory file missing'
except Exception as e:
    memory_detail = f'Error checking memory: {e}'
add_check('daily_memory_content', memory_ok, memory_detail)

# 6) Metrics summary exists and is operationally themed
metrics_ok = False
metrics_detail = ''
try:
    p = workspace / 'memory' / 'metrics.md'
    if p.exists():
        text = p.read_text(encoding='utf-8')
        ntext = norm(text)
        has_header = 'autonomy metrics' in ntext or 'metrics' in ntext
        has_numbers = bool(re.search(r'\b\d+\b', text)) or 'x' in ntext or 'y' in ntext or 'z' in ntext
        has_patterns = 'patterns' in ntext or 'this week' in ntext
        metrics_ok = has_header and has_numbers and has_patterns
        metrics_detail = f'header={has_header}, numbers={has_numbers}, patterns={has_patterns}'
    else:
        metrics_detail = 'metrics.md missing'
except Exception as e:
    metrics_detail = f'Error checking metrics: {e}'
add_check('metrics_summary', metrics_ok, metrics_detail)

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {
    'passed': passed_count == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result, ensure_ascii=False))
