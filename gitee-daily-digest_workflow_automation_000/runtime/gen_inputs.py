import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a deeply nested distractor structure simulating a real dev workspace
dirs = [
    "projects/fintech-core/src/api",
    "projects/fintech-core/src/models",
    "projects/fintech-core/tests",
    "projects/payment-gateway/docs",
    "projects/payment-gateway/config",
    "infra/k8s/manifests",
    "infra/terraform/modules",
    "scripts/deploy",
    "scripts/migrate",
    ".config/gitee",
    "notes/meetings",
    "notes/architecture",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "projects/fintech-core/src/api/payment.py": "# Payment API handler\ndef process_payment(amount, currency): pass\n",
    "projects/fintech-core/src/models/transaction.py": "# Transaction model\nclass Transaction:\n    pass\n",
    "projects/fintech-core/tests/test_payment.py": "import unittest\nclass TestPayment(unittest.TestCase): pass\n",
    "projects/payment-gateway/docs/integration.md": "# Integration Guide\nSee Gitee for issues.\n",
    "projects/payment-gateway/config/prod.yaml": "env: production\ndb_host: 10.0.0.1\nport: 5432\n",
    "infra/k8s/manifests/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: fintech-core\n",
    "infra/terraform/modules/vpc.tf": "resource \"aws_vpc\" \"main\" {\n  cidr_block = \"10.0.0.0/16\"\n}\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/migrate/run_migrations.sh": "#!/bin/bash\nflyway migrate\n",
    ".config/gitee/config.json": json.dumps({"endpoint": "https://gitee.com/api/v5", "timeout": 30}),
    "notes/meetings/2024-01-15-standup.md": "# Standup\n- Reviewed PR #42\n- Blocked on infra issue\n",
    "notes/architecture/event-sourcing.md": "# Event Sourcing\nConsider using Kafka for event bus.\n",
    "projects/fintech-core/src/api/auth.py": "# Auth handler\ndef verify_token(token): return True\n",
}

for path, content in distractor_files.items():
    full_path = workspace / path
    full_path.write_text(content)

# Create a mcporter config stub (agent needs to discover and use it)
mcporter_config = {
    "version": "1.0",
    "servers": {
        "gitee": {
            "enabled": True,
            "tools": ["get_user_info", "list_user_notifications", "list_repo_pulls", "list_repo_issues"]
        }
    }
}
(workspace / ".config" / "mcporter.json").write_text(json.dumps(mcporter_config, indent=2))

# Create a placeholder for where the agent should write output
# (We do NOT create daily_digest.md - agent must create it)

# Create a note about what the user wants (business context only, no hints)
(workspace / "notes" / "meetings" / "today-tasks.txt").write_text(
    "Need to check Gitee for what's pending today. Ask AI to generate daily digest.\n"
    "Should cover notifications, PRs, and issues.\n"
)

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")