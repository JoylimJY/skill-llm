import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractors ---
dirs = [
    "internal/legacy_contracts",
    "internal/billing",
    "internal/hr/onboarding",
    "ops/monitoring/alerts",
    "ops/deployment/k8s",
    "research/competitors",
    "research/market_data",
    "agents/retired",
    "agents/staging",
    "config/env_templates",
    "logs/2023",
    "logs/2024_q1",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "internal/legacy_contracts/freelance_v1.json": json.dumps({
        "platform": "OldMarket",
        "contract_id": "FM-0042",
        "status": "archived",
        "payout": "100 USD"
    }, indent=2),
    "internal/billing/invoices_q4.csv": "invoice_id,amount,currency\nINV-001,500,USD\nINV-002,300,USD",
    "internal/hr/onboarding/checklist.txt": "1. Sign NDA\n2. Setup VPN\n3. Read handbook",
    "ops/monitoring/alerts/rules.yaml": "alert: HighCPU\ncondition: cpu > 80%\naction: notify",
    "ops/deployment/k8s/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: neuralbridge-agent",
    "research/competitors/analysis_2024.txt": "Competitor A: 20% market share\nCompetitor B: 15% market share",
    "research/market_data/q2_rates.json": json.dumps({"avg_task_price": 75, "currency": "USD", "source": "internal"}, indent=2),
    "agents/retired/agent_v0.2_config.json": json.dumps({
        "handle": "oldbot_v02",
        "status": "decommissioned",
        "token": "expired_token_xyz"
    }, indent=2),
    "agents/staging/test_agent.json": json.dumps({
        "handle": "staging_bot",
        "email": "staging@neuralbridge.internal",
        "token": "NOT_A_REAL_TOKEN"
    }, indent=2),
    "config/env_templates/agent_template.env": "OPENTASK_EMAIL=\nOPENTASK_TOKEN=\nOPENTASK_WALLET=",
    "logs/2023/run_log_dec.txt": "2023-12-01 12:00:00 INFO legacy system shutdown",
    "logs/2024_q1/errors_jan.txt": "2024-01-15 ERROR connection refused to old marketplace API",
    "research/market_data/task_categories.json": json.dumps({
        "categories": ["data_analysis", "writing", "code", "research", "ai_agent"],
        "avg_budgets": {"data_analysis": 150, "writing": 80, "code": 400, "research": 100, "ai_agent": 40}
    }, indent=2),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The actual briefing file the agent must read to know what to do ---
briefing = {
    "organization": "NeuralBridge Labs",
    "mission": (
        "Automate revenue generation by registering our worker agent on the OpenTask marketplace, "
        "discovering available tasks, placing strategic bids, and submitting a deliverable for the first awarded contract."
    ),
    "agent_identity": {
        "email": "worker@neuralbridge-labs.ai",
        "password": "NeuralBridge#2024!",
        "handle": "neuralbridge_worker",
        "displayName": "NeuralBridge Worker Agent"
    },
    "wallet": {
        "denomination": "USDC",
        "network": "polygon",
        "address": "0xDEADBEEF00000000000000000000000000000001"
    },
    "task_preferences": {
        "min_budget_usdc": 50,
        "preferred_skills": ["data-analysis", "research", "python"]
    },
    "deliverable_template": {
        "repo_url": "https://github.com/neuralbridge-labs/deliverable-001",
        "notes": "Completed full analysis as specified. Verification: run main.py with provided dataset. Known limitations: assumes CSV input format."
    },
    "api_base_url": "http://localhost:8787",
    "output_file": "opentask_session.json"
}

with open(os.path.join(workspace, "neuralbridge_mission_brief.json"), "w") as f:
    json.dump(briefing, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} total")