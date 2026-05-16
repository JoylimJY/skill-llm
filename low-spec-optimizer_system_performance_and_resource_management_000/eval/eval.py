import sys
import json
import os
import re
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def run_checks(workspace: str):
    checks = []
    overall_passed = True

    # ── Locate optimization_report.json anywhere in workspace ──────────────
    candidates = list(Path(workspace).rglob("optimization_report.json"))
    report = None
    report_path = None

    try:
        if not candidates:
            raise FileNotFoundError("optimization_report.json not found")
        report_path = str(candidates[0])
        report = load_json_file(report_path)
        checks.append({"name": "report_exists", "passed": True,
                        "detail": f"Found at {report_path}"})
    except Exception as e:
        checks.append({"name": "report_exists", "passed": False, "detail": str(e)})
        overall_passed = False
        return overall_passed, 0.0, checks

    # ── CHECK 1: alert_level field is WARNING ───────────────────────────────
    try:
        raw = json.dumps(report).lower()
        # Accept in any sub-field
        alert_val = None
        def find_alert(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "alert" in k.lower() and isinstance(v, str):
                        return v.upper()
                    result = find_alert(v)
                    if result:
                        return result
            elif isinstance(obj, list):
                for item in obj:
                    result = find_alert(item)
                    if result:
                        return result
            return None

        alert_val = find_alert(report)
        passed = alert_val == "WARNING"
        checks.append({"name": "alert_level_warning", "passed": passed,
                        "detail": f"Found alert level: {alert_val}"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "alert_level_warning", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 2: RAM percentage captured correctly (~82%) ───────────────────
    try:
        report_str = json.dumps(report)
        found_pct = re.search(r'\b8[0-9]\b', report_str)
        # look for something in the 80-89 range representing ~82%
        passed = bool(found_pct)
        checks.append({"name": "ram_pct_captured", "passed": passed,
                        "detail": f"RAM percentage in 80–89 range found: {bool(found_pct)}"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "ram_pct_captured", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 3: Top process identified (openclaw-worker) ───────────────────
    try:
        report_str = json.dumps(report).lower()
        passed = "openclaw" in report_str or "openclaw-worker" in report_str
        checks.append({"name": "top_process_identified", "passed": passed,
                        "detail": f"'openclaw-worker' mentioned in report: {passed}"})
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "top_process_identified", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 4: Cleanup invocation log — dry-run was called FIRST ──────────
    try:
        log_path = "/tmp/cleanup_invocations.log"
        if not os.path.exists(log_path):
            raise FileNotFoundError("Cleanup invocation log missing")
        with open(log_path) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        if not lines:
            raise ValueError("No cleanup invocations recorded")

        first_line = lines[0]
        dry_run_first = "dry_run=true" in first_line.lower()
        checks.append({"name": "cleanup_dry_run_first", "passed": dry_run_first,
                        "detail": f"First invocation: {first_line}"})
        if not dry_run_first:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "cleanup_dry_run_first", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 5: Cleanup invocation log — aggressive mode was used ──────────
    try:
        log_path = "/tmp/cleanup_invocations.log"
        with open(log_path) as f:
            all_lines = f.read().lower()
        aggressive_used = "mode=aggressive" in all_lines or "--aggressive" in all_lines
        checks.append({"name": "cleanup_aggressive_used", "passed": aggressive_used,
                        "detail": f"Aggressive cleanup invocation found: {aggressive_used}"})
        if not aggressive_used:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "cleanup_aggressive_used", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 6: Config recommendation — lightweight model name ─────────────
    try:
        report_str = json.dumps(report).lower()
        has_model = ("hunter-alpha" in report_str or "glm-4.5-air" in report_str
                     or "glm4.5" in report_str or "glm-4" in report_str)
        checks.append({"name": "config_rec_lightweight_model", "passed": has_model,
                        "detail": f"Lightweight model (hunter-alpha or GLM-4.5-air) mentioned: {has_model}"})
        if not has_model:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_rec_lightweight_model", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 7: Config recommendation — thinking off ────────────────────────
    try:
        report_str = json.dumps(report).lower()
        has_thinking_off = (
            "thinking" in report_str and
            ("off" in report_str or '"off"' in json.dumps(report).lower() or "disable" in report_str)
        )
        checks.append({"name": "config_rec_thinking_off", "passed": has_thinking_off,
                        "detail": f"Thinking=off recommended: {has_thinking_off}"})
        if not has_thinking_off:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_rec_thinking_off", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 8: Config recommendation — subagent limit ≤ 2 ─────────────────
    try:
        report_str = json.dumps(report)
        # look for a number ≤2 near "subagent"
        subagent_nums = re.findall(r'(?i)subagent[^0-9]{0,30}(\d+)', report_str)
        subagent_nums += re.findall(r'(\d+)[^0-9]{0,30}(?i)subagent', report_str)
        valid_limit = any(int(n) <= 2 for n in subagent_nums if n.isdigit())
        checks.append({"name": "config_rec_subagent_limit", "passed": valid_limit,
                        "detail": f"Subagent limit ≤2 found (numbers near 'subagent': {subagent_nums})"})
        if not valid_limit:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_rec_subagent_limit", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 9: Config recommendation — web_fetch preference ───────────────
    try:
        report_str = json.dumps(report).lower()
        has_webfetch = "web_fetch" in report_str or "webfetch" in report_str
        checks.append({"name": "config_rec_web_fetch", "passed": has_webfetch,
                        "detail": f"web_fetch preference mentioned: {has_webfetch}"})
        if not has_webfetch:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_rec_web_fetch", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── CHECK 10: Config recommendation — mode:run for subagents ─────────────
    try:
        report_str = json.dumps(report).lower()
        has_mode_run = (
            ("mode" in report_str and "run" in report_str) or
            '"run"' in json.dumps(report).lower()
        )
        checks.append({"name": "config_rec_mode_run", "passed": has_mode_run,
                        "detail": f"subagent mode=run mentioned: {has_mode_run}"})
        if not has_mode_run:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "config_rec_mode_run", "passed": False, "detail": str(e)})
        overall_passed = False

    # ── Score ────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    final_passed = overall_passed and (passed_count >= total - 1)  # allow 1 minor miss

    return final_passed, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    passed, score, checks = run_checks(workspace)
    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()