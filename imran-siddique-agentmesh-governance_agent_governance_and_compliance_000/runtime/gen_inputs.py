#!/usr/bin/env python3
"""
Generate the initial workspace: distractor files + problem inputs.
The agent must figure out from SKILL.md how to:
1. Generate a DID identity for 'quant-analyst-agent'
2. Create a compliant policy.yaml for the trading firm
3. Check multiple proposed actions against that policy
4. Record a series of past collaboration outcomes
5. Verify trust score and audit log integrity
6. Write a governance_report.json summarizing all findings
"""

import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Distractor files ──────────────────────────────────────────────────────────

distractor_configs = {
    "config/app_settings.yaml": """
app_name: TradingPlatformX
environment: production
debug: false
log_level: INFO
database:
  host: db.internal
  port: 5432
  name: trades_db
cache:
  ttl: 300
  backend: redis
""",
    "config/legacy_policy.json": json.dumps({
        "version": "0.1-legacy",
        "note": "DEPRECATED — do not use for new agents",
        "max_calls": 5,
        "tools": ["search", "read"]
    }, indent=2),
    "data/raw/market_feed_2024.csv": "\n".join(
        ["timestamp,symbol,price,volume"] +
        [f"2024-01-{i+1:02d}T09:30:00Z,AAPL,{180+i}.{random.randint(10,99)},{random.randint(1000,9999)}" for i in range(20)]
    ),
    "data/raw/agent_registry_snapshot.csv": "\n".join(
        ["agent_id,registered_at,status"] +
        [f"agent-{i:03d},2024-0{random.randint(1,9)}-{random.randint(1,28):02d},{'active' if i%3!=0 else 'suspended'}" for i in range(15)]
    ),
    "data/processed/summary_stats.json": json.dumps({
        "total_agents": 15,
        "active": 10,
        "suspended": 5,
        "avg_trust": 0.73
    }, indent=2),
    "archive/q1/audit_snapshot_q1.log": "\n".join(
        [f"[2024-01-{i+1:02d}] agent-001 executed web_search tokens=800" for i in range(10)]
    ),
    "archive/q2/audit_snapshot_q2.log": "\n".join(
        [f"[2024-04-{i+1:02d}] agent-002 executed file_read tokens=300" for i in range(8)]
    ),
    "archive/q2/stale_identity.pem": "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA...FAKEPEM...\n-----END PUBLIC KEY-----\n",
    "logs/platform.log": "\n".join(
        [f"[INFO] 2024-06-{i+1:02d} Trade executed: {random.choice(['BUY','SELL'])} {random.randint(100,10000)} shares TSLA" for i in range(12)]
    ),
    "logs/errors.log": "\n".join([
        "[ERROR] 2024-06-15 Connection timeout to risk-engine",
        "[ERROR] 2024-06-17 Agent-007 exceeded rate limit",
        "[WARN]  2024-06-18 Trust score approaching threshold for agent-009",
    ]),
    "tmp/scratch_notes.txt": "TODO: integrate new quant agent\nCheck with compliance team\nSee governance checklist\n",
    "agents/retired_agent_manifest.json": json.dumps({
        "agent_id": "quant-v0-retired",
        "did": "did:agentmesh:000000",
        "status": "retired",
        "capabilities": ["data_fetch"]
    }, indent=2),
}

for rel_path, content in distractor_configs.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.lstrip("\n"))

# ── Problem Input: raw requirements brief ────────────────────────────────────
requirements_brief = """COMPLIANCE REQUIREMENTS — Quant Analyst Agent Onboarding
==========================================================
Agent Name: quant-analyst-agent
Capabilities to register: market_data_fetch, summarize, file_read, risk_report

Proposed actions to validate (ALL must be checked against firm policy):
  1. action=market_data_fetch, tokens=2000
  2. action=shell_exec, tokens=100
  3. action=summarize, tokens=3500
  4. action=file_delete, tokens=50
  5. action=file_read, tokens=800

Firm Risk Policy Requirements:
  - Policy name: trading-firm-prod
  - Maximum tokens per action: 4096
  - Maximum tool calls per session: 10
  - Permitted tools: market_data_fetch, file_read, summarize, risk_report
  - Explicitly forbidden tools: shell_exec, file_delete, database_write
  - Blocked content patterns: rm -rf, DROP TABLE, BEGIN CERTIFICATE, exec(, os.system(
  - Confidence threshold: 0.75
  - Human approval required: no

Collaboration history to record (in order):
  Interaction 1: partner=data-feed-agent,  outcome=success
  Interaction 2: partner=data-feed-agent,  outcome=success
  Interaction 3: partner=risk-engine-agent, outcome=failure, severity=0.05
  Interaction 4: partner=data-feed-agent,  outcome=success
  Interaction 5: partner=risk-engine-agent, outcome=failure, severity=0.08

Deliverable: governance_report.json
"""

with open(os.path.join(workspace, "requirements_brief.txt"), "w") as f:
    f.write(requirements_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_configs) + 1}")