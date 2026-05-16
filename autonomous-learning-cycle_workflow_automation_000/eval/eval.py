import json
import sys
import os
from pathlib import Path

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    passed_all = True

    # ── BLOCK 1: confidence-config.json ─────────────────────────────────────

    conf_path = Path(workspace) / "skills" / "autonomous-learning-cycle" / "configs" / "confidence-config.json"
    conf_data = None
    try:
        conf_data = load_json_file(conf_path)
    except Exception as e:
        checks.append({"name": "confidence-config: file readable", "passed": False, "detail": str(e)})
        passed_all = False
        conf_data = {}

    # Check weights keys
    weights = conf_data.get("weights", {})
    expected_weight_keys = {"baseScore", "successRate", "usageBonus", "timeDecay", "qualityBonus"}
    actual_keys = set(weights.keys())
    keys_ok = actual_keys == expected_weight_keys
    checks.append({
        "name": "confidence-config: weights has correct 5 keys",
        "passed": keys_ok,
        "detail": f"Expected keys {expected_weight_keys}, got {actual_keys}"
    })
    if not keys_ok:
        passed_all = False

    # Check weight values exactly match SKILL.md
    w_checks = [
        ("baseScore", 0.5),
        ("successRate", 0.3),
        ("usageBonus", 0.15),
        ("timeDecay", 0.05),
        ("qualityBonus", 0.1),
    ]
    for key, expected_val in w_checks:
        actual_val = weights.get(key)
        ok = actual_val == expected_val
        checks.append({
            "name": f"confidence-config: weights.{key} == {expected_val}",
            "passed": ok,
            "detail": f"Got {actual_val}"
        })
        if not ok:
            passed_all = False

    # Check thresholds - task says to use 0.8 for high (best practices: raise from 0.7 to 0.8)
    thresholds = conf_data.get("thresholds", {})
    threshold_checks = [
        ("high", 0.8),    # Per SKILL.md best practices: raise to 0.8
        ("medium", 0.4),
        ("low", 0.0),
    ]
    for key, expected_val in threshold_checks:
        actual_val = thresholds.get(key)
        ok = actual_val == expected_val
        checks.append({
            "name": f"confidence-config: thresholds.{key} == {expected_val}",
            "passed": ok,
            "detail": f"Got {actual_val}"
        })
        if not ok:
            passed_all = False

    # Check decay block
    decay = conf_data.get("decay", {})
    decay_checks = [
        ("daysToHalf", 30),
        ("minDecay", 0.5),
    ]
    for key, expected_val in decay_checks:
        actual_val = decay.get(key)
        ok = actual_val == expected_val
        checks.append({
            "name": f"confidence-config: decay.{key} == {expected_val}",
            "passed": ok,
            "detail": f"Got {actual_val}"
        })
        if not ok:
            passed_all = False

    # ── BLOCK 2: cron-jobs.json ──────────────────────────────────────────────

    cron_path = Path(workspace) / "skills" / "autonomous-learning-cycle" / "configs" / "cron-jobs.json"
    cron_data = None
    try:
        cron_data = load_json_file(cron_path)
    except Exception as e:
        checks.append({"name": "cron-jobs: file readable", "passed": False, "detail": str(e)})
        passed_all = False
        cron_data = {}

    jobs = cron_data.get("jobs", [])
    checks.append({
        "name": "cron-jobs: exactly 4 jobs defined",
        "passed": len(jobs) == 4,
        "detail": f"Got {len(jobs)} jobs"
    })
    if len(jobs) != 4:
        passed_all = False

    # Build lookup by name
    jobs_by_name = {j.get("name"): j for j in jobs}

    expected_jobs = [
        {
            "name": "自主进化循环",
            "schedule": "*/17 * * * *",
            "command": "node engines/evolution-engine.js run"
        },
        {
            "name": "每日反思",
            "schedule": "0 23 * * *",
            "command": "node engines/reflection.js daily"
        },
        {
            "name": "每周反思",
            "schedule": "0 20 * * 0",
            "command": "node engines/reflection.js weekly"
        },
        {
            "name": "学习方向生成",
            "schedule": "0 6 * * *",
            "command": "node engines/learning-direction.js auto"
        },
    ]

    for ej in expected_jobs:
        job_name = ej["name"]
        job = jobs_by_name.get(job_name)
        if job is None:
            checks.append({
                "name": f"cron-jobs: job '{job_name}' exists",
                "passed": False,
                "detail": f"Job not found. Available: {list(jobs_by_name.keys())}"
            })
            passed_all = False
            continue

        checks.append({
            "name": f"cron-jobs: job '{job_name}' exists",
            "passed": True,
            "detail": "Found"
        })

        sched_ok = job.get("schedule") == ej["schedule"]
        checks.append({
            "name": f"cron-jobs: '{job_name}' schedule == '{ej['schedule']}'",
            "passed": sched_ok,
            "detail": f"Got '{job.get('schedule')}'"
        })
        if not sched_ok:
            passed_all = False

        cmd_ok = job.get("command") == ej["command"]
        checks.append({
            "name": f"cron-jobs: '{job_name}' command == '{ej['command']}'",
            "passed": cmd_ok,
            "detail": f"Got '{job.get('command')}'"
        })
        if not cmd_ok:
            passed_all = False

    # ── BLOCK 3: Required directory structure ────────────────────────────────

    # memory/reflections must exist
    reflections_dir = Path(workspace) / "memory" / "reflections"
    refl_ok = reflections_dir.is_dir()
    checks.append({
        "name": "directory: memory/reflections/ exists",
        "passed": refl_ok,
        "detail": f"Path: {reflections_dir}"
    })
    if not refl_ok:
        passed_all = False

    # tasks/queue.json must exist with proper structure
    queue_path = Path(workspace) / "tasks" / "queue.json"
    try:
        queue_data = load_json_file(queue_path)
        has_tasks_key = "tasks" in queue_data
        checks.append({
            "name": "tasks/queue.json: exists and has 'tasks' key",
            "passed": has_tasks_key,
            "detail": f"Keys found: {list(queue_data.keys())}"
        })
        if not has_tasks_key:
            passed_all = False
    except Exception as e:
        checks.append({
            "name": "tasks/queue.json: exists and has 'tasks' key",
            "passed": False,
            "detail": str(e)
        })
        passed_all = False

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))