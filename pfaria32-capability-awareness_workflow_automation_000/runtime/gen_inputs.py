import os
import random
random.seed(42)

BASE = "/workspace"

# --- Create realistic deeply nested distractor structure ---
dirs = [
    "home/node/.openclaw/workspace/projects/capability-awareness-system",
    "home/node/.openclaw/workspace/projects/old-agent-v1",
    "home/node/.openclaw/workspace/projects/data-pipeline",
    "home/node/.openclaw/workspace/logs",
    "home/node/.openclaw/workspace/config",
    "home/node/.openclaw/workspace/skills",  # exists but EMPTY — agent must populate
    "home/node/.openclaw/workspace/skills/fraud-detection",
    "home/node/.openclaw/workspace/skills/currency-converter",
    "home/node/.openclaw/workspace/skills/compliance-checker",
    "home/node/.openclaw/workspace/tmp",
    "home/node/.openclaw/workspace/drafts",
    "home/node/.openclaw/workspace/.cache",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# Old broken AGENTS.md in root (wrong format, outdated — agent must create/fix the proper one)
broken_agents_md = """\
# Agent Configuration (DEPRECATED - DO NOT USE)

This file is outdated. The agent setup has moved to a new format.

## Old Skills List
- fraud-detection: checks for fraud
- currency-converter: converts currencies  
- compliance-checker: checks compliance

## Notes
This was the v0 approach. We switched to a different system.
"""
with open(os.path.join(BASE, "home/node/.openclaw/workspace/AGENTS.md"), "w") as f:
    f.write(broken_agents_md)

# Old project leftovers
with open(os.path.join(BASE, "home/node/.openclaw/workspace/projects/old-agent-v1/config.json"), "w") as f:
    f.write('{"version": "0.1", "skills": [], "deprecated": true}\n')

with open(os.path.join(BASE, "home/node/.openclaw/workspace/projects/old-agent-v1/README_OLD.md"), "w") as f:
    f.write("# Old Agent\nThis agent used a flat config file. No longer maintained.\n")

# Data pipeline distractor
with open(os.path.join(BASE, "home/node/.openclaw/workspace/projects/data-pipeline/pipeline.py"), "w") as f:
    f.write("# Data pipeline stub\ndef run(): pass\n")

with open(os.path.join(BASE, "home/node/.openclaw/workspace/projects/data-pipeline/schema.json"), "w") as f:
    f.write('{"tables": ["transactions", "users", "events"]}\n')

# Log distractors
for i in range(3):
    with open(os.path.join(BASE, f"home/node/.openclaw/workspace/logs/agent_{i}.log"), "w") as f:
        f.write(f"[2024-01-{10+i}] Agent run {i}: completed\n")

# Config distractors
with open(os.path.join(BASE, "home/node/.openclaw/workspace/config/env.yaml"), "w") as f:
    f.write("environment: production\nregion: eu-west-1\ndebug: false\n")

with open(os.path.join(BASE, "home/node/.openclaw/workspace/config/agent_settings.yaml"), "w") as f:
    f.write("model: gpt-4\nmax_tokens: 4096\ntemperature: 0.2\n")

# Drafts (wrong/incomplete attempts at SKILL.md — distractors)
with open(os.path.join(BASE, "home/node/.openclaw/workspace/drafts/skill_fraud_draft.md"), "w") as f:
    f.write("# Fraud Detection Draft\nJust a rough notes file, not the real SKILL.md\n- uses ML model\n- threshold: 0.85\n")

with open(os.path.join(BASE, "home/node/.openclaw/workspace/drafts/agents_idea.txt"), "w") as f:
    f.write("Idea: maybe put skills in a JSON file? Or YAML? TBD.\n")

# Cache placeholder
with open(os.path.join(BASE, "home/node/.openclaw/workspace/.cache/.gitkeep"), "w") as f:
    f.write("")

# Capability awareness project clone simulation (just a marker file, not full content)
with open(os.path.join(BASE, "home/node/.openclaw/workspace/projects/capability-awareness-system/README.md"), "w") as f:
    f.write("# OpenClaw Capability Awareness\nCloned reference implementation.\n")

# --- The ACTUAL skill source notes (raw, unstructured business docs the agent must use to write SKILL.md files) ---
# These are NOT proper SKILL.md files — they are raw business descriptions the agent must transform

fraud_raw = """\
FRAUD DETECTION SKILL - INTERNAL NOTES
========================================
Team: Risk Engineering
Status: Production Ready

What it does:
  Analyzes transaction data for anomalous patterns using a trained ML model.
  Integrates with our internal Postgres DB and returns risk scores.

When to use this skill:
  - User asks about suspicious transactions
  - Payment verification workflows
  - Risk scoring for new accounts

How to invoke:
  Run: python skills/fraud-detection/run.py --transaction-id <ID>
  Returns JSON with fields: risk_score (0.0-1.0), flags[], recommendation

Thresholds:
  > 0.85 = high risk (block)
  0.5-0.85 = medium risk (manual review)
  < 0.5 = low risk (allow)

Owner: alice@fintech.example.com
"""

currency_raw = """\
CURRENCY CONVERTER SKILL
========================
Built by: Platform Team
Last updated: 2024-03

Purpose:
  Real-time and historical FX rate lookups. Supports 150+ currencies.
  Uses internal rate feed (updated every 5 minutes).

Trigger cases:
  - Multi-currency transaction reporting
  - User asks about exchange rates
  - Invoice conversion for international clients

CLI usage:
  python skills/currency-converter/convert.py --from USD --to EUR --amount 1000
  python skills/currency-converter/convert.py --from GBP --to JPY --amount 500 --date 2024-01-15

Output: JSON with converted_amount, rate, timestamp, source

Dependencies: internal-rates-service (must be running)
"""

compliance_raw = """\
Compliance Checker - Quick Reference
=====================================
Category: Regulatory / Legal

Description:
  Validates transactions and customer profiles against AML, KYC, and
  PSD2 requirements. Also checks GDPR data handling compliance.

Use when:
  - Onboarding new business customers
  - Large value transaction (>10k EUR) screening
  - Quarterly compliance audit runs
  - User asks about regulatory requirements

Command:
  python skills/compliance-checker/check.py --mode [aml|kyc|gdpr|psd2] --input <file.json>

Returns: compliance_status (PASS/FAIL/REVIEW), violations[], report_id

Note: This skill requires the compliance-db container to be running.
Escalate FAIL results to compliance@fintech.example.com immediately.
"""

with open(os.path.join(BASE, "home/node/.openclaw/workspace/skills/fraud-detection/notes.txt"), "w") as f:
    f.write(fraud_raw)

with open(os.path.join(BASE, "home/node/.openclaw/workspace/skills/currency-converter/notes.txt"), "w") as f:
    f.write(currency_raw)

with open(os.path.join(BASE, "home/node/.openclaw/workspace/skills/compliance-checker/notes.txt"), "w") as f:
    f.write(compliance_raw)

# Tmp junk
with open(os.path.join(BASE, "home/node/.openclaw/workspace/tmp/scratch.txt"), "w") as f:
    f.write("scratch pad - ignore\n2+2=4\ntest test test\n")

print("Workspace generated successfully.")
print("Structure:")
for root, dirs_list, files in os.walk(BASE):
    level = root.replace(BASE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')