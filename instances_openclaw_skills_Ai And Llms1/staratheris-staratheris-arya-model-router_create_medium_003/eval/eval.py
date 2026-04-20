import json
import os
import re
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def run_router(text, context_chars=0):
    try:
        cmd = [sys.executable, str(workspace / 'router.py'), '--text', text, '--context-chars', str(context_chars)]
        p = subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True, timeout=20)
        out = (p.stdout or '').strip()
        try:
            data = json.loads(out)
            return True, data, out, p.returncode
        except Exception as e:
            return False, None, f'json parse error: {e}; raw={out[:300]}', p.returncode
    except Exception as e:
        return False, None, f'subprocess error: {e}', -1

# 1) input files with markers
try:
    normal = (workspace / 'input_normal.txt').read_text(encoding='utf-8')
    daily = (workspace / 'input_daily.txt').read_text(encoding='utf-8')
    heavy = (workspace / 'input_heavy.txt').read_text(encoding='utf-8')
    feedback = (workspace / 'input_feedback.txt').read_text(encoding='utf-8')
    markers_ok = all(m in normal + daily + heavy + feedback for m in ['MARKER_NORMAL', 'MARKER_DAILY', 'MARKER_HEAVY', 'MARKER_FEEDBACK'])
    add_check('marker_inputs_exist', markers_ok, 'All marker files present and readable.' if markers_ok else 'One or more marker files missing marker content.')
except Exception as e:
    add_check('marker_inputs_exist', False, f'Could not read generated marker files: {e}')

# 2) router report command
ok, data, detail, rc = run_router('router report')
if ok and isinstance(data, dict):
    has_mode = isinstance(data.get('mode'), str)
    has_last = 'lastDecision' in data
    has_feedback = 'feedback' in data and isinstance(data.get('feedback'), dict)
    add_check('router_report_json', has_mode and has_last and has_feedback, f'rc={rc}, keys={list(data.keys())}')
else:
    add_check('router_report_json', False, detail)

# 3) daily report should stay default unless clearly heavy
ok, data, detail, rc = run_router(daily, 0)
if ok and isinstance(data, dict):
    level = str(data.get('level', '')).lower()
    reasons = ' '.join([str(x) for x in data.get('reasons', [])]).lower()
    passed = (level == 'default') and ('daily' in reasons or 'reporte' in reasons or 'report' in reasons)
    add_check('daily_report_default', passed, f'level={level}, reasons={data.get("reasons")}, rc={rc}')
else:
    add_check('daily_report_default', False, detail)

# 4) heavy prompt with large context should suggest brief_first and use_subagent or pro
ok, data, detail, rc = run_router(heavy, 65000)
if ok and isinstance(data, dict):
    actions = [str(x) for x in data.get('actions', [])]
    reasons = ' '.join([str(x) for x in data.get('reasons', [])]).lower()
    level = str(data.get('level', '')).lower()
    passed = ('brief_first' in actions) and ('use_subagent' in actions) and (level in ('pro', 'ultra'))
    add_check('heavy_context_brief_first', passed, f'level={level}, actions={actions}, reasons={data.get("reasons")}, rc={rc}')
else:
    add_check('heavy_context_brief_first', False, detail)

# 5) feedback command should increase expensive counter
try:
    before_ok, before_data, before_detail, _ = run_router('router report')
    before_fb = int((before_data or {}).get('feedback', {}).get('too_expensive', -1)) if before_ok else -1
    fb_ok, fb_data, fb_detail, _ = run_router('router feedback expensive')
    after_ok, after_data, after_detail, _ = run_router('router report')
    after_fb = int((after_data or {}).get('feedback', {}).get('too_expensive', -1)) if after_ok else -1
    passed = after_fb >= before_fb + 1
    add_check('feedback_expensive_counter', passed, f'before={before_fb}, after={after_fb}, fb_ok={fb_ok}')
except Exception as e:
    add_check('feedback_expensive_counter', False, f'Error testing feedback: {e}')

# 6) output schema should be stable
ok, data, detail, rc = run_router('hello quick summary')
if ok and isinstance(data, dict):
    top_keys = set(data.keys())
    required = {'mode', 'level', 'model', 'score', 'reasons', 'actions', 'response_policy'}
    passed = required.issubset(top_keys)
    add_check('stable_output_schema', passed, f'keys={sorted(top_keys)}')
else:
    add_check('stable_output_schema', False, detail)

score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
passed = all(c['passed'] for c in checks)
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
