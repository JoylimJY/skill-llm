import json
import os
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def run_router(text, context_chars=0):
    try:
        cmd = [sys.executable, str(workspace / 'skills' / 'arya-model-router' / 'router.py'), '--text', text, '--context-chars', str(context_chars)]
        p = subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True, timeout=20)
        stdout = (p.stdout or '').strip()
        data = json.loads(stdout) if stdout else None
        return True, data, stdout, (p.stderr or '').strip(), p.returncode
    except Exception as e:
        return False, None, '', f'{type(e).__name__}: {e}', None

# Check 1: files exist
try:
    rules_ok = (workspace / 'skills' / 'arya-model-router' / 'rules.json').exists()
    state_ok = (workspace / 'skills' / 'arya-model-router' / 'state.json').exists()
    router_ok = (workspace / 'skills' / 'arya-model-router' / 'router.py').exists()
    brief_ok = (workspace / 'skills' / 'arya-model-router' / 'brief.py').exists() or True
    add_check('required_files', rules_ok and state_ok and router_ok and brief_ok, f'rules={rules_ok}, state={state_ok}, router={router_ok}')
except Exception as e:
    add_check('required_files', False, f'exception: {type(e).__name__}: {e}')

# Check 2: cheap routing on light text
ok, data, out, err, code = run_router('MARKER-CHEAP hello quick question')
try:
    passed = ok and isinstance(data, dict) and data.get('level') in ('cheap', 'default') and 'response_policy' in data
    add_check('light_routing', passed, f'level={None if not isinstance(data, dict) else data.get("level")}, stdout={out[:200]}, stderr={err[:120]}')
except Exception as e:
    add_check('light_routing', False, f'exception: {type(e).__name__}: {e}')

# Check 3: daily report stays default-ish and structured
ok, data, out, err, code = run_router('MARKER-DAILY daily report today blockers summary')
try:
    passed = ok and isinstance(data, dict) and data.get('level') == 'default' and ('daily_report_mode' in (data.get('actions') or []))
    add_check('daily_report_mode', passed, f'level={None if not isinstance(data, dict) else data.get("level")}, actions={None if not isinstance(data, dict) else data.get("actions")}, stdout={out[:200]}')
except Exception as e:
    add_check('daily_report_mode', False, f'exception: {type(e).__name__}: {e}')

# Check 4: heavy text escalates to pro and requests subagent or brief_first for large context
ok, data, out, err, code = run_router('MARKER-HEAVY refactor optimize benchmark debug traceback migrate ' + ('x' * 6000), context_chars=65000)
try:
    actions = data.get('actions') if isinstance(data, dict) else []
    passed = ok and isinstance(data, dict) and data.get('level') in ('pro', 'ultra') and ('use_subagent' in actions) and ('brief_first' in actions)
    add_check('heavy_escalation', passed, f'level={None if not isinstance(data, dict) else data.get("level")}, actions={actions}, stdout={out[:220]}')
except Exception as e:
    add_check('heavy_escalation', False, f'exception: {type(e).__name__}: {e}')

# Check 5: explicit ultra override is honored
ok, data, out, err, code = run_router('MARKER-ULTRA @ultra please handle this')
try:
    passed = ok and isinstance(data, dict) and data.get('level') == 'ultra' and data.get('model') is not None
    add_check('ultra_override', passed, f'level={None if not isinstance(data, dict) else data.get("level")}, model={None if not isinstance(data, dict) else data.get("model")}, stdout={out[:200]}')
except Exception as e:
    add_check('ultra_override', False, f'exception: {type(e).__name__}: {e}')

# Check 6: output JSON schema has exact required top-level keys subset and no crash
try:
    ok, data, out, err, code = run_router('router status')
    schema_keys = set(data.keys()) if isinstance(data, dict) else set()
    required = {'mode', 'level', 'model', 'score', 'reasons', 'actions', 'response_policy'}
    passed = ok and isinstance(data, dict) and required.issubset(schema_keys)
    add_check('json_schema', passed, f'keys={sorted(schema_keys)[:20]}, stdout={out[:180]}')
except Exception as e:
    add_check('json_schema', False, f'exception: {type(e).__name__}: {e}')

score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
passed = all(c['passed'] for c in checks)
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
