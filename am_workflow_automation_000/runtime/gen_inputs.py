#!/usr/bin/env python3
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deeply nested distractor directory structure ---
dirs = [
    "pipeline/ingestion/raw",
    "pipeline/ingestion/staging",
    "pipeline/analysis/models",
    "pipeline/analysis/outputs",
    "pipeline/coordination/logs",
    "pipeline/coordination/archive",
    "agents/analyst/config",
    "agents/analyst/outputs",
    "agents/coordinator/config",
    "agents/coordinator/state",
    "infra/relays/configs",
    "infra/monitoring",
    "reports/daily",
    "reports/weekly",
    "scripts/utils",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "pipeline/ingestion/raw/sample_data_001.jsonl": '\n'.join([
        json.dumps({"id": i, "value": random.random(), "tag": f"record_{i}"})
        for i in range(20)
    ]),
    "pipeline/ingestion/staging/manifest.json": json.dumps({
        "version": "1.2.0",
        "batch_id": "b-20240101",
        "records": 20,
        "status": "pending"
    }, indent=2),
    "pipeline/analysis/models/model_registry.json": json.dumps({
        "models": [
            {"name": "gpt-4o-mini", "version": "2024-07-18", "endpoint": "internal"},
            {"name": "llama-3-70b", "version": "2024-04", "endpoint": "local"}
        ]
    }, indent=2),
    "pipeline/analysis/outputs/run_20240610.csv": "id,score,label\n1,0.91,positive\n2,0.43,negative\n3,0.77,positive\n",
    "pipeline/coordination/logs/dispatch_log.txt": "\n".join([
        f"2024-06-{10+i:02d} 09:00:00 INFO dispatched task {1000+i} to agent-pool"
        for i in range(5)
    ]),
    "pipeline/coordination/archive/old_config.toml": "[relay]\nurls = [\"wss://deprecated.relay.io\"]\n\n[identity]\ndefault = \"legacy\"\n",
    "agents/analyst/config/params.yaml": "model: llama-3-70b\ntemperature: 0.3\nmax_tokens: 2048\n",
    "agents/analyst/outputs/analysis_result_20240610.json": json.dumps({
        "task_id": "t-9001",
        "status": "completed",
        "findings": ["anomaly at offset 42", "pattern detected in cluster 7"]
    }, indent=2),
    "agents/coordinator/config/routing_table.json": json.dumps({
        "routes": [
            {"agent": "analyst-1", "topic": "data-analysis"},
            {"agent": "analyst-2", "topic": "pattern-recognition"}
        ]
    }, indent=2),
    "agents/coordinator/state/last_heartbeat.txt": "1717027200\n",
    "infra/relays/configs/relay_notes.txt": "# Relay endpoints under evaluation\n# wss://relay.damus.io - stable\n# wss://nos.lol - fast\n# wss://relay.nostr.band - good uptime\n",
    "infra/monitoring/alert_rules.json": json.dumps({
        "rules": [
            {"metric": "message_latency_ms", "threshold": 500, "action": "page"},
            {"metric": "relay_failures", "threshold": 3, "action": "failover"}
        ]
    }, indent=2),
    "reports/daily/report_20240610.md": "# Daily Report\n- Tasks dispatched: 12\n- Tasks completed: 10\n- Pending: 2\n",
    "reports/weekly/summary_week24.md": "# Week 24 Summary\n- Throughput: 85 tasks\n- SLA compliance: 98.2%\n",
    "scripts/utils/health_check.sh": "#!/bin/bash\necho 'checking services...'\n",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# --- The actual task context file ---
# Partner agent's public address that the coordinator must send to
partner_npub = "npub1qqqqxyz9partner0000000000000000000000000000000000000000000099"

task_brief = {
    "mission": "Secure Multi-Agent Research Pipeline Coordination",
    "description": (
        "Set up two communication identities for this agent node: "
        "'analyst' (for data analysis tasks) and 'coordinator' (for inter-agent orchestration). "
        "The coordinator identity must become the default. "
        "Register two relay endpoints for message delivery resilience. "
        "Then, using the coordinator identity, forward the structured analysis task below to the partner agent. "
        "Finally, collect the last 5 incoming task responses and save their content payloads to task_responses.json."
    ),
    "partner_agent_address": partner_npub,
    "analysis_task_payload": {
        "task_id": "t-9001",
        "type": "pattern_analysis",
        "target_dataset": "pipeline/ingestion/raw/sample_data_001.jsonl",
        "priority": "high",
        "requester": "coordinator"
    },
    "relay_endpoints": [
        "wss://relay.damus.io",
        "wss://nos.lol"
    ]
}

(workspace / "mission_brief.json").write_text(json.dumps(task_brief, indent=2))

print("Workspace generated successfully.")
print(f"Partner npub: {partner_npub}")