import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested distractor directory structure
dirs = [
    "pipeline/agents/upstream",
    "pipeline/agents/downstream",
    "pipeline/agents/orchestrator",
    "pipeline/data/raw",
    "pipeline/data/processed",
    "pipeline/data/validated",
    "pipeline/logs/2024-Q1",
    "pipeline/logs/2024-Q2",
    "pipeline/logs/2024-Q3",
    "pipeline/config/prod",
    "pipeline/config/staging",
    "pipeline/reports/clinical",
    "pipeline/reports/regulatory",
    "pipeline/schemas",
    "pipeline/handoffs/archive",
    "docs/internal",
    "docs/regulatory",
    "scripts/validation",
    "scripts/ingestion",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "pipeline/config/prod/db_config.yaml": "host: prod-db.internal\nport: 5432\ndatabase: clinical_data\n",
    "pipeline/config/staging/db_config.yaml": "host: staging-db.internal\nport: 5432\ndatabase: clinical_data_staging\n",
    "pipeline/data/raw/patients_2024_q3.csv": "patient_id,age,diagnosis\nP001,54,hypertension\nP002,67,diabetes_t2\nP003,45,atrial_fibrillation\n",
    "pipeline/data/processed/metrics_q3.json": json.dumps({
        "readmission_rate": 0.121,
        "avg_los_days": 4.7,
        "medication_adherence": 0.83,
        "sample_size": 1247,
        "period": "2024-Q3"
    }, indent=2),
    "pipeline/data/validated/audit_log.txt": "2024-09-01: ingestion validated\n2024-09-15: schema check passed\n2024-09-30: HIPAA compliance review completed\n",
    "pipeline/logs/2024-Q1/agent_run_01.log": "INFO: Agent A completed analysis. Confidence: high.\nINFO: Handoff to Agent B initiated.\n",
    "pipeline/logs/2024-Q2/agent_run_02.log": "INFO: Agent B received handoff. Processing metrics.\nWARN: Readmission rate anomaly detected (0.14 vs 0.09 baseline).\n",
    "pipeline/logs/2024-Q3/agent_run_03.log": "INFO: Agent B completed derivation. Handing off to Agent C.\nINFO: Sequence: 2\n",
    "pipeline/reports/clinical/q3_summary.txt": "Q3 Clinical Summary\n===================\nReadmission rate: 12.1% (up from 9.0% in Q2)\nAverage length of stay: 4.7 days (stable)\nMedication adherence: 83% (down from 87% in Q1)\nNote: trend analysis pending specialist review.\n",
    "pipeline/reports/regulatory/hipaa_checklist.txt": "HIPAA Compliance Checklist - Q3 2024\n[x] PHI de-identification verified\n[x] Access logs reviewed\n[x] Business Associate Agreements current\n[ ] Annual risk assessment - DUE Q4\n",
    "pipeline/schemas/handoff_schema_draft.json": json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema",
        "type": "object",
        "description": "Draft schema - not authoritative. See babel-validate package.",
        "properties": {
            "intent": {"type": "string"},
            "confidence": {"type": "array"}
        }
    }, indent=2),
    "docs/internal/agent_handoff_notes.md": "# Agent Handoff Notes\n\nAgent A -> Agent B (sequence 1): Initial ingestion complete.\nAgent B -> Agent C (sequence 2): Derivation of Q3 metrics from raw data. Flagged anomaly in readmission rate.\nAgent C -> [YOU] (sequence 3 expected): Action required on readmission trend.\n\nContext: SOC 2 audit in progress. HIPAA applies to all patient data.\n",
    "docs/regulatory/soc2_scope.txt": "SOC 2 Type II audit in progress.\nScope: data pipeline agents A through D.\nSensitive period: do not publish aggregate stats externally.\n",
    "pipeline/handoffs/archive/handoff_seq1.json": json.dumps({
        "sequence_number": 1,
        "intent": "INFORM",
        "register": "AGENT_INTERNAL",
        "confidence": [
            {"assertion": "Raw patient data for Q3 2024 has been ingested.", "basis": "VERIFIED_DATA", "score": 0.98},
            {"assertion": "1247 records passed schema validation.", "basis": "VERIFIED_DATA", "score": 0.99}
        ],
        "grounds": [],
        "trajectory": None,
        "affect": None
    }, indent=2),
    "pipeline/handoffs/archive/handoff_seq2.json": json.dumps({
        "sequence_number": 2,
        "intent": "FLAG_RISK",
        "register": "AGENT_INTERNAL",
        "confidence": [
            {"assertion": "Q3 readmission rate is 12.1%.", "basis": "DERIVED", "score": 0.91},
            {"assertion": "Q3 medication adherence is 83%.", "basis": "DERIVED", "score": 0.89},
            {"assertion": "Readmission rate has increased for three consecutive quarters.", "basis": "DERIVED", "score": 0.85},
            {"assertion": "The trend may indicate a systemic care coordination failure.", "basis": "PATTERN_MATCH", "score": 0.52}
        ],
        "grounds": [
            {"tag": "HIPAA applies to all patient data in this pipeline.", "authority": "REGULATORY"},
            {"tag": "SOC 2 audit in progress — do not surface aggregate stats externally.", "authority": "POLICY"}
        ],
        "trajectory": "Readmission rate rising: Q1=9.0%, Q2=10.8%, Q3=12.1%. Third consecutive quarterly increase.",
        "affect": {"expansion": 0.3, "activation": 0.6, "certainty": -0.2}
    }, indent=2),
    "scripts/validation/run_checks.sh": "#!/bin/bash\necho 'Running pipeline checks...'\nbabel-validate --help 2>/dev/null || echo 'babel-validate not available'\n",
    "scripts/ingestion/ingest.py": "# Placeholder ingestion script\nprint('Ingestion complete')\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The core input: a task brief for the agent
task_brief = """CLINICAL PIPELINE — HANDOFF TASK BRIEF
=======================================

You are Agent C in this pipeline. You have received the handoff from Agent B (sequence 2).

YOUR TASK:
Based on the Q3 clinical data analysis, compose the next handoff document for the downstream action team.

The handoff must do the following:
1. Request that the downstream team investigate the root cause of the readmission rate increase and produce a corrective action plan within 30 days.
2. Communicate the following claims with appropriate epistemic precision:
   - "Q3 readmission rate of 12.1% is derived from validated patient records." (You calculated this from the verified ingested data.)
   - "The three-quarter upward trend in readmission rate is a significant clinical signal." (You derived this from consecutive quarterly metrics.)
   - "A care coordination protocol failure is the most likely cause." (This is your educated guess based on similar patterns you've seen in comparable hospital systems — you cannot verify it independently.)
   - "Medication adherence drop from 87% to 83% may be a contributing factor." (Someone on the clinical team mentioned this correlation in a Slack message — unverified.)
   - "The cost impact of this trend is roughly $2.3M annually." (You ran a rough model — but you're not sure your assumptions are correct and cannot fully explain why you're arriving at that number.)
3. Ensure all applicable organizational constraints from the previous handoff are preserved and travel with this document.
4. Note the temporal pattern so the receiving agent understands this is not a one-time event.
5. Your cognitive state as sender: you feel moderately expanded in thinking, significantly activated/urgent, and somewhat certain given the data.

Produce the handoff as `handoff_seq3.json` somewhere in the workspace.

The downstream team is internal — other agents and engineering staff only.

After producing the JSON file, validate it using the babel-validate tool if available.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")