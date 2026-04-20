from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

# Check 1: queue file exists
queue_path = workspace / 'tasks' / 'QUEUE.md'
try:
    exists = queue_path.exists()
    add_check('queue_exists', exists, 'found tasks/QUEUE.md' if exists else 'tasks/QUEUE.md is missing')
except Exception as e:
    add_check('queue_exists', False, f'error checking queue file: {e}')

# Check 2: heartbeat file exists
hb_path = workspace / 'HEARTBEAT.md'
try:
    exists = hb_path.exists()
    add_check('heartbeat_exists', exists, 'found HEARTBEAT.md' if exists else 'HEARTBEAT.md is missing')
except Exception as e:
    add_check('heartbeat_exists', False, f'error checking heartbeat file: {e}')

# Check 3: queue contains all required sections and marker-like content
try:
    text, err = safe_read(queue_path)
    if text is None:
        add_check('queue_content', False, f'could not read queue: {err}')
    else:
        lower = re.sub(r'\s+', ' ', text.lower())
        required_bits = ['ready', 'in progress', 'blocked', 'done today']
        found = sum(1 for bit in required_bits if bit in lower)
        has_marker_task = any(k in lower for k in ['onboarding checklist', 'autonomy overview', 'team update'])
        passed = found >= 4 and has_marker_task
        detail = f'found {found}/4 required sections; marker task present={has_marker_task}'
        add_check('queue_sections', passed, detail)
except Exception as e:
    add_check('queue_sections', False, f'error parsing queue: {e}')

# Check 4: heartbeat contains proactive instructions
try:
    text, err = safe_read(hb_path)
    if text is None:
        add_check('heartbeat_content', False, f'could not read heartbeat: {err}')
    else:
        lower = re.sub(r'\s+', ' ', text.lower())
        phrases = ['read `tasks/queue.md`', 'pick one ready task', 'do the work', 'log progress']
        matches = sum(1 for p in phrases if p in lower)
        passed = matches >= 3
        add_check('heartbeat_instructions', passed, f'found {matches}/4 proactive instruction phrases')
except Exception as e:
    add_check('heartbeat_instructions', False, f'error parsing heartbeat: {e}')

# Check 5: marker file exists and contains expected marker
marker_path = workspace / 'memory' / 'seed.json'
try:
    text, err = safe_read(marker_path)
    if text is None:
        add_check('marker_file', False, f'could not read marker file: {err}')
    else:
        try:
            data = json.loads(text)
            marker_ok = str(data.get('marker', '')).strip().lower() == 'autonomy_kit_demo'
            files_ok = isinstance(data.get('files'), list) and all(isinstance(x, str) for x in data.get('files', []))
            passed = marker_ok and files_ok
            add_check('marker_content', passed, f'marker_ok={marker_ok}, files_ok={files_ok}')
        except Exception as e:
            add_check('marker_content', False, f'invalid json in marker file: {e}')
except Exception as e:
    add_check('marker_content', False, f'error checking marker file: {e}')

passed_all = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": passed_all, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
