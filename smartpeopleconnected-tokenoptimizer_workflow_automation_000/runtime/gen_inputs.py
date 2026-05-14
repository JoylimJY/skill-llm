import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create a realistic, deeply nested distractor directory structure ---
dirs = [
    "src/agents/support",
    "src/agents/billing",
    "src/api/routes",
    "src/api/middleware",
    "config/env",
    "config/legacy",
    "logs/2024-01",
    "logs/2024-02",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "scripts/deploy",
    "scripts/maintenance",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic SaaS project noise) ---
(workspace / "src/agents/support/agent.py").write_text(
    "# Support agent using OpenClaw\nfrom openclaw import Agent\nagent = Agent(model='claude-sonnet')\n"
)
(workspace / "src/agents/billing/billing_agent.py").write_text(
    "# Billing agent\nfrom openclaw import Agent\nagent = Agent(model='claude-opus')\n"
)
(workspace / "src/api/routes/chat.py").write_text(
    "from flask import Blueprint\nchat_bp = Blueprint('chat', __name__)\n@chat_bp.route('/chat', methods=['POST'])\ndef chat(): pass\n"
)
(workspace / "src/api/middleware/auth.py").write_text(
    "def require_auth(f):\n    def wrapper(*args, **kwargs):\n        return f(*args, **kwargs)\n    return wrapper\n"
)
(workspace / "config/env/.env.production").write_text(
    "OPENCLAW_API_KEY=sk-prod-xxxxxxxxxxxxxxxxxxxx\nDATABASE_URL=postgres://localhost/prod\nREDIS_URL=redis://localhost:6379\n"
)
(workspace / "config/env/.env.staging").write_text(
    "OPENCLAW_API_KEY=sk-stage-xxxxxxxxxxxxxxxxxxxx\nDATABASE_URL=postgres://localhost/staging\n"
)
(workspace / "config/legacy/old_config.json").write_text(json.dumps({
    "model": "claude-opus",
    "temperature": 0.7,
    "max_tokens": 4096,
    "deprecated_heartbeat": True
}, indent=2))
(workspace / "logs/2024-01/app.log").write_text(
    "2024-01-15 INFO Agent started\n2024-01-15 ERROR Token limit exceeded\n2024-01-15 WARN High cost alert: $2.34 today\n"
)
(workspace / "logs/2024-02/cost_report.log").write_text(
    "2024-02-01 Daily cost: $2.87\n2024-02-02 Daily cost: $3.12\n2024-02-28 Monthly total: $78.45\n"
)
(workspace / "tests/unit/test_agent.py").write_text(
    "import pytest\ndef test_agent_responds(): assert True\n"
)
(workspace / "tests/integration/test_cost.py").write_text(
    "# Integration test - verify cost controls\nimport pytest\ndef test_budget_not_exceeded(): pass\n"
)
(workspace / "docs/architecture/system_design.md").write_text(
    "# System Design\n## Agent Architecture\nCurrently using Sonnet for all tasks (expensive).\n## Cost Issues\nMonthly bill averaging $80+.\n"
)
(workspace / "scripts/deploy/deploy.sh").write_text(
    "#!/bin/bash\necho 'Deploying to production...'\ndocker-compose up -d\n"
)
(workspace / "scripts/maintenance/cleanup.sh").write_text(
    "#!/bin/bash\nfind /tmp -mtime +7 -delete\n"
)

# A misleading partial config (NOT in ~/.openclaw, just a workspace distractor)
(workspace / "config/legacy/openclaw_draft.json").write_text(json.dumps({
    "agents": {
        "defaults": {
            "model": {"primary": "anthropic/claude-opus-4-5"},
        }
    },
    "heartbeat": {
        "provider": "anthropic",
        "model": "anthropic/claude-haiku-4-5"
    }
}, indent=2))

# A fake stats file in workspace (distractor, real one goes in ~/.openclaw/)
(workspace / "config/legacy/fake_stats.json").write_text(json.dumps({
    "total_savings": 0,
    "optimizations_applied": 0
}, indent=2))

# --- Create a broken / missing ~/.openclaw/ to simulate a fresh unoptimized system ---
openclaw_dir = Path.home() / ".openclaw"
if openclaw_dir.exists():
    shutil.rmtree(openclaw_dir)
# Leave ~/.openclaw/ completely absent — the tool should create it

print("Workspace generated successfully.")
print(f"Workspace: {workspace}")
print(f"~/.openclaw/ intentionally absent (unoptimized state).")