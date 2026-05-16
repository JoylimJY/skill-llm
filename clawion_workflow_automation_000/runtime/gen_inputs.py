import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep distractor directory structure ---
distractor_dirs = [
    "biotech_pipeline/raw_data/batch_001",
    "biotech_pipeline/raw_data/batch_002",
    "biotech_pipeline/qc_reports/2024_Q1",
    "biotech_pipeline/qc_reports/2024_Q2",
    "biotech_pipeline/ingestion/logs",
    "biotech_pipeline/ingestion/config",
    "biotech_pipeline/validation/schemas",
    "biotech_pipeline/validation/results",
    "biotech_pipeline/docs/protocols",
    "biotech_pipeline/docs/sops",
    "biotech_pipeline/archive/deprecated",
    "infra/monitoring",
    "infra/alerting",
    "infra/scripts",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "biotech_pipeline/raw_data/batch_001/samples.csv": "sample_id,patient_id,timestamp\nS001,P001,2024-01-10\nS002,P002,2024-01-11\n",
    "biotech_pipeline/raw_data/batch_002/samples.csv": "sample_id,patient_id,timestamp\nS003,P003,2024-02-01\n",
    "biotech_pipeline/qc_reports/2024_Q1/summary.txt": "QC pass rate: 94.2%\nFailed samples: 3\n",
    "biotech_pipeline/qc_reports/2024_Q2/summary.txt": "QC pass rate: 97.8%\nFailed samples: 1\n",
    "biotech_pipeline/ingestion/logs/ingest_20240101.log": "[INFO] Ingestion started\n[INFO] 120 records processed\n[INFO] Ingestion complete\n",
    "biotech_pipeline/ingestion/config/db_config.json": json.dumps({"host": "localhost", "port": 5432, "db": "biotech_staging"}),
    "biotech_pipeline/validation/schemas/sample_schema.json": json.dumps({"type": "object", "properties": {"sample_id": {"type": "string"}}}),
    "biotech_pipeline/validation/results/batch_001_result.json": json.dumps({"batch": "001", "passed": True, "errors": []}),
    "biotech_pipeline/docs/protocols/ingestion_sop_v2.md": "# Ingestion SOP\n\n## Step 1\nRun the ingestion pipeline daily at 06:00 UTC.\n\n## Step 2\nVerify record counts match source.\n",
    "biotech_pipeline/docs/sops/qc_checklist.md": "- [ ] Check null values\n- [ ] Verify patient IDs\n- [ ] Confirm timestamp format\n",
    "biotech_pipeline/archive/deprecated/old_pipeline.py": "# DEPRECATED - do not use\nimport sys\nprint('old pipeline')\n",
    "infra/monitoring/alerts.yaml": "alerts:\n  - name: ingestion_failure\n    threshold: 0\n",
    "infra/alerting/pagerduty_config.json": json.dumps({"service_key": "REDACTED", "enabled": False}),
    "infra/scripts/health_check.sh": "#!/bin/bash\necho 'All systems nominal'\n",
    "biotech_pipeline/ingestion/config/retry_policy.json": json.dumps({"max_retries": 3, "backoff_seconds": 30}),
}

for rel_path, content in distractor_files.items():
    target = workspace / rel_path
    target.write_text(content)

# --- Mission specification brief (non-technical, business context) ---
# This tells the agent what they need to set up, without giving CLI hints.
brief = {
    "mission": {
        "id": "trial-data-pipeline",
        "name": "Clinical Trial Data Pipeline Coordination"
    },
    "agents": [
        {
            "id": "mgr-coord-01",
            "name": "Pipeline Coordinator",
            "role": "manager",
            "description": "Oversees the clinical trial data pipeline mission, dispatches tasks to workers, and maintains the task board."
        },
        {
            "id": "wkr-ingest-02",
            "name": "Data Ingestion Agent",
            "role": "worker",
            "description": "Responsible for pulling raw trial data from source systems and staging it for QC."
        },
        {
            "id": "wkr-qc-03",
            "name": "QC Validation Agent",
            "role": "worker",
            "description": "Runs quality control checks on staged data and flags anomalies for human review."
        }
    ],
    "tasks": [
        {
            "id": "task-ingest-001",
            "title": "Ingest Batch 003 Raw Data",
            "description": "Pull raw trial data for Batch 003 from the source CSV exports and load into the staging database.",
            "assigned_to": "wkr-ingest-02"
        },
        {
            "id": "task-qc-001",
            "title": "Validate Batch 003 QC Schema",
            "description": "Run the schema validation suite on staged Batch 003 data and produce a QC results report.",
            "assigned_to": "wkr-qc-03"
        }
    ],
    "roadmap": "## Phase 1: Data Ingestion\nIngest all pending batch data into the staging database.\n\n## Phase 2: QC Validation\nRun automated QC checks and escalate failures to human reviewers.\n\n## Phase 3: Approval Gate\nObtain sign-off from clinical data manager before promoting to production.",
    "cron_interval_minutes": 15
}

(workspace / "mission_brief.json").write_text(json.dumps(brief, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")