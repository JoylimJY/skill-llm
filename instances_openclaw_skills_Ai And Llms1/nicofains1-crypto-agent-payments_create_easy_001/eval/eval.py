import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    output_path = workspace / 'output.txt'
    if not output_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
    else:
        try:
            text = output_path.read_text(encoding='utf-8', errors='replace')
            norm = re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
            has_marker = 'alpha 7x' in norm
            has_chain = 'base' in norm
            has_task = 'onlyswaps 001' in norm or 'task id onlyswaps 001' in norm
            add_check('mentions_marker', has_marker, 'expected marker ALPHA-7X to be mentioned')
            add_check('mentions_chain', has_chain, 'expected Base to be mentioned')
            add_check('mentions_task_id', has_task, 'expected onlyswaps-001 to be mentioned')
        except Exception as e:
            add_check('output_readable', False, f'could not read output.txt: {e}')

    try:
        config_path = workspace / 'task_config.json'
        notes_path = workspace / 'notes.txt'
        cfg_ok = False
        notes_ok = False
        if config_path.exists():
            try:
                cfg = json.loads(config_path.read_text(encoding='utf-8', errors='replace'))
                cfg_ok = all(k in cfg for k in ['task_id', 'chain', 'marker'])
                add_check('config_marker_present', cfg_ok and cfg.get('marker', '').lower() == 'alpha-7x'.lower(), 'task_config.json contains the expected marker')
            except Exception as e:
                add_check('config_parse', False, f'could not parse task_config.json: {e}')
        else:
            add_check('config_present', False, 'task_config.json is missing')

        if notes_path.exists():
            try:
                notes = notes_path.read_text(encoding='utf-8', errors='replace').lower()
                notes_ok = ('alpha-7x'.lower() in notes) and ('base' in notes) and ('onlyswaps-001' in notes)
                add_check('notes_marker_present', notes_ok, 'notes.txt contains marker, chain, and task id')
            except Exception as e:
                add_check('notes_read', False, f'could not read notes.txt: {e}')
        else:
            add_check('notes_present', False, 'notes.txt is missing')
    except Exception as e:
        add_check('input_checks', False, f'unexpected error while checking inputs: {e}')

except Exception as e:
    add_check('fatal', False, f'unexpected evaluator error: {e}')

score = 0.0
try:
    score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
except Exception:
    score = 0.0

passed = all(c['passed'] for c in checks) if checks else False
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
