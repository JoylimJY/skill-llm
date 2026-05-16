import os
import json
import random
import stat

random.seed(42)

workspace = os.environ.get("WORKSPACE", "/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "skill-dir/scripts",
    "skill-dir/references",
    "project/src",
    "project/logs",
    "project/tmp",
    "project/config",
    "project/cache/npm",
    "project/cache/pip",
    "system/journal",
    "system/sessions",
    "distractor/old_backups",
    "distractor/reports",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Mock check_resources.sh ─────────────────────────────────────────────────
# Returns WARNING-level JSON (RAM at ~82%)
check_resources = r"""#!/usr/bin/env bash
# Mock check_resources.sh — simulates a WARNING-level resource state

RAM_TOTAL=4096
RAM_USED=3360
RAM_PCT=82
CPU_PCT=34
TOP_PROC="openclaw-worker"
TOP_MEM_MB=1120

cat <<EOF
{
  "alert": "WARNING",
  "ram": {
    "total_mb": ${RAM_TOTAL},
    "used_mb": ${RAM_USED},
    "free_mb": $((RAM_TOTAL - RAM_USED)),
    "pct": ${RAM_PCT}
  },
  "cpu": {
    "pct": ${CPU_PCT}
  },
  "top_process": {
    "name": "${TOP_PROC}",
    "mem_mb": ${TOP_MEM_MB}
  }
}
EOF
"""

check_path = os.path.join(workspace, "skill-dir/scripts/check_resources.sh")
with open(check_path, "w") as f:
    f.write(check_resources)
os.chmod(check_path, os.stat(check_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Mock cleanup_sessions.sh ────────────────────────────────────────────────
# Logs every invocation to /tmp/cleanup_invocations.log
cleanup_sessions = r"""#!/usr/bin/env bash
# Mock cleanup_sessions.sh — records how it was called

LOG_FILE="/tmp/cleanup_invocations.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

MODE="normal"
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            ;;
        --aggressive)
            MODE="aggressive"
            ;;
    esac
done

echo "${TIMESTAMP} dry_run=${DRY_RUN} mode=${MODE} args=$*" >> "${LOG_FILE}"

if [ "$DRY_RUN" = "true" ]; then
    echo "[DRY-RUN] Would clean: 3 stale sessions, 512MB npm cache, 256MB pip cache, 89MB journal"
else
    if [ "$MODE" = "aggressive" ]; then
        echo "[CLEANUP] Removed: 3 stale sessions, 512MB npm cache, 256MB pip cache, 89MB journal"
        echo "[CLEANUP] Aggressive mode: additional caches purged"
    else
        echo "[CLEANUP] Removed: 3 stale sessions"
    fi
fi
"""

cleanup_path = os.path.join(workspace, "skill-dir/scripts/cleanup_sessions.sh")
with open(cleanup_path, "w") as f:
    f.write(cleanup_sessions)
os.chmod(cleanup_path, os.stat(cleanup_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Distractor: partial / misleading config file ────────────────────────────
bad_config = {
    "model": "gpt-4o",
    "thinking": "enabled",
    "subagents": {"max_concurrent": 8},
    "browser": {"keep_open": True},
    "fetch_method": "browser_automation",
    "subagent_mode": "session"
}
with open(os.path.join(workspace, "project/config/openclaw.json"), "w") as f:
    json.dump(bad_config, f, indent=2)

# ── Distractor: stale log files ─────────────────────────────────────────────
for i in range(4):
    with open(os.path.join(workspace, f"project/logs/worker_{i}.log"), "w") as f:
        f.write(f"[2024-01-{10+i}] worker {i} started\n" * random.randint(50, 200))

# ── Distractor: temp / cache junk ───────────────────────────────────────────
for name in ["session_abc.tmp", "session_def.tmp", "session_xyz.tmp"]:
    with open(os.path.join(workspace, f"system/sessions/{name}"), "w") as f:
        f.write("stale session data\n" * 10)

for pkg in ["lodash-4.17.21.tgz", "express-5.0.0.tgz"]:
    with open(os.path.join(workspace, f"project/cache/npm/{pkg}"), "w") as f:
        f.write("binary cache placeholder\n")

with open(os.path.join(workspace, "project/cache/pip/requirements_cache.txt"), "w") as f:
    f.write("numpy==1.26.0\ntorch==2.2.0\ntransformers==4.38.0\n")

# ── Distractor: old backup files ────────────────────────────────────────────
for i in range(3):
    with open(os.path.join(workspace, f"distractor/old_backups/backup_{2022+i}.tar.gz.stub"), "w") as f:
        f.write(f"stub backup {2022+i}\n")

# ── Distractor: a red-herring "health" report from months ago ───────────────
old_report = {
    "date": "2024-11-01",
    "status": "OK",
    "note": "Everything was fine back then"
}
with open(os.path.join(workspace, "distractor/reports/health_2024_11.json"), "w") as f:
    json.dump(old_report, f, indent=2)

# ── Distractor: journal fragments ───────────────────────────────────────────
for j in range(3):
    with open(os.path.join(workspace, f"system/journal/entry_{j:03d}.log"), "w") as f:
        f.write(f"journal entry {j}: system event recorded\n" * 30)

# ── Distractor: a misleading "optimization tips" text ───────────────────────
with open(os.path.join(workspace, "distractor/optimization_notes.txt"), "w") as f:
    f.write(
        "General tip: use GPT-4 for best results.\n"
        "Increase subagents for parallelism.\n"
        "Always keep browser open for speed.\n"
        "Enable thinking mode for complex tasks.\n"
        "Use browser automation for robust fetching.\n"
    )

# ── Distractor: a broken partial script ─────────────────────────────────────
with open(os.path.join(workspace, "project/src/monitor.sh"), "w") as f:
    f.write("#!/bin/bash\n# TODO: finish this\n# check_resources | grep alert\n")

print("Workspace generated successfully.")
print(f"Key paths:\n  {check_path}\n  {cleanup_path}")