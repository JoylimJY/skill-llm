#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a deeply nested distractor structure simulating a trading ops project
dirs = [
    "ops/legacy/v1/strategies",
    "ops/legacy/v1/logs",
    "ops/legacy/v2/archive",
    "ops/configs/prod",
    "ops/configs/staging",
    "ops/monitoring/dashboards",
    "ops/monitoring/alerts",
    "docs/runbooks",
    "docs/api",
    "scripts/deploy",
    "scripts/backup",
    "data/snapshots",
    "data/exports",
    ".cache/tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "ops/legacy/v1/strategies/momentum_v1.py": """# Legacy momentum strategy - DEPRECATED
class MomentumV1:
    def run(self): pass
""",
    "ops/legacy/v1/strategies/mean_revert.py": """# Mean reversion - archived
THRESHOLD = 0.05
""",
    "ops/legacy/v1/logs/run_20240101.log": """[2024-01-01 10:00] RUN STARTED strategyId=strat_old_001
[2024-01-01 10:05] position opened MARKET=BTC
[2024-01-01 11:00] RUN STOPPED
""",
    "ops/legacy/v2/archive/README_DO_NOT_USE.txt": "These strategies are deprecated. Use new system.",
    "ops/configs/prod/db.json": json.dumps({"host": "db.prod.internal", "port": 5432, "db": "trading"}),
    "ops/configs/staging/feature_flags.json": json.dumps({"paper_only": True, "max_budget": 200}),
    "ops/monitoring/dashboards/grafana_export.json": json.dumps({"panels": [], "title": "Trading Ops"}),
    "ops/monitoring/alerts/pagerduty_rules.yaml": "alerts:\n  - name: strategy_down\n    threshold: 5m\n",
    "docs/runbooks/incident_response.md": "# Incident Response\n1. Check logs\n2. Stop strategy\n3. Alert team\n",
    "docs/api/openapi_draft.yaml": "openapi: 3.0.0\ninfo:\n  title: Trading API Draft\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploy script placeholder'\n",
    "scripts/backup/backup_strategies.py": """import os
# Backs up strategy files
def backup(): pass
""",
    "data/snapshots/snapshot_20240115.csv": "timestamp,market,price\n2024-01-15,BTC-USD,45000\n2024-01-15,ETH-USD,2500\n",
    "data/exports/positions_old.json": json.dumps([
        {"market": "BTC-USD", "side": "BUY", "pnl": 120.5},
        {"market": "ETH-USD", "side": "SELL", "pnl": -30.2},
    ]),
    ".cache/tmp/session_token_expired.txt": "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.EXPIRED",
}

for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.write_text(content)

# Write a strategy specification file the agent should use as the strategy description
strategy_spec = {
    "intent": "Trade on political event prediction markets. Buy YES shares when polling averages shift more than 3% in 24 hours. Exit positions after 48 hours or at 15% profit. Maximum exposure per market: $20.",
    "mode": "paper",
    "budget_usd": 75,
    "duration_hours": 6,
    "notes": "This is for a paper run only. Do not use --live flag."
}
(workspace / "ops/configs/staging/strategy_spec.json").write_text(
    json.dumps(strategy_spec, indent=2)
)

# Write a partially filled lifecycle tracker (agent must complete it)
partial_tracker = {
    "project": "political-markets-bot",
    "status": "NOT_STARTED",
    "conversationId": None,
    "strategyId": None,
    "run_mode": None,
    "monitoring_summary": None,
    "last_command": None
}
(workspace / "ops/monitoring/lifecycle_tracker_partial.json").write_text(
    json.dumps(partial_tracker, indent=2)
)

# A confusing old report that should NOT be the final answer
old_report = {
    "project": "political-markets-bot",
    "status": "COMPLETED",
    "conversationId": "conv_FAKE_DO_NOT_USE",
    "strategyId": "strat_FAKE_001",
    "run_mode": "live",
    "monitoring_summary": "This is a fake historical report",
    "last_command": "dawn run stop conv_FAKE_DO_NOT_USE"
}
(workspace / "data/snapshots/old_lifecycle_report.json").write_text(
    json.dumps(old_report, indent=2)
)

print("Workspace generated successfully.")