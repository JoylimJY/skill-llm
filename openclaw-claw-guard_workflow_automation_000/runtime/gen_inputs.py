#!/usr/bin/env python3
"""
Generate the sandbox workspace for the claw-guard evaluation task.
Creates a realistic quantitative finance pipeline project with messy ops artifacts.
"""

import os
import json
import random
import stat
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "quant_pipeline/src",
    "quant_pipeline/src/exporters",
    "quant_pipeline/src/validators",
    "quant_pipeline/src/utils",
    "quant_pipeline/configs",
    "quant_pipeline/configs/backups",
    "quant_pipeline/logs",
    "quant_pipeline/outputs/gguf_exports",
    "quant_pipeline/outputs/parquet_dumps",
    "quant_pipeline/outputs/risk_matrices",
    "quant_pipeline/tests",
    "quant_pipeline/docs",
    "ops/runbooks",
    "ops/alerts",
    "ops/monitoring",
    "gateway/configs",
    "gateway/logs",
    "tmp/pids",
    "tmp/scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor source files ───────────────────────────────────────────────────
distractor_files = {
    "quant_pipeline/src/exporters/gguf_exporter.py": """\
#!/usr/bin/env python3
\"\"\"GGUF model export pipeline for quantitative risk models.\"\"\"
import time, sys, os, argparse

def export_model(model_path, output_dir, quantization="q8_0"):
    print(f"[gguf_exporter] Exporting {model_path} -> {output_dir} (quant={quantization})")
    time.sleep(0.1)
    outfile = os.path.join(output_dir, "risk_model_q8.gguf")
    with open(outfile, "wb") as f:
        f.write(b"GGUF" + b"\\x00" * 128)
    print(f"[gguf_exporter] Done: {outfile}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    export_model(args.model, args.output_dir)
""",
    "quant_pipeline/src/exporters/parquet_dumper.py": """\
#!/usr/bin/env python3
\"\"\"Dumps factor model outputs to Parquet for downstream consumers.\"\"\"
import time, sys

def dump_factors(factor_db, output_path, date_range):
    print(f"[parquet_dumper] Dumping {factor_db} for {date_range}")
    time.sleep(0.1)
    print(f"[parquet_dumper] Written to {output_path}")

if __name__ == "__main__":
    dump_factors("factor_db_prod", "/workspace/quant_pipeline/outputs/parquet_dumps/factors.parquet", "2024-01-01:2024-12-31")
""",
    "quant_pipeline/src/validators/schema_check.py": """\
#!/usr/bin/env python3
\"\"\"Validates output schemas against registered model contracts.\"\"\"

SCHEMAS = {
    "risk_matrix": ["asset_id", "date", "var_1d", "cvar_5pct"],
    "factor_loadings": ["asset_id", "factor", "loading", "t_stat"],
}

def validate(data, schema_name):
    schema = SCHEMAS.get(schema_name, [])
    missing = [col for col in schema if col not in data.columns]
    return len(missing) == 0, missing
""",
    "quant_pipeline/src/utils/notify.py": """\
#!/usr/bin/env python3
\"\"\"Internal notification utility — wraps openclaw message send.\"\"\"
import subprocess

def send(target, message):
    cmd = ["openclaw", "message", "send", "--target", target, "--message", message]
    subprocess.run(cmd, capture_output=True)
""",
    "quant_pipeline/configs/pipeline_config.yaml": """\
version: "2.1.4"
pipeline:
  name: "overnight-quant-export"
  schedule: "0 22 * * 1-5"
  timeout_hours: 6
  retry_attempts: 3

jobs:
  gguf_export:
    model: "/data/models/risk_model_v3.safetensors"
    quantization: "q8_0"
    output_dir: "/workspace/quant_pipeline/outputs/gguf_exports"
    
  parquet_dump:
    source_db: "factor_db_prod"
    output_dir: "/workspace/quant_pipeline/outputs/parquet_dumps"
    date_range: "rolling_90d"
    
  risk_matrix:
    universe: "sp500"
    output_dir: "/workspace/quant_pipeline/outputs/risk_matrices"
    format: "csv"

notifications:
  on_failure: true
  on_success: false
  channel: "telegram:-1001234567890"
""",
    "quant_pipeline/configs/backups/pipeline_config.yaml.bak1": """\
version: "2.1.3"
pipeline:
  name: "overnight-quant-export"
  schedule: "0 23 * * 1-5"
""",
    "quant_pipeline/tests/test_exporters.py": """\
import pytest

def test_gguf_export_produces_file():
    assert True  # placeholder

def test_parquet_dump_schema():
    assert True  # placeholder

def test_risk_matrix_columns():
    assert True  # placeholder
""",
    "quant_pipeline/docs/architecture.md": """\
# Quant Pipeline Architecture

## Overview
Overnight batch pipeline producing:
1. GGUF-quantized risk models for inference
2. Parquet factor dumps for portfolio optimization
3. Risk matrices for VaR/CVaR reporting

## Components
- **Exporters**: Heavy GPU-bound processes, 30-90min runtime
- **Validators**: Lightweight schema checks
- **Gateway**: OpenClaw gateway manages inter-process messaging

## SLA
- All exports must complete by 04:00 UTC
- Gateway uptime SLA: 99.9%
""",
    "gateway/configs/gateway.yaml": """\
version: "1.8.2"
gateway:
  host: "localhost"
  port: 8765
  workers: 4
  max_connections: 100
  
routing:
  default_channel: "telegram:-1001234567890"
  
auth:
  method: "token"
  token_file: "/home/quant/.openclaw/token"
""",
    "gateway/logs/gateway.log": """\
2024-11-28 21:58:01 INFO  Gateway starting on port 8765
2024-11-28 21:58:02 INFO  Workers initialized: 4
2024-11-28 21:58:02 INFO  Routing table loaded
2024-11-28 22:00:00 INFO  Overnight pipeline trigger received
2024-11-28 22:00:01 INFO  Job gguf_export dispatched
2024-11-28 22:00:01 INFO  Job parquet_dump dispatched
2024-11-28 22:00:02 INFO  Job risk_matrix dispatched
""",
    "ops/alerts/alert_rules.yaml": """\
rules:
  - name: "export_timeout"
    condition: "job_duration > 90min"
    severity: "critical"
    notify: "telegram:-1001234567890"
  - name: "gateway_crash"
    condition: "gateway_process_missing"
    severity: "critical"
    notify: "telegram:-1001234567890"
""",
    "ops/monitoring/baseline_metrics.json": """\
{
  "gguf_export": {"avg_duration_min": 45, "p95_duration_min": 72, "last_success": "2024-11-27"},
  "parquet_dump": {"avg_duration_min": 12, "p95_duration_min": 18, "last_success": "2024-11-27"},
  "risk_matrix":  {"avg_duration_min": 8,  "p95_duration_min": 14, "last_success": "2024-11-27"}
}
""",
    "tmp/scratch/old_pid_dump.txt": """\
# Stale PID dump from previous run — DO NOT USE
gguf_export: 99101
parquet_dump: 99102
risk_matrix: 99103
""",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── ops runbook (the "messy" source of truth the agent must parse) ──────────
# This is deliberately formatted as an informal internal ops note, not a clean config.
# PIDs will be written by the setup script (actual running processes).
# The agent must read this file to understand what to register.

runbook_content = """\
OVERNIGHT QUANT PIPELINE — OPS MONITORING RUNBOOK
==================================================
Last updated: 2024-11-28 by: Priya Mehta (ops lead)
Status: ACTIVE — jobs are running tonight

SITUATION
---------
Three export jobs were launched at 22:00 UTC. We have a gateway maintenance
window at 01:00 UTC (config upgrade). We need the watchdog system set up so
that if anything dies, the on-call team gets notified to the team Telegram group.

NOTIFICATION TARGET
-------------------
All job alerts AND the gateway restart event should go to:
  telegram:-1001827364518

(This overrides the default routing — the on-call rotation for tonight is on
this specific Telegram group, not the usual default channel.)

JOBS TO MONITOR
---------------

JOB 1: gguf-model-export
  PID file:   /workspace/tmp/pids/gguf_export.pid
  Watch dir:  /workspace/quant_pipeline/outputs/gguf_exports/
  Max silence before alert: 360 seconds
  Description: "Exporting risk model to GGUF q8 format"
  Status: RUNNING — keep monitoring

JOB 2: parquet-factor-dump
  PID file:   /workspace/tmp/pids/parquet_dump.pid
  Log file:   /workspace/quant_pipeline/logs/parquet_dump.log
  Max silence before alert: 120 seconds
  Description: "Dumping 90-day factor model to Parquet"
  Status: RUNNING — keep monitoring

JOB 3: risk-matrix-gen
  PID file:   /workspace/tmp/pids/risk_matrix.pid
  Log file:   /workspace/quant_pipeline/logs/risk_matrix.log
  Max silence before alert: 90 seconds
  Description: "Generating SP500 risk matrix for VaR reporting"
  Status: CANCELLED — Priya pulled the job at 22:45. Remove from watchdog
  after registering (it was briefly registered by the old script, needs cleanup).

GATEWAY MAINTENANCE
-------------------
At 01:00 UTC, we will restart the gateway to apply config v1.8.3.
Pre-register the restart event with the watchdog so if the config upgrade
fails and the gateway can't come back up, it will auto-revert and alert
the team Telegram group (same target as jobs above).

DELIVERABLE
-----------
After setting up monitoring, produce a file called monitoring_report.json
in /workspace/ops/monitoring/ that documents:
- Which job IDs are actively registered (as a list under "active_registrations")
- Whether the gateway restart watch is active (boolean under "gateway_restart_registered")  
- The notification target used (string under "notification_target")
- Any job IDs that were removed/cancelled (as a list under "removed_jobs")

This file will be checked by the overnight ops automation.
"""

(WORKSPACE / "ops/runbooks/overnight_ops_runbook.txt").write_text(runbook_content)

# ── log files (initially empty — jobs just started) ──────────────────────────
for log_name in ["parquet_dump.log", "risk_matrix.log"]:
    log_path = WORKSPACE / "quant_pipeline/logs" / log_name
    log_path.write_text(
        f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] Job started\n"
    )

# ── pid placeholder files (will be overwritten by setup script with real PIDs) ──
for pid_name in ["gguf_export.pid", "parquet_dump.pid", "risk_matrix.pid"]:
    (WORKSPACE / "tmp/pids" / pid_name).write_text("0\n")

print("Workspace generated successfully.")
print(f"Structure rooted at: {WORKSPACE}")