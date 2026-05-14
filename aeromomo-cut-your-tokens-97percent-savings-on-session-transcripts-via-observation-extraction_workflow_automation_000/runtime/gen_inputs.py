#!/usr/bin/env python3
"""
Generate a realistic fintech AI-agent workspace with messy session transcripts,
verbose memory files, and distractor files. The agent must run claw-compactor
observe → dict → tiers pipeline on this workspace.
"""

import os
import json
import random
import string
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/agent-workspace")

# --- Directory structure ---
dirs = [
    WORKSPACE / "memory",
    WORKSPACE / "memory" / "sessions",
    WORKSPACE / "memory" / "observations",
    WORKSPACE / "docs",
    WORKSPACE / "docs" / "api",
    WORKSPACE / "docs" / "internal",
    WORKSPACE / "src",
    WORKSPACE / "src" / "agents",
    WORKSPACE / "src" / "utils",
    WORKSPACE / "logs",
    WORKSPACE / "reports",
    WORKSPACE / "config",
    WORKSPACE / "archive",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────

(WORKSPACE / "docs" / "api" / "payment_api.md").write_text("""# Payment API v3
## Endpoints
- POST /v3/transfer
- GET /v3/balance/{account_id}
- DELETE /v3/mandate/{id}
## Auth
Bearer token required. Rate limit: 100 req/min.
""")

(WORKSPACE / "docs" / "internal" / "compliance_notes.md").write_text("""# Compliance Notes Q3
- KYC refresh cycle: 180 days
- AML threshold updated to £10,000
- GDPR data retention: 7 years for transaction logs
- PCI-DSS scope confirmed for card vault
""")

(WORKSPACE / "docs" / "internal" / "team_charter.md").write_text("""# Agent Team Charter
We operate three autonomous agents: Reconciler, Fraud-Sentinel, and ReportBot.
Each agent writes session transcripts to memory/sessions/ after every run.
""")

(WORKSPACE / "src" / "agents" / "reconciler.py").write_text("""# reconciler.py
class ReconcilerAgent:
    def run(self, ledger_path):
        # TODO: implement
        pass
""")

(WORKSPACE / "src" / "agents" / "fraud_sentinel.py").write_text("""# fraud_sentinel.py
class FraudSentinel:
    def scan(self, transaction_batch):
        pass
""")

(WORKSPACE / "src" / "utils" / "token_counter.py").write_text("""def count_tokens(text: str, chars_per_token: float = 4.0) -> int:
    return int(len(text) / chars_per_token)
""")

(WORKSPACE / "logs" / "system.log").write_text("""2024-01-15 03:00:01 INFO  cron: heartbeat triggered
2024-01-15 03:00:02 INFO  reconciler: starting daily run
2024-01-15 03:00:45 INFO  reconciler: processed 4821 transactions
2024-01-15 03:01:10 WARN  fraud_sentinel: latency spike 2.3s
2024-01-15 03:02:00 INFO  heartbeat: complete
""")

(WORKSPACE / "reports" / "weekly_cost_report.md").write_text("""# Weekly Token Cost Report — Week 3 Jan 2024
| Agent | Sessions | Total Tokens | Cost (USD) |
|---|---|---|---|
| Reconciler | 7 | 142,000 | $4.26 |
| FraudSentinel | 14 | 287,000 | $8.61 |
| ReportBot | 3 | 61,000 | $1.83 |
**Total: $14.70 — 23% over budget**
""")

(WORKSPACE / "config" / "agent_routing.json").write_text(json.dumps({
    "routing": {
        "reconciler": {"model": "gpt-4o", "max_tokens": 4096},
        "fraud_sentinel": {"model": "gpt-4o-mini", "max_tokens": 8192},
        "report_bot": {"model": "gpt-4o", "max_tokens": 2048}
    }
}, indent=2))

(WORKSPACE / "archive" / "old_memory_backup.md").write_text("""# MEMORY BACKUP — 2023-12-01
## Decisions
- Switched from rule-based to ML fraud detection
- Deprecated v1 reconciler
## Open Items
- None
""")

(WORKSPACE / "src" / "utils" / "ledger_parser.py").write_text("""def parse_csv_ledger(path):
    import csv
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows
""")

# ── MAIN MEMORY FILE ──────────────────────────────────────────────────────────
# Verbose, repetitive memory file — good compression target

MEMORY_MD = """# Agent Team Memory

## Overview
This document contains the working memory for the autonomous agent team at FinCore Ltd.
The team consists of three agents: Reconciler, Fraud-Sentinel, and ReportBot.
This document contains the working memory for the autonomous agent team at FinCore Ltd.

## Key Decisions

### Decision: Adopt ML-Based Fraud Scoring (2024-01-10)
After extensive evaluation, the team decided to adopt ML-based fraud scoring.
The previous rule-based system had a false positive rate of 12%.
After extensive evaluation, the team decided to adopt ML-based fraud scoring.
The ML model reduced false positives to 2.1%.
The model is deployed at /opt/models/fraud_scorer_v2.pkl.
The model is deployed at /opt/models/fraud_scorer_v2.pkl.

### Decision: Daily Reconciliation Window (2024-01-11)
The reconciliation window is set to run between 03:00 and 04:00 UTC daily.
This window was chosen to minimise overlap with peak transaction times.
The reconciliation window is set to run between 03:00 and 04:00 UTC daily.

### Decision: Token Budget Enforcement (2024-01-12)
A hard token budget of $12.00/week per agent cluster was enforced.
Overspend triggers an automated alert to the infrastructure Slack channel.
A hard token budget of $12.00/week per agent cluster was enforced.

## Architecture Notes

The agent memory system uses a shared markdown file (this file) as primary context.
Sub-agents load this file at the start of each session to restore context.
The agent memory system uses a shared markdown file (this file) as primary context.
Session transcripts are stored as JSONL files in memory/sessions/.
Session transcripts are stored as JSONL files in memory/sessions/.

## Open Items
- [ ] Migrate fraud_sentinel to dedicated GPU instance
- [ ] Implement cross-agent deduplication
- [ ] Review PCI-DSS scope for card tokenisation service
- [ ] Migrate fraud_sentinel to dedicated GPU instance

## Glossary
- **REC**: Reconciler Agent
- **FS**: Fraud-Sentinel Agent
- **RB**: ReportBot Agent
- **TXN**: Transaction
- **AML**: Anti-Money Laundering
- **KYC**: Know Your Customer
- **PCI-DSS**: Payment Card Industry Data Security Standard
- **REC**: Reconciler Agent
- **FS**: Fraud-Sentinel Agent
"""

(WORKSPACE / "memory" / "MEMORY.md").write_text(MEMORY_MD)

# ── SESSION TRANSCRIPTS (JSONL) ───────────────────────────────────────────────
# Realistic agent session transcripts in JSONL format

def make_observation(role, content):
    return {"role": role, "content": content}

sessions = {
    "session-reconciler-2024-01-13.jsonl": [
        {"type": "session_start", "agent": "reconciler", "timestamp": "2024-01-13T03:00:00Z"},
        {"type": "observation", "role": "user", "content": "Run daily reconciliation for 2024-01-13. Ledger file at /data/ledger_20240113.csv. Expected transaction count: 5102."},
        {"type": "observation", "role": "assistant", "content": "Loading ledger file from /data/ledger_20240113.csv. Parsing CSV with 5102 rows. Beginning balance check against settlement records."},
        {"type": "tool_use", "tool": "read_file", "input": {"path": "/data/ledger_20240113.csv"}, "output": "5102 rows loaded successfully."},
        {"type": "observation", "role": "assistant", "content": "Ledger loaded. Running balance reconciliation algorithm. Checking for missing settlements."},
        {"type": "tool_use", "tool": "run_reconciliation", "input": {"ledger_rows": 5102}, "output": {"matched": 5099, "unmatched": 3, "total_discrepancy_gbp": 147.23}},
        {"type": "observation", "role": "assistant", "content": "Reconciliation complete. 3 unmatched transactions found. Total discrepancy: £147.23. Flagging for manual review."},
        {"type": "tool_use", "tool": "write_report", "input": {"path": "/reports/recon_20240113.json"}, "output": "Report written successfully."},
        {"type": "observation", "role": "assistant", "content": "Report saved to /reports/recon_20240113.json. Sending alert to #reconciliation-alerts Slack channel."},
        {"type": "tool_use", "tool": "send_slack", "input": {"channel": "#reconciliation-alerts", "message": "Recon complete: 3 unmatched, £147.23 discrepancy."}, "output": "Message sent."},
        {"type": "observation", "role": "assistant", "content": "Daily reconciliation for 2024-01-13 complete. 3 items require manual review."},
        {"type": "session_end", "timestamp": "2024-01-13T03:04:22Z", "tokens_used": 8421},
    ],
    "session-fraud-sentinel-2024-01-13.jsonl": [
        {"type": "session_start", "agent": "fraud_sentinel", "timestamp": "2024-01-13T06:00:00Z"},
        {"type": "observation", "role": "user", "content": "Scan today's transaction batch for fraud. Batch path: /data/txn_batch_20240113.parquet. Use model v2."},
        {"type": "observation", "role": "assistant", "content": "Loading transaction batch from /data/txn_batch_20240113.parquet. Initialising fraud_scorer_v2 model from /opt/models/fraud_scorer_v2.pkl."},
        {"type": "tool_use", "tool": "load_model", "input": {"path": "/opt/models/fraud_scorer_v2.pkl"}, "output": "Model loaded. Version: 2.1.3. Feature count: 47."},
        {"type": "observation", "role": "assistant", "content": "Model loaded successfully. Scoring 14,203 transactions against fraud features."},
        {"type": "tool_use", "tool": "score_batch", "input": {"batch_size": 14203}, "output": {"high_risk": 12, "medium_risk": 89, "low_risk": 14102}},
        {"type": "observation", "role": "assistant", "content": "Scoring complete. 12 high-risk transactions identified. Escalating to compliance team."},
        {"type": "tool_use", "tool": "escalate_cases", "input": {"case_ids": ["TXN-9921", "TXN-9934", "TXN-9978", "TXN-10001", "TXN-10034", "TXN-10056", "TXN-10099", "TXN-10103", "TXN-10141", "TXN-10188", "TXN-10201", "TXN-10244"]}, "output": "12 cases escalated."},
        {"type": "observation", "role": "assistant", "content": "All 12 cases escalated to compliance. Generating summary report."},
        {"type": "tool_use", "tool": "write_report", "input": {"path": "/reports/fraud_20240113.json"}, "output": "Report written."},
        {"type": "observation", "role": "assistant", "content": "Fraud scan for 2024-01-13 complete. 12 high-risk cases escalated."},
        {"type": "session_end", "timestamp": "2024-01-13T06:11:44Z", "tokens_used": 11203},
    ],
    "session-reportbot-2024-01-14.jsonl": [
        {"type": "session_start", "agent": "report_bot", "timestamp": "2024-01-14T08:00:00Z"},
        {"type": "observation", "role": "user", "content": "Generate weekly token cost report for the week of 2024-01-08 to 2024-01-14. Pull data from /data/usage_logs/. Format: markdown table."},
        {"type": "observation", "role": "assistant", "content": "Loading usage logs from /data/usage_logs/ for the period 2024-01-08 to 2024-01-14. Aggregating token counts per agent."},
        {"type": "tool_use", "tool": "aggregate_usage", "input": {"start": "2024-01-08", "end": "2024-01-14"}, "output": {"reconciler": {"sessions": 7, "tokens": 142000}, "fraud_sentinel": {"sessions": 14, "tokens": 287000}, "report_bot": {"sessions": 3, "tokens": 61000}}},
        {"type": "observation", "role": "assistant", "content": "Usage aggregated. Total tokens this week: 490,000. Calculating costs at $0.00003/token."},
        {"type": "observation", "role": "assistant", "content": "Total cost: $14.70. Budget: $12.00. Overspend: $2.70 (22.5%). Triggering budget alert."},
        {"type": "tool_use", "tool": "send_alert", "input": {"type": "budget_overspend", "amount_usd": 2.70, "pct": 22.5}, "output": "Alert sent to infrastructure channel."},
        {"type": "observation", "role": "assistant", "content": "Weekly report generated and budget alert sent. Recommend investigating token reduction strategies."},
        {"type": "session_end", "timestamp": "2024-01-14T08:07:31Z", "tokens_used": 5840},
    ],
}

for filename, entries in sessions.items():
    path = WORKSPACE / "memory" / "sessions" / filename
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

# ── WORKSPACE CONFIG (intentionally ABSENT — agent must create it) ────────────
# The task requires a non-standard chars_per_token of 3.5
# Agent must discover this and write the config file.

print(f"Workspace generated at {WORKSPACE}")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")