import sys
import json
import subprocess
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score_total = 0.0
score_weights = {}

def run_clawion(*args):
    """Run a clawion CLI command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["clawion"] + list(args),
            capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_weights[name] = weight
    return passed

# Load mission brief for reference values
try:
    brief = json.loads((workspace / "mission_brief.json").read_text())
    MISSION_ID = brief["mission"]["id"]
    MANAGER_ID = next(a["id"] for a in brief["agents"] if a["role"] == "manager")
    WORKER_IDS = [a["id"] for a in brief["agents"] if a["role"] == "worker"]
    ALL_AGENT_IDS = [a["id"] for a in brief["agents"]]
    TASK_IDS = [t["id"] for t in brief["tasks"]]
    TASK_ASSIGNMENTS = {t["id"]: t["assigned_to"] for t in brief["tasks"]}
    CRON_INTERVAL = brief["cron_interval_minutes"]
    AGENT_COUNT = len(brief["agents"])
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [
        {"name": "brief_load", "passed": False, "detail": f"Could not load mission_brief.json: {e}"}
    ]}))
    sys.exit(0)

# -----------------------------------------------------------------------
# CHECK 1: Mission exists
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("mission", "show", "--id", MISSION_ID)
    if rc == 0 and MISSION_ID in stdout:
        add_check("mission_created", True, f"Mission '{MISSION_ID}' exists.", weight=1.0)
    else:
        add_check("mission_created", False, f"Mission '{MISSION_ID}' not found. rc={rc} stderr={stderr[:200]}", weight=1.0)
except Exception as e:
    add_check("mission_created", False, f"Exception: {e}", weight=1.0)

# -----------------------------------------------------------------------
# CHECK 2: Manager agent registered with system-role=manager
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("agent", "show", "--mission", MISSION_ID, "--id", MANAGER_ID)
    if rc == 0 and "manager" in stdout.lower():
        add_check("manager_registered", True, f"Manager '{MANAGER_ID}' registered with manager role.", weight=1.5)
    else:
        add_check("manager_registered", False, f"Manager agent missing or wrong role. rc={rc} stdout={stdout[:300]}", weight=1.5)
except Exception as e:
    add_check("manager_registered", False, f"Exception: {e}", weight=1.5)

# -----------------------------------------------------------------------
# CHECK 3: Worker agents registered with system-role=worker
# -----------------------------------------------------------------------
workers_ok = True
worker_details = []
for wid in WORKER_IDS:
    try:
        rc, stdout, stderr = run_clawion("agent", "show", "--mission", MISSION_ID, "--id", wid)
        if rc == 0 and "worker" in stdout.lower():
            worker_details.append(f"{wid}: OK")
        else:
            workers_ok = False
            worker_details.append(f"{wid}: MISSING or wrong role. stdout={stdout[:100]}")
    except Exception as e:
        workers_ok = False
        worker_details.append(f"{wid}: Exception {e}")
add_check("workers_registered", workers_ok, "; ".join(worker_details), weight=1.5)

# -----------------------------------------------------------------------
# CHECK 4: Tasks created and assigned correctly
# -----------------------------------------------------------------------
tasks_ok = True
task_details = []
for tid, assignee in TASK_ASSIGNMENTS.items():
    try:
        rc, stdout, stderr = run_clawion("task", "show", "--mission", MISSION_ID, "--id", tid)
        if rc == 0 and assignee in stdout:
            task_details.append(f"{tid}→{assignee}: OK")
        elif rc == 0:
            tasks_ok = False
            task_details.append(f"{tid}: exists but assignee '{assignee}' not found in output. stdout={stdout[:150]}")
        else:
            tasks_ok = False
            task_details.append(f"{tid}: not found. rc={rc} stderr={stderr[:100]}")
    except Exception as e:
        tasks_ok = False
        task_details.append(f"{tid}: Exception {e}")
add_check("tasks_created_and_assigned", tasks_ok, "; ".join(task_details), weight=2.0)

# -----------------------------------------------------------------------
# CHECK 5: Mission roadmap set
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("mission", "roadmap", "--id", MISSION_ID)
    if rc == 0 and len(stdout.strip()) > 20:
        add_check("roadmap_set", True, f"Roadmap present ({len(stdout.strip())} chars).", weight=1.0)
    else:
        add_check("roadmap_set", False, f"Roadmap empty or missing. rc={rc} stdout={stdout[:200]}", weight=1.0)
except Exception as e:
    add_check("roadmap_set", False, f"Exception: {e}", weight=1.0)

# -----------------------------------------------------------------------
# CHECK 6: Cron jobs created — one per agent, naming convention enforced
# Expected: clawion:<MISSION_ID>:manager:<MANAGER_ID>
#           clawion:<MISSION_ID>:worker:<WORKER_ID_1>
#           clawion:<MISSION_ID>:worker:<WORKER_ID_2>
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("cron", "list", "--mission", MISSION_ID)
    cron_output = stdout if rc == 0 else ""

    expected_job_names = []
    for agent in brief["agents"]:
        role = "manager" if agent["role"] == "manager" else "worker"
        expected_job_names.append(f"clawion:{MISSION_ID}:{role}:{agent['id']}")

    found_jobs = []
    missing_jobs = []
    for jname in expected_job_names:
        if jname in cron_output:
            found_jobs.append(jname)
        else:
            missing_jobs.append(jname)

    if not missing_jobs:
        add_check("cron_jobs_naming", True, f"All cron jobs found with correct names: {found_jobs}", weight=2.0)
    else:
        add_check("cron_jobs_naming", False, f"Missing jobs: {missing_jobs}. Found in output: {cron_output[:400]}", weight=2.0)
except Exception as e:
    add_check("cron_jobs_naming", False, f"Exception listing cron jobs: {e}", weight=2.0)

# -----------------------------------------------------------------------
# CHECK 7: All cron jobs created DISABLED
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("cron", "list", "--mission", MISSION_ID)
    cron_output = stdout if rc == 0 else ""

    # Parse cron list output: look for 'enabled: false' or 'disabled' associated with our jobs
    # Attempt JSON parse first, else text heuristic
    all_disabled = True
    disable_details = []
    try:
        cron_data = json.loads(cron_output)
        jobs = cron_data if isinstance(cron_data, list) else cron_data.get("jobs", [])
        for job in jobs:
            jname = job.get("name", "")
            if MISSION_ID in jname:
                enabled = job.get("enabled", job.get("active", True))
                if enabled:
                    all_disabled = False
                    disable_details.append(f"{jname}: ENABLED (should be disabled)")
                else:
                    disable_details.append(f"{jname}: disabled OK")
    except Exception:
        # Fallback text heuristic: if any job line contains 'enabled: true' or 'active: true'
        lines = cron_output.lower().splitlines()
        for line in lines:
            if MISSION_ID in line and ("enabled: true" in line or "active: true" in line or '"enabled":true' in line):
                all_disabled = False
                disable_details.append(f"Enabled job detected: {line[:100]}")
        if not disable_details:
            disable_details.append("Could not verify disabled state from text output — assuming OK if naming passed.")

    add_check("cron_jobs_disabled", all_disabled, "; ".join(disable_details) if disable_details else "All verified disabled.", weight=1.5)
except Exception as e:
    add_check("cron_jobs_disabled", False, f"Exception: {e}", weight=1.5)

# -----------------------------------------------------------------------
# CHECK 8: Cron job payload is minimal (wake command only, no embedded context)
# -----------------------------------------------------------------------
try:
    rc, stdout, stderr = run_clawion("cron", "list", "--mission", MISSION_ID)
    cron_output = stdout if rc == 0 else ""

    # Forbidden phrases that indicate the agent embedded context into the payload
    forbidden_phrases = [
        "task-ingest", "task-qc", "batch 003", "staging database",
        "schema validation", "roadmap", "phase 1", "phase 2",
        "ingestion sop", "qc checklist", "trial-data-pipeline",
    ]
    # Required phrase: the wake command must be present
    required_phrase = "clawion agent wake"

    payload_clean = True
    payload_details = []

    if required_phrase not in cron_output.lower():
        payload_clean = False
        payload_details.append(f"Required phrase '{required_phrase}' not found in cron output.")

    for phrase in forbidden_phrases:
        if phrase.lower() in cron_output.lower():
            payload_clean = False
            payload_details.append(f"Forbidden embedded context found: '{phrase}'")

    if payload_clean:
        add_check("cron_payload_minimal", True, "Cron payload is minimal and contains wake command.", weight=2.0)
    else:
        add_check("cron_payload_minimal", False, "; ".join(payload_details), weight=2.0)
except Exception as e:
    add_check("cron_payload_minimal", False, f"Exception: {e}", weight=2.0)

# -----------------------------------------------------------------------
# CHECK 9: Staggered cron offsets (N=15 min, K=3 agents → offsets: 0, 5, 10)
# Formula: round(i * N / K) for i=0..K-1
# -----------------------------------------------------------------------
try:
    N = CRON_INTERVAL  # 15
    K = AGENT_COUNT    # 3
    expected_offsets = sorted([round(i * N / K) for i in range(K)])
    # expected_offsets = [0, 5, 10]

    rc, stdout, stderr = run_clawion("cron", "list", "--mission", MISSION_ID)
    cron_output = stdout if rc == 0 else ""

    # Try to extract offset/delay/stagger values from the cron output
    import re
    found_offsets = set()

    # Look for patterns like offset:5, delay:5, +5m, stagger:5
    offset_patterns = [
        r'"offset"\s*:\s*(\d+)',
        r'"delay"\s*:\s*(\d+)',
        r'"stagger"\s*:\s*(\d+)',
        r'offset[:\s]+(\d+)',
        r'\+(\d+)m',
        r'minute.*?(\d+)',
    ]
    for pat in offset_patterns:
        for m in re.finditer(pat, cron_output, re.IGNORECASE):
            found_offsets.add(int(m.group(1)))

    # Check if at least 2 of the 3 expected non-zero offsets appear
    # (offset 0 is default and may not be explicitly listed)
    non_zero_expected = set(o for o in expected_offsets if o > 0)  # {5, 10}
    matched = non_zero_expected & found_offsets

    if len(matched) >= len(non_zero_expected):
        add_check("cron_stagger_offsets", True,
                  f"Expected offsets {expected_offsets} (non-zero: {non_zero_expected}), found in output: {sorted(found_offsets)}",
                  weight=2.0)
    else:
        add_check("cron_stagger_offsets", False,
                  f"Expected stagger offsets {expected_offsets} (formula: round(i*{N}/{K})). Non-zero offsets needed: {non_zero_expected}. Found in cron output: {sorted(found_offsets)}. Raw output snippet: {cron_output[:300]}",
                  weight=2.0)
except Exception as e:
    add_check("cron_stagger_offsets", False, f"Exception parsing stagger offsets: {e}", weight=2.0)

# -----------------------------------------------------------------------
# SCORING
# -----------------------------------------------------------------------
total_weight = sum(score_weights[c["name"]] for c in checks)
earned_weight = sum(score_weights[c["name"]] for c in checks if c["passed"])
final_score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))