import json
import os
import sys
from pathlib import Path


def normalize_text(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def load_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def check_decision(workspace, filename, expected_level=None, expected_mode=None, expected_actions=None, expected_contains=None, expected_model_substr=None, expected_policy_style=None, expect_brief=False):
    checks = []
    passed = True
    p = Path(workspace) / filename
    data, err = load_json_file(p)
    if err:
        return False, checks + [{"name": f"load {filename}", "passed": False, "detail": f"failed to load JSON: {err}"}]
    # file exists
    checks.append({"name": f"file exists {filename}", "passed": True, "detail": "output file present"})
    # level
    if expected_level is not None:
        ok = isinstance(data, dict) and normalize_text(data.get('level')) == normalize_text(expected_level)
        checks.append({"name": f"level {filename}", "passed": ok, "detail": f"level={data.get('level')} expected~{expected_level}"})
        passed = passed and ok
    if expected_mode is not None:
        ok = isinstance(data, dict) and normalize_text(data.get('mode')) == normalize_text(expected_mode)
        checks.append({"name": f"mode {filename}", "passed": ok, "detail": f"mode={data.get('mode')} expected~{expected_mode}"})
        passed = passed and ok
    if expected_actions is not None:
        actions = data.get('actions') if isinstance(data, dict) else None
        ok = isinstance(actions, list)
        if ok:
            norm_actions = [normalize_text(a) for a in actions]
            ok = all(any(normalize_text(e) in a for a in norm_actions) for e in expected_actions)
        checks.append({"name": f"actions {filename}", "passed": ok, "detail": f"actions={actions}"})
        passed = passed and ok
    if expected_contains is not None:
        reasons = data.get('reasons') if isinstance(data, dict) else None
        joined = normalize_text(reasons)
        ok = all(normalize_text(x) in joined for x in expected_contains)
        checks.append({"name": f"reasons {filename}", "passed": ok, "detail": f"reasons={reasons}"})
        passed = passed and ok
    if expected_model_substr is not None:
        model = data.get('model') if isinstance(data, dict) else None
        ok = normalize_text(expected_model_substr) in normalize_text(model)
        checks.append({"name": f"model {filename}", "passed": ok, "detail": f"model={model}"})
        passed = passed and ok
    if expected_policy_style is not None:
        policy = data.get('response_policy') if isinstance(data, dict) else None
        style = policy.get('style') if isinstance(policy, dict) else None
        ok = normalize_text(style) == normalize_text(expected_policy_style)
        checks.append({"name": f"policy {filename}", "passed": ok, "detail": f"style={style}"})
        passed = passed and ok
    if expect_brief:
        actions = data.get('actions') if isinstance(data, dict) else []
        ok = isinstance(actions, list) and any(normalize_text('brief_first') == normalize_text(a) for a in actions)
        checks.append({"name": f"brief_first {filename}", "passed": ok, "detail": f"actions={actions}"})
        passed = passed and ok
    return passed, checks


def main():
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Required outputs
    out1 = ws / 'out_cheap.json'
    out2 = ws / 'out_default.json'
    out3 = ws / 'out_pro.json'
    out4 = ws / 'out_override.json'
    out5 = ws / 'out_auto_off.json'
    out6 = ws / 'out_brief.json'
    out7 = ws / 'out_daily.json'

    all_passed = True

    scenarios = [
        ('out_cheap.json', 'cheap', 'auto', ['stay_main'], ['hello'], 'brief'),
        ('out_default.json', 'default', 'auto', ['stay_main'], ['status', 'update'], 'concise'),
        ('out_pro.json', 'pro', 'auto', ['use_subagent'], ['refactor', 'optimize'], 'detailed'),
        ('out_override.json', 'pro', 'auto', ['override'], ['override'], 'detailed'),
        ('out_auto_off.json', 'cheap', 'off', ['auto_off'], ['router auto off'], 'brief'),
        ('out_brief.json', 'pro', 'auto', ['use_subagent', 'brief_first'], ['contexto', 'brief'], 'detailed'),
        ('out_daily.json', 'default', 'auto', ['daily_report_mode'], ['reporte', 'daily'], 'concise'),
    ]

    for fname, level, mode, actions, reasons, style in scenarios:
        ok, sub = check_decision(ws, fname, expected_level=level, expected_mode=mode, expected_actions=actions, expected_contains=reasons, expected_policy_style=style, expect_brief=('brief_first' in actions))
        checks.extend(sub)
        all_passed = all_passed and ok

    # Verify state persistence for auto-off scenario changed state.json mode to off
    state, err = load_json_file(ws / 'state.json')
    if err:
        checks.append({"name": "state.json readable", "passed": False, "detail": err})
        all_passed = False
    else:
        mode = state.get('mode') if isinstance(state, dict) else None
        ok = normalize_text(mode) == normalize_text('off')
        checks.append({"name": "state persistence", "passed": ok, "detail": f"state.mode={mode} expected~off"})
        all_passed = all_passed and ok

    # Verify marker-rich inputs exist and are non-empty
    marker_files = ['case_cheap.txt', 'case_default.txt', 'case_pro.txt', 'case_override.txt', 'case_auto_off.txt', 'case_brief.txt', 'case_daily.txt']
    for fn in marker_files:
        text, err = safe_read(ws / fn)
        ok = err is None and text is not None and len(text) > 0
        marker_ok = ok and ('MARKER_CASE_' in text)
        checks.append({"name": f"input marker {fn}", "passed": marker_ok, "detail": err or text[:120]})
        all_passed = all_passed and marker_ok

    # Score based on passed checks
    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = (passed_count / total) if total else 0.0
    result = {"passed": bool(all_passed), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))
