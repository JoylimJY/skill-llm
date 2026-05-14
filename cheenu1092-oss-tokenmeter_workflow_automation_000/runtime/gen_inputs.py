import os
import json
import random
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create a realistic messy directory structure with distractor files
dirs = [
    "company/legal/contracts",
    "company/legal/briefs",
    "company/finance/invoices",
    "company/finance/reports",
    "company/tech/logs/legalbot",
    "company/tech/logs/researchbot",
    "company/tech/configs",
    "company/hr/onboarding",
    "company/hr/policies",
    "archive/2025/q4",
    "archive/2025/q3",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "company/legal/contracts/nda_template.txt": "NON-DISCLOSURE AGREEMENT TEMPLATE v2.1\nThis agreement...",
    "company/legal/briefs/case_001_notes.txt": "Case #001: Patent infringement analysis\nKey points:\n- Prior art search needed",
    "company/finance/invoices/anthropic_jan2026.txt": "Anthropic Invoice - January 2026\nClaude Max Plan: $100.00\nDue: Feb 1, 2026",
    "company/finance/invoices/anthropic_feb2026.txt": "Anthropic Invoice - February 2026\nClaude Max Plan: $100.00\nDue: Mar 1, 2026",
    "company/finance/reports/q4_2025_summary.txt": "Q4 2025 Technology Spend Summary\nCloud services: $2,340\nAI tools: $400\nTotal: $2,740",
    "company/tech/configs/legalbot.yaml": "bot_name: legalbot\nmodel: claude-opus-4\nmax_tokens: 4096\ntemperature: 0.1",
    "company/tech/configs/researchbot.yaml": "bot_name: researchbot\nmodel: claude-sonnet-4\nmax_tokens: 8192\ntemperature: 0.3",
    "company/hr/policies/ai_usage_policy.md": "# AI Usage Policy\nEmployees must log all AI assistant usage...",
    "company/hr/onboarding/new_hire_checklist.txt": "1. Set up email\n2. Review AI policy\n3. Get tokenmeter access",
    "archive/2025/q4/usage_summary_old.txt": "Old format usage log - DEPRECATED\nDo not use for billing",
    "archive/2025/q3/cost_report_q3.txt": "Q3 2025 AI Costs\nOpenAI: $230\nAnthropic: $180\nTotal: $410",
    "tmp/scratch/test_query.sql": "SELECT * FROM usage LIMIT 10;",
}

for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# THE ACTUAL PROBLEM: Raw usage data for February 2026
# This is a messy CSV that the agent needs to process and load into tokenmeter
# It includes:
# - Records with cache tokens (requiring JSONL import via --path)
# - Records without cache tokens (can use manual log)
# - Mixed models and apps
# - Some records have intentionally messy/inconsistent formatting

# JSONL session files for the legalbot (has cache tokens - must use import --path)
legalbot_sessions = [
    {
        "session_id": "lb-sess-001",
        "timestamp": "2026-02-03T09:15:22Z",
        "model": "anthropic/claude-opus-4",
        "usage": {
            "input_tokens": 2500,
            "output_tokens": 1200,
            "cache_creation_input_tokens": 45000,
            "cache_read_input_tokens": 0
        }
    },
    {
        "session_id": "lb-sess-002",
        "timestamp": "2026-02-03T11:30:45Z",
        "model": "anthropic/claude-opus-4",
        "usage": {
            "input_tokens": 800,
            "output_tokens": 2100,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 42000
        }
    },
    {
        "session_id": "lb-sess-003",
        "timestamp": "2026-02-04T14:22:10Z",
        "model": "anthropic/claude-sonnet-4",
        "usage": {
            "input_tokens": 3200,
            "output_tokens": 1800,
            "cache_creation_input_tokens": 28000,
            "cache_read_input_tokens": 0
        }
    },
    {
        "session_id": "lb-sess-004",
        "timestamp": "2026-02-05T16:45:33Z",
        "model": "anthropic/claude-opus-4",
        "usage": {
            "input_tokens": 1100,
            "output_tokens": 3400,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 89000
        }
    },
    {
        "session_id": "lb-sess-005",
        "timestamp": "2026-02-06T10:11:55Z",
        "model": "anthropic/claude-sonnet-4",
        "usage": {
            "input_tokens": 4500,
            "output_tokens": 900,
            "cache_creation_input_tokens": 62000,
            "cache_read_input_tokens": 155000
        }
    },
    {
        "session_id": "lb-sess-006",
        "timestamp": "2026-02-07T08:30:00Z",
        "model": "anthropic/claude-3.5-haiku",
        "usage": {
            "input_tokens": 12000,
            "output_tokens": 4500,
            "cache_creation_input_tokens": 8000,
            "cache_read_input_tokens": 35000
        }
    },
]

# Write legalbot JSONL session file
legalbot_jsonl_path = workspace / "company/tech/logs/legalbot/session_feb2026.jsonl"
with open(legalbot_jsonl_path, 'w') as f:
    for record in legalbot_sessions:
        f.write(json.dumps(record) + '\n')

# JSONL session files for the researchbot (also has cache tokens)
researchbot_sessions = [
    {
        "session_id": "rb-sess-001",
        "timestamp": "2026-02-03T13:00:00Z",
        "model": "anthropic/claude-sonnet-4",
        "usage": {
            "input_tokens": 5600,
            "output_tokens": 7200,
            "cache_creation_input_tokens": 95000,
            "cache_read_input_tokens": 0
        }
    },
    {
        "session_id": "rb-sess-002",
        "timestamp": "2026-02-04T09:45:12Z",
        "model": "anthropic/claude-sonnet-4",
        "usage": {
            "input_tokens": 2200,
            "output_tokens": 8900,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 91000
        }
    },
    {
        "session_id": "rb-sess-003",
        "timestamp": "2026-02-05T11:20:30Z",
        "model": "anthropic/claude-opus-4",
        "usage": {
            "input_tokens": 3800,
            "output_tokens": 5500,
            "cache_creation_input_tokens": 72000,
            "cache_read_input_tokens": 215000
        }
    },
    {
        "session_id": "rb-sess-004",
        "timestamp": "2026-02-06T15:33:44Z",
        "model": "anthropic/claude-3.5-haiku",
        "usage": {
            "input_tokens": 18000,
            "output_tokens": 12000,
            "cache_creation_input_tokens": 25000,
            "cache_read_input_tokens": 180000
        }
    },
    {
        "session_id": "rb-sess-005",
        "timestamp": "2026-02-07T12:00:00Z",
        "model": "anthropic/claude-sonnet-4",
        "usage": {
            "input_tokens": 6700,
            "output_tokens": 9300,
            "cache_creation_input_tokens": 88000,
            "cache_read_input_tokens": 302000
        }
    },
]

researchbot_jsonl_path = workspace / "company/tech/logs/researchbot/session_feb2026.jsonl"
with open(researchbot_jsonl_path, 'w') as f:
    for record in researchbot_sessions:
        f.write(json.dumps(record) + '\n')

# Write a task brief for the agent (the business request, not a how-to guide)
task_brief = """INTERNAL MEMO - AI Cost Audit Request
FROM: Sarah Chen, CFO
TO: Engineering Team
DATE: February 8, 2026
RE: Monthly AI Cost Justification

Our Anthropic Claude Max plan renews at $100/month. The board wants to know 
if we're getting value. Please audit our two AI assistant bots (legalbot and 
researchbot) for February 2026 usage.

The raw session logs are in company/tech/logs/legalbot/ and 
company/tech/logs/researchbot/ directories.

Deliverable: A JSON file named 'cost_audit_feb2026.json' containing:
- Total API-equivalent cost (what we would have paid without Max plan)
- Cost breakdown per model
- Max plan monthly cost ($100)
- Total savings from having Max plan

Submit ASAP - board meeting is Monday.

- Sarah
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

# Also create a misleading "template" that has wrong field names to trap naive agents
wrong_template = {
    "month": "February 2026",
    "api_cost": 0.0,
    "models": {},
    "subscription_cost": 100.0,
    "net_savings": 0.0
}
(workspace / "tmp/scratch/report_template_OLD.json").write_text(json.dumps(wrong_template, indent=2))

print("Workspace generated successfully.")
print(f"Legalbot sessions: {legalbot_jsonl_path}")
print(f"Researchbot sessions: {researchbot_jsonl_path}")
print(f"Total legalbot records: {len(legalbot_sessions)}")
print(f"Total researchbot records: {len(researchbot_sessions)}")

# Pre-compute expected costs for eval reference (stored separately, not in workspace)
# Prices per 1M tokens:
# claude-opus-4: input=$15, output=$75, cache_write=$18.75, cache_read=$1.50
# claude-sonnet-4: input=$3, output=$15, cache_write=$3.75, cache_read=$0.30
# claude-3.5-haiku: input=$0.80, output=$4, cache_write=$1.00, cache_read=$0.08

def calc_cost(model, input_t, output_t, cache_w, cache_r):
    pricing = {
        "anthropic/claude-opus-4":    {"input": 15.0, "output": 75.0, "cache_write": 18.75, "cache_read": 1.50},
        "anthropic/claude-sonnet-4":  {"input": 3.0,  "output": 15.0, "cache_write": 3.75,  "cache_read": 0.30},
        "anthropic/claude-3.5-haiku": {"input": 0.80, "output": 4.0,  "cache_write": 1.00,  "cache_read": 0.08},
    }
    p = pricing[model]
    cost = (input_t * p["input"] + output_t * p["output"] + cache_w * p["cache_write"] + cache_r * p["cache_read"]) / 1_000_000
    return cost

all_sessions = legalbot_sessions + researchbot_sessions
total_cost = 0.0
model_costs = {}

for s in all_sessions:
    m = s["model"]
    u = s["usage"]
    c = calc_cost(m, u["input_tokens"], u["output_tokens"],
                  u.get("cache_creation_input_tokens", 0),
                  u.get("cache_read_input_tokens", 0))
    total_cost += c
    model_costs[m] = model_costs.get(m, 0.0) + c

print(f"\nExpected total cost: ${total_cost:.4f}")
for m, c in model_costs.items():
    print(f"  {m}: ${c:.4f}")
print(f"Expected savings (vs $100 Max plan): ${total_cost - 100:.4f}")