import json
import os
import subprocess
import sys
from pathlib import Path


def fuzzy_has(items, needle):
    try:
        n = ''.join(ch.lower() for ch in needle if ch.isalnum() or ch.isspace()).strip()
        for item in items:
            s = ''.join(ch.lower() for ch in str(item) if ch.isalnum() or ch.isspace()).strip()
            if n in s:
                return True
        return False
    except Exception:
        return False


def run_router(workspace, text, context_chars=0):
    try:
        proc = subprocess.run(
            [sys.executable, str(Path(workspace) / 'router.py'), '--text', text, '--context-chars', str(context_chars)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else '{}'
        return json.loads(out)
    except Exception as e:
        return {'_error': str(e)}


def main():
    ws = Path(sys.argv[1])
    checks = []

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # 1) Required files exist
    try:
        router_path = ws / 'router.py'
        rules_path = ws / 'rules.json'
        state_path = ws / 'state.json'
        add('required_files_exist', router_path.exists() and rules_path.exists() and state_path.exists(), f'router.py={router_path.exists()}, rules.json={rules_path.exists()}, state.json={state_path.exists()}')
    except Exception as e:
        add('required_files_exist', False, f'error: {e}')

    # 2) Cheap/default/pro decisions
    try:
        cheap = run_router(ws, 'Hi, thanks! Please give a brief response.')
        default = run_router(ws, 'Could you summarize this simple request with a balanced answer?')
        pro = run_router(ws, 'Please refactor and debug this architecture issue; investigate the failure and optimize the design.')
        ok = (
            str(cheap.get('level', '')).lower() == 'cheap' and
            str(default.get('level', '')).lower() == 'default' and
            str(pro.get('level', '')).lower() == 'pro'
        )
        add('tier_routing_basic', ok, f"cheap={cheap.get('level')} default={default.get('level')} pro={pro.get('level')}")
    except Exception as e:
        add('tier_routing_basic', False, f'error: {e}')

    # 3) Brief-first on large context with pro
    try:
        long_text = 'Please investigate and refactor the architecture. ' + ('A' * 14000)
        res = run_router(ws, long_text, context_chars=13050)
        actions = res.get('actions', []) if isinstance(res, dict) else []
        ok = str(res.get('level', '')).lower() == 'pro' and fuzzy_has(actions, 'brief_first') and fuzzy_has(actions, 'use_subagent')
        add('brief_first_behavior', ok, f"level={res.get('level')} actions={actions}")
    except Exception as e:
        add('brief_first_behavior', False, f'error: {e}')

    # 4) Daily report stays default and structured
    try:
        res = run_router(ws, 'Daily report: status report for the team. Keep it structured and concise.')
        actions = res.get('actions', []) if isinstance(res, dict) else []
        policy = res.get('response_policy', {}) if isinstance(res, dict) else {}
        ok = str(res.get('level', '')).lower() == 'default' and fuzzy_has(actions, 'daily_report_mode') and isinstance(policy, dict) and bool(policy)
        add('daily_report_mode', ok, f"level={res.get('level')} actions={actions} policy={policy}")
    except Exception as e:
        add('daily_report_mode', False, f'error: {e}')

    # 5) Tag override should force pro
    try:
        res = run_router(ws, '@pro Please answer this one with the stronger model.')
        actions = res.get('actions', []) if isinstance(res, dict) else []
        ok = str(res.get('level', '')).lower() == 'pro' and fuzzy_has(actions, 'override')
        add('tag_override', ok, f"level={res.get('level')} actions={actions}")
    except Exception as e:
        add('tag_override', False, f'error: {e}')

    # 6) Auto off forces cheap unless override
    try:
        subprocess.run([sys.executable, str(ws / 'router.py'), '--text', 'router auto off'], cwd=ws, capture_output=True, text=True, timeout=30)
        res = run_router(ws, 'Please refactor and debug this architecture issue; investigate the failure and optimize the design.')
        ok = str(res.get('level', '')).lower() == 'cheap' and fuzzy_has(res.get('actions', []), 'auto_off')
        add('auto_off_forces_cheap', ok, f"level={res.get('level')} actions={res.get('actions')}")
    except Exception as e:
        add('auto_off_forces_cheap', False, f'error: {e}')

    # 7) Feedback commands update state.json and are visible
    try:
        subprocess.run([sys.executable, str(ws / 'router.py'), '--text', 'router feedback expensive'], cwd=ws, capture_output=True, text=True, timeout=30)
        subprocess.run([sys.executable, str(ws / 'router.py'), '--text', 'router feedback weak'], cwd=ws, capture_output=True, text=True, timeout=30)
        data = {}
        try:
            data = json.loads((ws / 'state.json').read_text(encoding='utf-8'))
        except Exception:
            data = {}
        fb = data.get('feedback', {}) if isinstance(data, dict) else {}
        ok = int(fb.get('too_expensive', 0)) >= 1 and int(fb.get('too_weak', 0)) >= 1
        add('feedback_state_updates', ok, f'feedback={fb}')
    except Exception as e:
        add('feedback_state_updates', False, f'error: {e}')

    # Final scoring
    try:
        total = len(checks)
        passed = sum(1 for c in checks if c['passed'])
        score = passed / total if total else 0.0
        result = {'passed': passed == total, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
