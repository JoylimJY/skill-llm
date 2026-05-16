#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw cron guardrails task.
Checks that the agent produced a valid, correctly classified cron spec (final_cron_spec.json)
that passes all guardrail rules for a "scheduled visible delivery" job.
"""

import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Find final_cron_spec.json ───────────────────────────────────────────
    spec_files = list(workspace.rglob("final_cron_spec.json"))

    check_file_exists = {
        "name": "final_cron_spec.json exists",
        "passed": len(spec_files) > 0,
        "detail": f"Found {len(spec_files)} file(s): {[str(f) for f in spec_files]}" if spec_files else "File not found anywhere in workspace"
    }
    checks.append(check_file_exists)
    if not check_file_exists["passed"]:
        return False, 0.0, checks

    spec_path = spec_files[0]

    # ── Parse the spec ──────────────────────────────────────────────────────
    try:
        spec = json.loads(spec_path.read_text())
    except Exception as e:
        checks.append({"name": "spec JSON parseable", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    checks.append({"name": "spec JSON parseable", "passed": True, "detail": f"Parsed from {spec_path}"})

    # ── Check 1: version == "1" ─────────────────────────────────────────────
    version_ok = spec.get("version") == "1"
    checks.append({
        "name": "version is '1'",
        "passed": version_ok,
        "detail": f"version={spec.get('version')!r}"
    })
    if version_ok:
        total_score += 0.05

    # ── Check 2: taskType == "isolated" ─────────────────────────────────────
    # SKILL: "Scheduled visible delivery" → isolated + explicit delivery
    runtime = spec.get("runtime", {})
    task_type = runtime.get("taskType", "")
    task_type_ok = task_type == "isolated"
    checks.append({
        "name": "runtime.taskType is 'isolated' (scheduled visible delivery pattern)",
        "passed": task_type_ok,
        "detail": f"taskType={task_type!r}. Skill requires 'isolated' for scheduled visible delivery, NOT 'main'."
    })
    if task_type_ok:
        total_score += 0.20

    # ── Check 3: delivery.mode == "channel" (not systemEvent) ───────────────
    delivery = spec.get("delivery", {})
    delivery_mode = delivery.get("mode", "")
    delivery_mode_ok = delivery_mode == "channel"
    checks.append({
        "name": "delivery.mode is 'channel' (not systemEvent or none)",
        "passed": delivery_mode_ok,
        "detail": f"delivery.mode={delivery_mode!r}. Skill requires explicit 'channel' for scheduled visible delivery."
    })
    if delivery_mode_ok:
        total_score += 0.15

    # ── Check 4: delivery.channel is explicit and NOT "last" ─────────────────
    delivery_channel = delivery.get("channel", "")
    channel_ok = bool(delivery_channel) and delivery_channel != "last"
    checks.append({
        "name": "delivery.channel is explicit and not 'last'",
        "passed": channel_ok,
        "detail": f"delivery.channel={delivery_channel!r}. Skill explicitly forbids 'last' in multi-channel setups."
    })
    if channel_ok:
        total_score += 0.15

    # ── Check 5: delivery.to is non-empty ────────────────────────────────────
    delivery_to = delivery.get("to", "")
    to_ok = bool(delivery_to and delivery_to.strip())
    checks.append({
        "name": "delivery.to is explicitly set (non-empty)",
        "passed": to_ok,
        "detail": f"delivery.to={delivery_to!r}. Skill requires explicit 'to' when mode=channel."
    })
    if to_ok:
        total_score += 0.10

    # ── Check 6: sessionTarget == "none" ────────────────────────────────────
    session_target = runtime.get("sessionTarget", "")
    session_ok = session_target == "none"
    checks.append({
        "name": "runtime.sessionTarget is 'none' (isolated job must not use current session)",
        "passed": session_ok,
        "detail": f"sessionTarget={session_target!r}. Skill: isolated channel jobs must have sessionTarget='none'."
    })
    if session_ok:
        total_score += 0.10

    # ── Check 7: timeoutSeconds >= 180 ──────────────────────────────────────
    timeout = runtime.get("timeoutSeconds", 0)
    timeout_ok = isinstance(timeout, int) and timeout >= 180
    checks.append({
        "name": "runtime.timeoutSeconds >= 180 (non-trivial isolated task)",
        "passed": timeout_ok,
        "detail": f"timeoutSeconds={timeout}. Skill requires >= 180 for non-trivial isolated tasks."
    })
    if timeout_ok:
        total_score += 0.10

    # ── Check 8: schedule.tz is non-empty ───────────────────────────────────
    schedule = spec.get("schedule", {})
    tz = schedule.get("tz", "")
    tz_ok = bool(tz and tz.strip())
    checks.append({
        "name": "schedule.tz is explicitly set (wall-clock schedule requires timezone)",
        "passed": tz_ok,
        "detail": f"schedule.tz={tz!r}. Skill requires explicit tz for wall-clock schedules."
    })
    if tz_ok:
        total_score += 0.05

    # ── Check 9: schedule.cron is non-empty ─────────────────────────────────
    cron_expr = schedule.get("cron", "")
    cron_ok = bool(cron_expr and cron_expr.strip())
    checks.append({
        "name": "schedule.cron is set",
        "passed": cron_ok,
        "detail": f"schedule.cron={cron_expr!r}"
    })
    if cron_ok:
        total_score += 0.05

    # ── Check 10: payload.prompt is non-empty ───────────────────────────────
    payload = spec.get("payload", {})
    prompt_ok = bool(payload.get("prompt", "").strip())
    payload_kind_ok = payload.get("kind") == "prompt"
    checks.append({
        "name": "payload.kind='prompt' and payload.prompt is set",
        "passed": prompt_ok and payload_kind_ok,
        "detail": f"kind={payload.get('kind')!r}, prompt length={len(payload.get('prompt',''))}"
    })
    if prompt_ok and payload_kind_ok:
        total_score += 0.05

    # ── Check 11: validate_cron_spec.py passes ──────────────────────────────
    try:
        val_result = subprocess.run(
            ["python3", str(workspace / "scripts/validate_cron_spec.py"),
             "--spec", str(spec_path)],
            capture_output=True, text=True, timeout=30,
            cwd=str(workspace)
        )
        validator_passed = val_result.returncode == 0
        checks.append({
            "name": "validate_cron_spec.py reports spec as VALID",
            "passed": validator_passed,
            "detail": (val_result.stdout + val_result.stderr).strip()
        })
        if validator_passed:
            total_score += 0.0  # bonus already covered by individual checks above
    except Exception as e:
        checks.append({
            "name": "validate_cron_spec.py reports spec as VALID",
            "passed": False,
            "detail": f"Failed to run validator: {e}"
        })

    # ── Overall pass gate ────────────────────────────────────────────────────
    # Must pass all critical checks: taskType, delivery.mode, channel not last,
    # to not empty, sessionTarget=none, timeout>=180
    critical_names = [
        "runtime.taskType is 'isolated' (scheduled visible delivery pattern)",
        "delivery.mode is 'channel' (not systemEvent or none)",
        "delivery.channel is explicit and not 'last'",
        "delivery.to is explicitly set (non-empty)",
        "runtime.sessionTarget is 'none' (isolated job must not use current session)",
        "runtime.timeoutSeconds >= 180 (non-trivial isolated task)",
        "schedule.tz is explicitly set (wall-clock schedule requires timezone)",
        "validate_cron_spec.py reports spec as VALID",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_pass = all(critical_results.get(n, False) for n in critical_names)

    return all_critical_pass, round(total_score, 3), checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace_dir = sys.argv[1]

    try:
        passed, score, checks = run_checks(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, indent=2))
        sys.exit(1)

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()