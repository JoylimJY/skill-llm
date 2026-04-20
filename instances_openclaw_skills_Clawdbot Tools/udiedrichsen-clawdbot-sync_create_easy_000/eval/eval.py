import json
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

# Check 1: peers.json exists and contains expected peer marker
try:
    peers_path = workspace / 'memory' / 'clawdbot-sync' / 'peers.json'
    if not peers_path.exists():
        add_check('peers_file_exists', False, f'missing: {peers_path}')
    else:
        data = json.loads(peers_path.read_text(encoding='utf-8'))
        text = json.dumps(data).lower()
        ok = 'lab-peer' in text and '100.64.10.25' in text and 'clawdbot' in text and '/home/clawdbot/clawd' in text
        add_check('peers_content', ok, 'found expected peer fields' if ok else f'unexpected content: {text[:200]}')
except Exception as e:
    add_check('peers_content', False, f'error reading/parsing peers.json: {e}')

# Check 2: marker content preserved in generated inputs
try:
    marker_path = workspace / 'README_TASK.txt'
    if not marker_path.exists():
        add_check('task_marker_exists', False, f'missing: {marker_path}')
    else:
        txt = marker_path.read_text(encoding='utf-8')
        ok = 'read_me_task_delta_11'.lower() in txt.lower().replace('-', '_')
        add_check('task_marker_exists', ok, 'marker present' if ok else f'content: {txt[:200]}')
except Exception as e:
    add_check('task_marker_exists', False, f'error reading task marker: {e}')

# Check 3: config.json exists and has expected conflict mode
try:
    cfg_path = workspace / 'memory' / 'clawdbot-sync' / 'config.json'
    if not cfg_path.exists():
        add_check('config_file_exists', False, f'missing: {cfg_path}')
    else:
        data = json.loads(cfg_path.read_text(encoding='utf-8'))
        conflict_mode = str(data.get('conflict_mode', '')).lower().replace(' ', '-')
        ok = 'newest-wins' in conflict_mode
        add_check('config_conflict_mode', ok, f'conflict_mode={data.get("conflict_mode")!r}')
except Exception as e:
    add_check('config_conflict_mode', False, f'error reading/parsing config.json: {e}')

# Check 4: history.json exists and is valid JSON
try:
    hist_path = workspace / 'memory' / 'clawdbot-sync' / 'history.json'
    if not hist_path.exists():
        add_check('history_file_exists', False, f'missing: {hist_path}')
    else:
        data = json.loads(hist_path.read_text(encoding='utf-8'))
        ok = isinstance(data.get('events'), list)
        add_check('history_valid_structure', ok, 'events list present' if ok else f'bad structure: {data}')
except Exception as e:
    add_check('history_valid_structure', False, f'error reading/parsing history.json: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
