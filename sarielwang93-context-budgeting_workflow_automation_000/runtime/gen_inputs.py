#!/usr/bin/env python3
"""
Generates the initial sandbox workspace for the context-budgeting task.
Deterministic: uses fixed seeds and hardcoded content.
"""
import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ─── Directory Structure ───────────────────────────────────────────────────────
dirs = [
    "skills/context-budgeting/scripts",
    "memory/hot",
    "memory/cold",
    "memory/archive",
    "pipeline/logs",
    "pipeline/configs",
    "pipeline/schemas",
    "pipeline/outputs/raw",
    "pipeline/outputs/processed",
    "agents/monitor",
    "agents/scheduler",
    "docs/runbooks",
    "docs/architecture",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)


# ─── Distractor Files ──────────────────────────────────────────────────────────

# 1. Pipeline config (distractor)
with open(os.path.join(WORKSPACE, "pipeline/configs/etl_config.yaml"), "w") as f:
    f.write("""pipeline:
  name: financial-data-ingestion
  version: 3.2.1
  schedule: "0 */6 * * *"
  sources:
    - type: s3
      bucket: raw-transactions
      prefix: 2024/
  sinks:
    - type: postgres
      host: db-prod-01
      database: analytics
""")

# 2. Schema file (distractor)
with open(os.path.join(WORKSPACE, "pipeline/schemas/transaction_schema.json"), "w") as f:
    json.dump({
        "type": "object",
        "properties": {
            "tx_id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "status": {"type": "string", "enum": ["pending", "settled", "failed"]}
        },
        "required": ["tx_id", "amount", "currency", "timestamp"]
    }, f, indent=2)

# 3. Massive raw JSON diagnostic dump (simulates "multi-megabyte" context pollution)
raw_diagnostics = {
    "run_id": "run-2024-07-15-094512",
    "agent": "pipeline-monitor-v2",
    "duration_seconds": 14402,
    "steps": []
}
step_templates = [
    ("fetch_batch", "success", "Fetched {n} records from S3 prefix 2024/07/15"),
    ("validate_schema", "success", "Schema validation passed for {n} records"),
    ("dedup_check", "warning", "Found {n} duplicate tx_ids, dropped"),
    ("enrich_fx_rates", "success", "Appended FX rates for {n} currency pairs"),
    ("write_staging", "success", "Wrote {n} rows to staging table"),
    ("run_anomaly_model", "failure", "Model timeout after {n}s on batch"),
    ("retry_anomaly_model", "success", "Retry succeeded after {n}s"),
    ("promote_to_prod", "success", "Promoted {n} rows to prod table"),
]
for i in range(120):
    tmpl = step_templates[i % len(step_templates)]
    raw_diagnostics["steps"].append({
        "step_index": i,
        "step_name": tmpl[0],
        "status": tmpl[1],
        "message": tmpl[2].format(n=random.randint(100, 99999)),
        "elapsed_ms": random.randint(200, 45000),
        "metadata": {
            "node": f"worker-{random.randint(1,8):02d}",
            "memory_mb": random.randint(512, 4096),
            "cpu_pct": round(random.uniform(10, 95), 2)
        }
    })
with open(os.path.join(WORKSPACE, "pipeline/outputs/raw/diagnostics_run_latest.json"), "w") as f:
    json.dump(raw_diagnostics, f, indent=2)

# 4. Processed output summary (distractor)
with open(os.path.join(WORKSPACE, "pipeline/outputs/processed/run_summary.txt"), "w") as f:
    f.write("""Run ID: run-2024-07-15-094512
Total records processed: 4,821,033
Failures: 3 (anomaly model timeouts, all retried successfully)
Final status: COMPLETE
Prod rows promoted: 4,820,891
Duplicates dropped: 142
""")

# 5. Agent turn log — raw messy dialogue (simulates short-term history overflow)
turns = [
    ("user", "Start monitoring the financial ingestion pipeline for run 2024-07-15."),
    ("agent", "Acknowledged. Initiating pipeline health checks. Fetching S3 manifest..."),
    ("user", "Any anomalies so far?"),
    ("agent", "Step 5 flagged 142 duplicate tx_ids. These have been dropped per dedup policy. Continuing."),
    ("user", "The anomaly model timed out — what happened?"),
    ("agent", "Worker-04 hit memory pressure at 3,891 MB. Model timed out at step 45. Retry on worker-07 succeeded in 8.2s."),
    ("user", "Good. How many records promoted to prod?"),
    ("agent", "4,820,891 rows promoted. Run is 94% complete. Remaining: final audit log flush."),
    ("user", "Do we need to re-validate FX rates?"),
    ("agent", "No. FX enrichment completed at step 16 for all 47 currency pairs without error."),
    ("user", "What's left?"),
    ("agent", "Final step: flush audit log to cold storage. Estimated 2 minutes."),
    ("user", "Complete the audit flush and then hold."),
    ("agent", "Audit log flushed. 14,402 seconds total runtime. Holding at checkpoint."),
    ("user", "Context is getting large. Summarize the key decisions before we continue."),
    ("agent", "Key decisions: (1) Dropped 142 duplicates. (2) Retried anomaly model on worker-07. (3) Promoted 4.82M rows. Awaiting next instruction."),
    ("user", "We're now over the memory limit threshold. Stabilize the session before continuing."),
]
with open(os.path.join(WORKSPACE, "agents/monitor/session_turns.jsonl"), "w") as f:
    for role, content in turns:
        f.write(json.dumps({"role": role, "content": content}) + "\n")

# 6. Old stale HOT_MEMORY (wrong format, from a previous aborted session — to confuse naive agents)
with open(os.path.join(WORKSPACE, "memory/hot/HOT_MEMORY.md"), "w") as f:
    f.write("""# Session Notes (STALE - DO NOT USE)

Last updated: 2024-07-14T22:10:00Z
Agent was monitoring pipeline run 2024-07-14.
Run failed at step 80 due to DB connection timeout.
Rolled back staging table.
---
TODO: Resume tomorrow with fresh context.
""")

# 7. Cold memory snippets (distractor — background knowledge)
with open(os.path.join(WORKSPACE, "memory/cold/pipeline_runbook.md"), "w") as f:
    f.write("""# Pipeline Runbook

## Duplicate Handling
Policy: Drop exact duplicate tx_ids within a 24h window. Log count to audit table.

## Anomaly Model
Timeout threshold: 30s. Auto-retry once on alternate worker. If retry fails, page on-call.

## FX Rates
Source: ECB reference rates, updated daily at 00:00 UTC.
Enrichment is idempotent; safe to re-run.

## Prod Promotion Criteria
- Schema validation: PASS
- Dedup check: PASS
- Anomaly model: PASS or retried-PASS
""")

# 8. Archive (distractor)
with open(os.path.join(WORKSPACE, "memory/archive/session_2024-07-14.md"), "w") as f:
    f.write("Archived session from 2024-07-14. Run failed. No prod promotion.\n")

# 9. Scheduler config (distractor)
with open(os.path.join(WORKSPACE, "agents/scheduler/cron_config.yaml"), "w") as f:
    f.write("""heartbeat_interval_minutes: 30
context_threshold_pct: 80
auto_compact_on_threshold: true
notify_on_compact: false
""")

# 10. Docs (distractor)
with open(os.path.join(WORKSPACE, "docs/runbooks/incident_response.md"), "w") as f:
    f.write("""# Incident Response Runbook

## P1 - Data Loss
1. Stop pipeline immediately.
2. Notify data-eng-oncall.
3. Roll back staging table.

## P2 - Delay > 2h
1. Check worker logs.
2. Identify bottleneck step.
3. Scale out workers if CPU > 80%.
""")

with open(os.path.join(WORKSPACE, "docs/architecture/context_window_limits.md"), "w") as f:
    f.write("""# Context Window Architecture

Agent context window: 200,000 tokens (estimated).
At 80% utilization (~160,000 tokens), GC is triggered automatically.
Raw JSON diagnostic outputs are primary contributor to context bloat.
""")

# 11. tmp scratch (distractor)
with open(os.path.join(WORKSPACE, "tmp/scratch/notes.txt"), "w") as f:
    f.write("scratch pad - ignore\nfx_rate_eur_usd=1.0823\ncheck worker-04 logs tomorrow\n")


# ─── THE KEY ARTIFACT: gc_and_checkpoint.sh ───────────────────────────────────
# This is the proprietary automation script the agent must call.
# It validates that HOT_MEMORY.md exists and has the required fields,
# then writes a sentinel file to confirm it was invoked correctly.
gc_script_content = r"""#!/usr/bin/env bash
# gc_and_checkpoint.sh — OpenClaw context compaction automation
# Called AFTER the agent updates memory/hot/HOT_MEMORY.md

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOT_MEMORY="${WORKSPACE_ROOT}/memory/hot/HOT_MEMORY.md"
SENTINEL="${WORKSPACE_ROOT}/memory/hot/.gc_ran"

echo "[gc_and_checkpoint] Starting context compaction..."

# Verify HOT_MEMORY.md exists
if [ ! -f "${HOT_MEMORY}" ]; then
  echo "[gc_and_checkpoint] ERROR: HOT_MEMORY.md not found. Aborting."
  exit 1
fi

# Verify required fields exist
for field in "Status" "Key Decision" "Next Step"; do
  if ! grep -qi "^##\? *${field}" "${HOT_MEMORY}" 2>/dev/null && \
     ! grep -qi "^\*\*${field}\*\*" "${HOT_MEMORY}" 2>/dev/null && \
     ! grep -qi "^${field}:" "${HOT_MEMORY}" 2>/dev/null; then
    echo "[gc_and_checkpoint] WARNING: Field '${field}' may be missing from HOT_MEMORY.md"
  fi
done

# Simulate clearing raw data (write a log entry)
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo 'unknown')"
echo "[gc_and_checkpoint] Compaction run at ${TIMESTAMP}" >> "${WORKSPACE_ROOT}/memory/hot/compaction.log"

# Write sentinel file to prove script was actually executed
echo "gc_ran_at=${TIMESTAMP}" > "${SENTINEL}"
echo "hot_memory_path=${HOT_MEMORY}" >> "${SENTINEL}"

echo "[gc_and_checkpoint] Context compaction complete. Sentinel written to ${SENTINEL}"
"""

gc_script_path = os.path.join(WORKSPACE, "skills/context-budgeting/scripts/gc_and_checkpoint.sh")
with open(gc_script_path, "w") as f:
    f.write(gc_script_content)

# Make it executable
os.chmod(gc_script_path, 0o755)

print("Workspace generation complete.")
print(f"Key files created:")
print(f"  - skills/context-budgeting/scripts/gc_and_checkpoint.sh (executable)")
print(f"  - memory/hot/HOT_MEMORY.md (stale, must be overwritten)")
print(f"  - agents/monitor/session_turns.jsonl (15-turn session log)")
print(f"  - pipeline/outputs/raw/diagnostics_run_latest.json (120-step diagnostic dump)")