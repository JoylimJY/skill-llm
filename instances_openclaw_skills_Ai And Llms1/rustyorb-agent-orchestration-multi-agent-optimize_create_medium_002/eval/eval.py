import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    summary_path = workspace / 'summary.txt'
    plan_path = workspace / 'allocation_plan.json'
    note_path = workspace / 'validation_note.txt'

    if summary_path.exists():
        try:
            summary = summary_path.read_text(encoding='utf-8', errors='ignore')
            text = re.sub(r'\s+', ' ', summary.lower())
            passed = ('latency' in text or 'token' in text) and ('agent' in text) and ('baseline' in text or 'before' in text)
            add_check('summary_present_and_relevant', passed, 'summary.txt found and checked for orchestration/performance language')
        except Exception as e:
            add_check('summary_present_and_relevant', False, f'could not read summary.txt: {e}')
    else:
        add_check('summary_present_and_relevant', False, 'summary.txt is missing')

    if plan_path.exists():
        try:
            data = json.loads(plan_path.read_text(encoding='utf-8', errors='ignore'))
            items = data.get('assignments', []) if isinstance(data, dict) else []
            has_three = isinstance(items, list) and len(items) >= 3
            agents = []
            valid = True
            for item in items:
                if not isinstance(item, dict):
                    valid = False
                    continue
                agent = str(item.get('agent', '')).strip().lower()
                task = str(item.get('task', '')).strip().lower()
                agents.append(agent)
                if not agent or not task:
                    valid = False
            required_agents = {'db-agent', 'app-agent', 'frontend-agent'}
            covered = required_agents.issubset(set(agents))
            passed = has_three and valid and covered
            add_check('allocation_plan_structure', passed, f'assignments={len(items) if isinstance(items, list) else "invalid"}, covered_agents={sorted(set(agents))}')
        except Exception as e:
            add_check('allocation_plan_structure', False, f'could not parse allocation_plan.json: {e}')
    else:
        add_check('allocation_plan_structure', False, 'allocation_plan.json is missing')

    if note_path.exists():
        try:
            note = note_path.read_text(encoding='utf-8', errors='ignore')
            norm = re.sub(r'[^a-z0-9]+', ' ', note.lower()).strip()
            passed = ('validated' in norm or 'validation' in norm) and ('rollback' in norm or 'revert' in norm or 'retry' in norm)
            add_check('validation_note_present', passed, 'validation_note.txt found and checked for validation/rollback language')
        except Exception as e:
            add_check('validation_note_present', False, f'could not read validation_note.txt: {e}')
    else:
        add_check('validation_note_present', False, 'validation_note.txt is missing')

except Exception as e:
    add_check('fatal_eval_error', False, f'Unexpected evaluator error: {e}')

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": all(c['passed'] for c in checks) if checks else False, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
