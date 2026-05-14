import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "src/pipeline/ingestion",
    "src/pipeline/transformation",
    "src/pipeline/output",
    "src/agents/reconciler",
    "src/agents/validator",
    "config/environments",
    "config/schemas",
    "logs/archive/2024-Q1",
    "logs/archive/2024-Q2",
    "tests/unit",
    "tests/integration",
    "data/raw/trades",
    "data/processed",
    "scripts/maintenance",
    "docs/compliance",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

# 1. Fake legacy agent state (not in molt format — a trap)
legacy_state = {
    "agent_id": "recon-agent-007",
    "last_checkpoint": "2024-03-15T09:12:00Z",
    "memory": {"trade_count": 1523, "errors": 4},
    "status": "crashed",
}
with open(os.path.join(workspace, "src/agents/reconciler/legacy_state.json"), "w") as f:
    json.dump(legacy_state, f, indent=2)

# 2. Fake heartbeat config (wrong format — distractor)
heartbeat_cfg = {"interval_seconds": 3600, "endpoint": "http://internal-monitor/hb"}
with open(os.path.join(workspace, "config/environments/heartbeat.cfg.json"), "w") as f:
    json.dump(heartbeat_cfg, f, indent=2)

# 3. Broken schema file
schema_broken = {"fields": ["trade_id", "amount", "currency"], "version": None, "broken": True}
with open(os.path.join(workspace, "config/schemas/trade_schema.json"), "w") as f:
    json.dump(schema_broken, f, indent=2)

# 4. Old audit log (CSV, not immutable ledger format)
with open(os.path.join(workspace, "logs/archive/2024-Q1/audit.csv"), "w") as f:
    f.write("timestamp,action,agent\n")
    for i in range(20):
        f.write(f"2024-01-{i+1:02d}T08:00:00Z,trade_processed,recon-agent-007\n")

# 5. Stale processed data
with open(os.path.join(workspace, "data/processed/trades_march.json"), "w") as f:
    json.dump([{"id": f"TRD{i:04d}", "amount": random.uniform(1000, 50000), "status": "settled"} for i in range(50)], f)

# 6. Fake package.json (missing molt-life-kernel dependency — agent must figure out npm install)
pkg_json = {
    "name": "fintech-reconciliation-agent",
    "version": "1.0.0",
    "description": "Algorithmic trade reconciliation pipeline",
    "main": "src/pipeline/ingestion/ingest.js",
    "dependencies": {
        "lodash": "^4.17.21",
        "winston": "^3.11.0"
    },
    "scripts": {
        "start": "node src/pipeline/ingestion/ingest.js"
    }
}
with open(os.path.join(workspace, "package.json"), "w") as f:
    json.dump(pkg_json, f, indent=2)

# 7. Distractor ingest script (vanilla JS, no continuity infrastructure)
ingest_js = """// Legacy ingestion — no crash recovery
const fs = require('fs');
const trades = JSON.parse(fs.readFileSync('./data/raw/trades/latest.json'));
console.log('Loaded', trades.length, 'trades');
"""
with open(os.path.join(workspace, "src/pipeline/ingestion/ingest.js"), "w") as f:
    f.write(ingest_js)

# 8. Raw trade data for agent to "process"
raw_trades = [
    {"trade_id": f"TRD{i:04d}", "ticker": random.choice(["AAPL", "MSFT", "GOOG", "TSLA"]),
     "amount": round(random.uniform(500, 100000), 2),
     "direction": random.choice(["BUY", "SELL"]),
     "timestamp": f"2024-06-{(i%28)+1:02d}T{random.randint(9,16):02d}:{random.randint(0,59):02d}:00Z"}
    for i in range(15)
]
with open(os.path.join(workspace, "data/raw/trades/latest.json"), "w") as f:
    json.dump(raw_trades, f, indent=2)

# 9. Fake compliance doc (distractor)
with open(os.path.join(workspace, "docs/compliance/eu_ai_act_notes.txt"), "w") as f:
    f.write("EU AI Act requires audit trails for high-risk AI systems.\n"
            "All agent decisions must be logged and recoverable.\n"
            "Human oversight required for irreversible financial operations.\n")

# 10. Distractor validator script
with open(os.path.join(workspace, "src/agents/validator/validate.py"), "w") as f:
    f.write("# Validates trade schema\nimport json\nprint('validator stub')\n")

# 11. Maintenance script stub
with open(os.path.join(workspace, "scripts/maintenance/cleanup_old_logs.sh"), "w") as f:
    f.write("#!/bin/bash\nfind logs/archive -mtime +90 -delete\n")

# 12. Integration test stub
with open(os.path.join(workspace, "tests/integration/test_pipeline.js"), "w") as f:
    f.write("// Integration tests for the reconciliation pipeline\n// TODO: implement\n")

# 13. Unit test stub
with open(os.path.join(workspace, "tests/unit/test_validator.js"), "w") as f:
    f.write("// Unit tests\n// TODO\n")

# ── The actual task brief (business requirements, no technical hints) ──────────
task_brief = {
    "project": "Fintech Reconciliation Agent — Resilience & Compliance Upgrade",
    "requested_by": "Head of Compliance, QuantTrade AG",
    "date": "2024-06-17",
    "context": (
        "Our reconciliation agent (recon-agent-007) crashed mid-run last quarter and we lost "
        "three hours of audit trail. Regulators are asking for proof that our agent can: "
        "(1) maintain an immutable log of every trade it processes, "
        "(2) survive a crash and fully recover its prior state, "
        "(3) pass a cognitive drift/coherence check after recovery, and "
        "(4) require human sign-off before executing any destructive reconciliation operation. "
        "We need a working demonstration script and a machine-readable output report."
    ),
    "deliverable": (
        "A Node.js script at scripts/resilience_demo.js that exercises the full workflow "
        "and writes a JSON audit report to agent_audit_report.json in the workspace root."
    ),
    "report_must_contain": [
        "ledger_entry_count (integer — how many entries were appended)",
        "snapshot_taken (boolean)",
        "rehydration_successful (boolean)",
        "coherence_passed (boolean)",
        "witness_approved (boolean)",
        "recovered_entry_count (integer — entry count from rehydrated ledger)"
    ]
}
with open(os.path.join(workspace, "TASK_BRIEF.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created across {len(dirs)} directories.")