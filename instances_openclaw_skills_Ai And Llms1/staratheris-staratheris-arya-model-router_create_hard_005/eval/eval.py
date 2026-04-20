import json
import os
import re
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def run_py(cmd, input_text=None):
    try:
        proc = subprocess.run(
            [sys.executable] + cmd,
            input=(input_text.encode('utf-8') if input_text is not None else None),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(workspace),
            timeout=20,
            check=False,
        )
        return proc.returncode, proc.stdout.decode('utf-8', errors='replace'), proc.stderr.decode('utf-8', errors='replace')
    except Exception as e:
        return 999, "", str(e)

# Check 1: brief.py exists and is runnable
brief_path = workspace / 'skills' / 'arya-model-router' / 'brief.py'
exists = False
try:
    exists = brief_path.is_file()
except Exception as e:
    add_check('brief_exists', False, f'error checking file existence: {e}')
else:
    add_check('brief_exists', exists, 'brief.py present' if exists else 'brief.py missing')

# Check 2: brief output contains required fields and marker preservation
brief_ok = False
brief_detail = 'not tested'
try:
    if exists:
        sample = (workspace / 'sample_context.txt').read_text(encoding='utf-8')
        code, out, err = run_py(['skills/arya-model-router/brief.py', '--max-chars', '4000'], input_text=sample)
        try:
            data = json.loads(out)
            summary = str(data.get('summary', ''))
            top_terms = data.get('top_terms', [])
            approx_chars = data.get('approx_chars', None)
            source_hint = str(data.get('source_hint', ''))
            markers = ' '.join([summary, json.dumps(top_terms, ensure_ascii=False), source_hint]).lower()
            has_markers = all(k.lower() in markers for k in ['marker_alpha', 'marker_beta', 'marker_gamma', 'daily_report'])
            brief_ok = (
                isinstance(data, dict)
                and isinstance(summary, str) and len(summary.strip()) > 20
                and isinstance(top_terms, list) and len(top_terms) >= 3
                and isinstance(approx_chars, int) and approx_chars > 0
                and isinstance(source_hint, str) and len(source_hint.strip()) > 0
                and has_markers
            )
            brief_detail = f'code={code}, summary_len={len(summary)}, top_terms={top_terms[:5]}, approx_chars={approx_chars}, stderr={err[-200:] if err else ""}'
        except Exception as e:
            brief_detail = f'brief output malformed: {e}; raw={out[:300]!r}; stderr={err[-200:]}'
except Exception as e:
    brief_detail = f'brief execution error: {e}'
add_check('brief_json_and_markers', brief_ok, brief_detail)

# Check 3: router returns valid JSON and helper path exists in output
router_ok = False
router_detail = 'not tested'
try:
    router_input = '@pro analyze this large daily report with MARKER_ALPHA and MARKER_BETA and MARKER_GAMMA to brief_first if needed '
    router_input *= 5
    code, out, err = run_py(['skills/arya-model-router/router.py', '--text', router_input, '--context-chars', '65000'])
    try:
        data = json.loads(out)
        helper = str(data.get('helper_scripts', {}).get('brief', ''))
        helper_path = workspace / helper.split('--max-chars')[0].strip().split()[-1] if helper else None
        router_ok = (
            isinstance(data, dict)
            and data.get('mode') in ('auto', 'off')
            and data.get('level') in ('cheap', 'default', 'pro', 'ultra')
            and isinstance(data.get('actions', []), list)
            and helper and 'brief.py' in helper
            and helper_path is not None and helper_path.is_file()
        )
        router_detail = f'level={data.get("level")}, actions={data.get("actions")}, helper={helper}, stderr={err[-200:] if err else ""}'
    except Exception as e:
        router_detail = f'router output malformed: {e}; raw={out[:300]!r}; stderr={err[-200:]}'
except Exception as e:
    router_detail = f'router execution error: {e}'
add_check('router_json_and_helper_path', router_ok, router_detail)

# Check 4: manual override and daily report detection behavior
behavior_ok = False
behavior_detail = 'not tested'
try:
    code1, out1, err1 = run_py(['skills/arya-model-router/router.py', '--text', '@cheap please keep this short DAILY_REPORT'], input_text=None)
    code2, out2, err2 = run_py(['skills/arya-model-router/router.py', '--text', 'router feedback expensive'])
    code3, out3, err3 = run_py(['skills/arya-model-router/router.py', '--text', 'router status'])
    try:
        d1 = json.loads(out1)
        d2 = json.loads(out2)
        d3 = json.loads(out3)
        override_ok = d1.get('level') == 'cheap' and 'override:tag' in ' '.join(d1.get('actions', []))
        feedback_ok = bool(d2.get('ok', False))
        status_ok = isinstance(d3, dict) and 'mode' in d3
        behavior_ok = override_ok and feedback_ok and status_ok
        behavior_detail = f'override={d1.get("level")}/{d1.get("actions")}, feedback={d2}, status_keys={list(d3.keys()) if isinstance(d3, dict) else None}'
    except Exception as e:
        behavior_detail = f'behavior outputs malformed: {e}; out1={out1[:200]!r}; out2={out2[:200]!r}; out3={out3[:200]!r}'
except Exception as e:
    behavior_detail = f'behavior execution error: {e}'
add_check('override_feedback_status_behavior', behavior_ok, behavior_detail)

# Check 5: expected output files are present after generation and include markers
files_ok = False
files_detail = 'not tested'
try:
    marker = workspace / 'marker_input.txt'
    sample = workspace / 'sample_context.txt'
    rules = workspace / 'skills' / 'arya-model-router' / 'rules.json'
    state = workspace / 'skills' / 'arya-model-router' / 'state.json'
    files_ok = all(p.is_file() for p in [marker, sample, rules, state])
    if files_ok:
        text = marker.read_text(encoding='utf-8') + '\n' + sample.read_text(encoding='utf-8')
        files_ok = all(x in text for x in ['MARKER_ALPHA', 'MARKER_BETA', 'MARKER_GAMMA', 'DAILY_REPORT'])
    files_detail = f'files_present={files_ok}'
except Exception as e:
    files_detail = f'file check error: {e}'
add_check('generated_inputs_and_markers', files_ok, files_detail)

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
