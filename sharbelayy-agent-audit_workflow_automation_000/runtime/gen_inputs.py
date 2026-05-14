import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ".openclaw",
    ".openclaw/sessions",
    ".openclaw/cron",
    ".openclaw/cron/history",
    ".openclaw/agents",
    ".openclaw/logs",
    "scripts",
    "references",
    "configs/backup",
    "configs/staging",
    "docs/internal",
    "docs/runbooks",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(workspace / "docs/internal/onboarding.md").write_text("# Onboarding\nWelcome to Meridian FinOps.\n")
(workspace / "docs/runbooks/incident-response.md").write_text("# Incident Response\nSee PagerDuty.\n")
(workspace / "configs/backup/openclaw.json.bak").write_text('{"version": "0.8.1", "legacy": true}\n')
(workspace / "configs/staging/env.yaml").write_text("environment: staging\ndebug: true\n")
(workspace / "tmp/scratch/notes.txt").write_text("TODO: check billing dashboard\n")
(workspace / ".openclaw/logs/system.log").write_text(
    "[2026-01-15 08:00:01] INFO  scheduler started\n"
    "[2026-01-15 08:00:02] INFO  loaded 6 cron jobs\n"
    "[2026-01-15 09:15:33] WARN  job 'compliance-scan' took 4m12s\n"
)
(workspace / ".openclaw/sessions/.session_index").write_text("sessions: 47\n")
(workspace / "configs/backup/agents.json.bak").write_text('{"agents": [], "deprecated": true}\n')
(workspace / "tmp/scratch/old_pricing.txt").write_text("claude-opus: $8/M (OUTDATED)\n")
(workspace / "docs/internal/model-comparison.txt").write_text(
    "Internal note: grok-3 behaves unexpectedly on financial prompts.\n"
)

# ── OpenClaw main config ─────────────────────────────────────────────────────
openclaw_config = {
    "version": "1.4.2",
    "default_model": "anthropic/claude-sonnet-4",
    "agents": [
        {
            "id": "agent-001",
            "name": "TradeAlert Bot",
            "model": "anthropic/claude-opus-4",
            "description": "Sends trading alerts and price notifications to Slack",
            "thinking": False,
        },
        {
            "id": "agent-002",
            "name": "ComplianceGuard",
            "model": "anthropic/claude-opus-4",
            "description": "Performs security and compliance review of trade logs",
            "thinking": True,
        },
        {
            "id": "agent-003",
            "name": "DailyDigest",
            "model": "openai/gpt-4o",
            "description": "Produces daily market research summaries for analysts",
            "thinking": False,
        },
        {
            "id": "agent-004",
            "name": "CodeReviewBot",
            "model": "anthropic/claude-opus-4",
            "description": "Reviews pull requests and generates code quality reports",
            "thinking": False,
        },
        {
            "id": "agent-005",
            "name": "PingWatcher",
            "model": "anthropic/claude-opus-4",
            "description": "Health check monitor for internal microservices",
            "thinking": False,
        },
        {
            "id": "agent-006",
            "name": "RegulatoryBrief",
            "model": "xai/grok-3",
            "description": "Drafts weekly regulatory update briefs for the legal team",
            "thinking": False,
        },
    ],
    "cron_enabled": True,
    "history_retention_days": 30,
}

(workspace / ".openclaw/openclaw.json").write_text(
    json.dumps(openclaw_config, indent=2)
)

# ── Cron job configs ─────────────────────────────────────────────────────────
cron_jobs = [
    {
        "id": "cron-001",
        "name": "Trade Price Alert",
        "agent_id": "agent-001",
        "model": "anthropic/claude-opus-4",
        "schedule": "*/15 * * * *",  # every 15 min → 96/day
        "runs_per_day": 96,
        "payload_type": "systemEvent",
        "description": "Checks price feeds and sends Slack alerts for threshold breaches",
        "user_explicit_model": False,
    },
    {
        "id": "cron-002",
        "name": "Compliance Audit Scan",
        "agent_id": "agent-002",
        "model": "anthropic/claude-opus-4",
        "schedule": "0 2 * * *",  # daily at 2am
        "runs_per_day": 1,
        "payload_type": "auditRequest",
        "description": "Security review of daily trade logs for regulatory compliance",
        "user_explicit_model": False,
    },
    {
        "id": "cron-003",
        "name": "Market Research Digest",
        "agent_id": "agent-003",
        "model": "openai/gpt-4o",
        "schedule": "0 7 * * 1-5",  # weekdays at 7am
        "runs_per_day": 0.71,  # 5/7
        "payload_type": "researchRequest",
        "description": "Synthesizes overnight market news into analyst digest",
        "user_explicit_model": False,
    },
    {
        "id": "cron-004",
        "name": "PR Code Review",
        "agent_id": "agent-004",
        "model": "anthropic/claude-opus-4",
        "schedule": "0 */4 * * *",  # every 4h
        "runs_per_day": 6,
        "payload_type": "codeReview",
        "description": "Scans open pull requests and generates review comments",
        "user_explicit_model": False,
    },
    {
        "id": "cron-005",
        "name": "Microservice Health Ping",
        "agent_id": "agent-005",
        "model": "anthropic/claude-opus-4",
        "schedule": "*/5 * * * *",  # every 5 min → 288/day
        "runs_per_day": 288,
        "payload_type": "systemEvent",
        "description": "Pings 12 internal microservices and posts status to dashboard",
        "user_explicit_model": False,
    },
    {
        "id": "cron-006",
        "name": "Regulatory Weekly Brief",
        "agent_id": "agent-006",
        "model": "xai/grok-3",
        "schedule": "0 9 * * 1",  # Mondays at 9am
        "runs_per_day": 0.143,  # 1/7
        "payload_type": "researchRequest",
        "description": "Compiles regulatory changes into weekly legal team brief",
        "user_explicit_model": False,
    },
]

for cron in cron_jobs:
    path = workspace / ".openclaw/cron" / f"{cron['id']}.json"
    path.write_text(json.dumps(cron, indent=2))

# ── Cron run history (last 7 days, deterministic) ────────────────────────────
# cron-001: Trade Price Alert — simple systemEvent, tiny output, high success
# Should be recommended: downgrade opus-4 → haiku-3
cron001_runs = []
for i in range(96 * 7):  # 672 runs
    cron001_runs.append({
        "run_id": f"r001-{i:04d}",
        "cron_id": "cron-001",
        "timestamp": f"2026-01-{15 - (i // 96):02d}T{(i % 24):02d}:00:00Z",
        "model": "anthropic/claude-opus-4",
        "input_tokens": random.randint(280, 340),
        "output_tokens": random.randint(90, 150),  # well under 500 → Simple
        "runtime_seconds": random.randint(4, 9),    # under 30s → Simple
        "success": True,
        "tool_calls": 0,
    })

# cron-002: Compliance Audit Scan — security task, thinking=True → NEVER downgrade
cron002_runs = []
for i in range(7):
    cron002_runs.append({
        "run_id": f"r002-{i:04d}",
        "cron_id": "cron-002",
        "timestamp": f"2026-01-{15 - i:02d}T02:00:00Z",
        "model": "anthropic/claude-opus-4",
        "input_tokens": random.randint(8000, 12000),
        "output_tokens": random.randint(2500, 4000),  # Complex by output
        "runtime_seconds": random.randint(180, 300),
        "success": True,
        "tool_calls": random.randint(5, 9),
    })

# cron-003: Market Research Digest — medium task, gpt-4o is correct tier
# Medium signals: output 800-1800, runtime 60-120s, 1-2 tool calls
# gpt-4o IS the medium tier model → NO recommendation needed
cron003_runs = []
for i in range(5):
    cron003_runs.append({
        "run_id": f"r003-{i:04d}",
        "cron_id": "cron-003",
        "timestamp": f"2026-01-{15 - i:02d}T07:00:00Z",
        "model": "openai/gpt-4o",
        "input_tokens": random.randint(3000, 5000),
        "output_tokens": random.randint(900, 1600),  # Medium range
        "runtime_seconds": random.randint(65, 115),
        "success": True,
        "tool_calls": random.randint(1, 3),
    })

# cron-004: PR Code Review — CODING TASK → NEVER downgrade
cron004_runs = []
for i in range(6 * 7):  # 42 runs
    cron004_runs.append({
        "run_id": f"r004-{i:04d}",
        "cron_id": "cron-004",
        "timestamp": f"2026-01-{15 - (i // 6):02d}T{(i % 6) * 4:02d}:00:00Z",
        "model": "anthropic/claude-opus-4",
        "input_tokens": random.randint(4000, 8000),
        "output_tokens": random.randint(2200, 4500),  # Complex
        "runtime_seconds": random.randint(200, 400),
        "success": True,
        "tool_calls": random.randint(4, 8),
    })

# cron-005: Microservice Health Ping — systemEvent, tiny output, BUT error rate ~15% → NO downgrade
cron005_runs = []
for i in range(288 * 7):  # 2016 runs
    # 15% error rate
    success = random.random() > 0.15
    cron005_runs.append({
        "run_id": f"r005-{i:06d}",
        "cron_id": "cron-005",
        "timestamp": f"2026-01-{15 - (i // 288):02d}T00:{(i % 60):02d}:00Z",
        "model": "anthropic/claude-opus-4",
        "input_tokens": random.randint(150, 250),
        "output_tokens": random.randint(60, 120),   # Simple by output
        "runtime_seconds": random.randint(3, 8),
        "success": success,
        "tool_calls": 0,
    })

# cron-006: Regulatory Weekly Brief — only 3 runs (<5) → "insufficient data"
# grok-3 is Complex tier, task is medium-ish, but <5 runs → no recommendation
cron006_runs = []
for i in range(3):  # Only 3 runs → insufficient data
    cron006_runs.append({
        "run_id": f"r006-{i:04d}",
        "cron_id": "cron-006",
        "timestamp": f"2026-01-{15 - i * 7:02d}T09:00:00Z",
        "model": "xai/grok-3",
        "input_tokens": random.randint(2000, 4000),
        "output_tokens": random.randint(1200, 1800),
        "runtime_seconds": random.randint(90, 150),
        "success": True,
        "tool_calls": 2,
    })

# Write history files
all_histories = {
    "cron-001": cron001_runs,
    "cron-002": cron002_runs,
    "cron-003": cron003_runs,
    "cron-004": cron004_runs,
    "cron-005": cron005_runs,
    "cron-006": cron006_runs,
}

for cron_id, runs in all_histories.items():
    history_path = workspace / ".openclaw/cron/history" / f"{cron_id}-history.json"
    history_path.write_text(json.dumps({"cron_id": cron_id, "runs": runs}, indent=2))

# ── scripts/ and references/ directories (skill scaffolding) ─────────────────
# The audit.py script is referenced by the skill — create a stub that only prints help
# so the agent cannot simply run it and get the answer.
audit_stub = '''#!/usr/bin/env python3
"""
OpenClaw Audit Script
Usage: python3 audit.py [--format markdown|summary] [--dry-run] [--output FILE]
This script requires the OpenClaw environment to be configured.
"""
import sys
print("ERROR: OpenClaw runtime not initialized. Run `openclaw init` first.")
print("Hint: This script is a launcher stub. The agent audit skill logic must be")
print("      implemented based on the SKILL.md documentation.")
sys.exit(1)
'''
(workspace / "scripts").mkdir(exist_ok=True)
(workspace / "scripts/audit.py").write_text(audit_stub)
os.chmod(workspace / "scripts/audit.py", 0o755)

# Write model pricing and classification references
model_pricing = """# Model Pricing Reference

Updated: February 2026. Prices per 1M tokens.

## Anthropic (Claude)

| Model | Input | Output | Tier |
|-------|-------|--------|------|
| claude-opus-4 | $15.00 | $75.00 | Complex |
| claude-sonnet-4 | $3.00 | $15.00 | Medium |
| claude-haiku-3.5 | $0.80 | $4.00 | Simple |
| claude-haiku-3 | $0.25 | $1.25 | Simple |

## OpenAI

| Model | Input | Output | Tier |
|-------|-------|--------|------|
| gpt-4.5 | $75.00 | $150.00 | Complex |
| gpt-4o | $2.50 | $10.00 | Medium |
| gpt-4o-mini | $0.15 | $0.60 | Simple |
| o1 | $15.00 | $60.00 | Complex |
| o3-mini | $1.10 | $4.40 | Medium |

## Google (Gemini)

| Model | Input | Output | Tier |
|-------|-------|--------|------|
| gemini-2.5-pro | $1.25 | $10.00 | Complex |
| gemini-2.0-flash | $0.10 | $0.40 | Simple |
| gemini-2.0-flash-lite | $0.025 | $0.10 | Simple |

## xAI (Grok)

| Model | Input | Output | Tier |
|-------|-------|--------|------|
| grok-3 | $3.00 | $15.00 | Complex |
| grok-3-mini | $0.30 | $0.50 | Simple |
| grok-4-1-fast | $5.00 | $25.00 | Medium |

## How to Calculate Monthly Cost

```
monthly_cost = (input_tokens / 1M × input_price) + (output_tokens / 1M × output_price)
```

For cron jobs, multiply by runs per month:
```
cron_monthly_cost = cost_per_run × runs_per_day × 30
```

## Tier Recommendations by Provider

| Task Type | Anthropic | OpenAI | Google | xAI |
|-----------|-----------|--------|--------|-----|
| Simple | haiku-3 | gpt-4o-mini | flash-lite | grok-3-mini |
| Medium | sonnet-4 | gpt-4o | flash | grok-4-1-fast |
| Complex | opus-4 | gpt-4.5/o1 | 2.5-pro | grok-3 |
"""
(workspace / "references").mkdir(exist_ok=True)
(workspace / "references/model-pricing.md").write_text(model_pricing)

task_classification = """# Task Classification Heuristics

## Signal-Based Classification

The audit classifies tasks by analyzing multiple signals from cron history and config.

### Simple Task Signals (→ cheapest model)
- **Output length**: Consistently under 500 tokens
- **Name patterns**: "health check", "status", "monitor", "ping", "reminder", "notify", "alert"
- **Runtime**: Under 30 seconds average
- **Token ratio**: Input tokens >> output tokens (reading a lot, writing little)
- **Success rate**: >95% (task is predictable/deterministic)
- **Payload type**: `systemEvent` payloads are almost always simple
- **No tool use**: Tasks that don't call external tools

### Medium Task Signals (→ mid-tier model)
- **Output length**: 500-2000 tokens
- **Name patterns**: "draft", "research", "summary", "analysis", "report", "brief", "scan", "digest"
- **Runtime**: 30 seconds to 3 minutes
- **Some creativity**: Content generation, but with templates/guidelines
- **Tool use**: 1-3 tool calls per run
- **Moderate reasoning**: Needs to make decisions but within clear parameters

### Complex Task Signals (→ top-tier model)
- **Output length**: 2000+ tokens consistently
- **Name patterns**: "code", "build", "architect", "security", "audit", "review", "fix", "debug"
- **Runtime**: Over 3 minutes
- **Heavy reasoning**: Multi-step planning, code generation, nuanced analysis
- **Tool use**: 4+ tool calls per run
- **Low tolerance for error**: Security, financial, or production-critical tasks
- **Previous failures**: Any task that failed on a lower-tier model should stay at current tier

## Override Rules (NEVER downgrade)

1. **Coding tasks** — any task that generates, modifies, or reviews code
2. **Security tasks** — any task involving security review, vulnerability scanning, access control
3. **Financial tasks** — any task involving trading, payments, or financial analysis
4. **User-explicit model choice** — if the user set a specific model in config, respect it
5. **Previously failed downgrades** — if a task was upgraded after failing, don't suggest downgrading again
6. **Main session model** — never recommend changing the user's default interactive model
7. **Tasks with thinking enabled** — if thinking/reasoning is turned on, the task needs it

## Confidence Scoring

| Confidence | Meaning | When to Apply |
|------------|---------|---------------|
| HIGH | Very confident this change is safe | Simple tasks with clear patterns, large cost savings |
| MEDIUM | Likely safe but monitor after change | Medium tasks being suggested for downgrade, less history |
| LOW | Uncertain, proceed with caution | Limited run history, borderline complexity, mixed signals |

## Edge Cases

- **New cron jobs** (<5 runs): Mark as "insufficient data" — don't recommend changes
- **Inconsistent output length**: If output varies wildly, classify at the HIGHER tier
- **Mixed tasks in one cron**: If a cron does both simple and complex work, classify as complex
- **Crons with errors**: If error rate >10%, don't recommend downgrading — it may need MORE capability
"""
(workspace / "references/task-classification.md").write_text(task_classification)

print("✓ Workspace initialized successfully.")
print(f"  Config: {workspace / '.openclaw/openclaw.json'}")
print(f"  Cron jobs: 6")
print(f"  History files: 6")
print(f"  Total run records: {sum(len(v) for v in all_histories.values())}")