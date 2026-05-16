import os
import random

random.seed(42)

workspace = "/workspace"

# ─── DISTRACTOR FILES: simulate a real platform repo ───────────────────────
distractor_structure = {
    "platform-infra/ci/pipelines/deploy.yml": "stages:\n  - build\n  - test\n  - deploy\n",
    "platform-infra/ci/pipelines/lint.yml": "linters:\n  - flake8\n  - mypy\n",
    "platform-infra/terraform/main.tf": 'provider "aws" {\n  region = "us-east-1"\n}\n',
    "platform-infra/terraform/variables.tf": 'variable "env" {\n  default = "staging"\n}\n',
    "platform-infra/docs/architecture.md": "# Architecture\nThis platform handles fraud detection.\n",
    "platform-infra/docs/runbook.md": "# Runbook\nOn alert: check Grafana dashboard.\n",
    "agent-marketplace/README.md": "# Agent Marketplace\nInternal registry for AI capabilities.\n",
    "agent-marketplace/registry.json": '{"skills": [], "version": "0.1.0"}\n',
    "agent-marketplace/scripts/publish.sh": "#!/bin/bash\necho 'Publishing skill...'\n",
    "agent-marketplace/scripts/index.py": "# indexes all skills\nprint('indexing')\n",
    "legacy-skills/old-skill/skill.md": "# Old Skill\nThis uses the deprecated format.\n",
    "legacy-skills/old-skill/config.json": '{"name": "old-skill", "version": "0.0.1"}\n',
}

for path, content in distractor_structure.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ─── THE BROKEN DRAFT SKILL ─────────────────────────────────────────────────
# Problems injected (agent must fix all):
# 1. Directory name: "Fraud_Detection_Workflow" — uppercase + underscores, doesn't match name field
# 2. name field: "fraud_detection_workflow" — underscores are invalid (must be hyphens only)
# 3. description: >1024 chars AND missing "Use when..." trigger phrase
# 4. metadata.version: unquoted float 1.2 (YAML parses as float, must be "1.2")
# 5. Forbidden 4th subdirectory: "docs/" (only scripts/, references/, assets/ allowed)
# 6. Deep reference: references/v2/advanced.md (violates one-level-deep rule; also file doesn't exist)
# 7. A valid reference file is missing: references/api.md is referenced but doesn't exist
# 8. scripts/analyze.py exists (good) — keep it
# 9. assets/template.json exists (good) — keep it
# Note: correct directory name must be "fraud-detection-workflow" matching name "fraud-detection-workflow"

draft_dir = os.path.join(workspace, "Fraud_Detection_Workflow")
os.makedirs(draft_dir, exist_ok=True)

# Subdirectories
for d in ["scripts", "references", "assets", "docs"]:
    os.makedirs(os.path.join(draft_dir, d), exist_ok=True)

# Forbidden deep reference dir
os.makedirs(os.path.join(draft_dir, "references", "v2"), exist_ok=True)

# SKILL.md with multiple violations
long_description = (
    "This skill provides a comprehensive end-to-end fraud detection pipeline "
    "for financial transaction monitoring systems. It integrates rule-based heuristics "
    "with machine learning model inference to flag suspicious transactions in real time. "
    "The workflow covers data ingestion, feature extraction, model scoring, alert generation, "
    "case management handoff, and audit trail creation. Designed for the internal risk and "
    "compliance team to deploy across multiple banking products. Supports both batch and "
    "streaming modes. Requires access to the transaction database and the fraud ML model endpoint. "
    "Compatible with Python 3.9+ and the internal data platform SDK version 4.x and above. "
    "This is maintained by the AI Platform team and reviewed quarterly. "
    "The skill also provides configurable thresholds for alert sensitivity, supports multi-currency "
    "transaction analysis, and integrates with the internal case management system for downstream "
    "workflow automation. Logging and observability hooks are built in for integration with Grafana "
    "and the internal monitoring stack. All outputs are audit-logged for compliance purposes."
)
# Verify it's > 1024 chars
assert len(long_description) > 1024, f"Description length {len(long_description)} not >1024"

skill_md_content = f"""---
name: fraud_detection_workflow
description: "{long_description}"
license: Apache-2.0
compatibility: Python 3.9+, internal data platform SDK 4.x
metadata:
  author: ai-platform-team
  version: 1.2
  tags: fraud, fintech, ml
allowed-tools: bash python
---

# Fraud Detection Workflow

## Overview
Orchestrate the full fraud detection pipeline from raw transaction ingestion to alert dispatch.

## Prerequisites
- Internal data platform SDK 4.x installed
- Access to transaction database
- ML model endpoint configured

## Quick Start
```bash
python scripts/analyze.py --mode batch --input transactions.csv
```

## Full Workflow
1. Ingest raw transactions: `python scripts/analyze.py --ingest`
2. Score with ML model: `python scripts/analyze.py --score`
3. Generate alerts: `python scripts/analyze.py --alert`

## References
- [API Documentation](references/api.md)
- [Advanced Patterns](references/v2/advanced.md)

## Troubleshooting
**Error**: Model endpoint unreachable → **Fix**: Check VPN and endpoint config.
**Error**: SDK version mismatch → **Fix**: Run `pip install internal-sdk==4.x`.
"""

with open(os.path.join(draft_dir, "SKILL.md"), "w") as f:
    f.write(skill_md_content)

# scripts/analyze.py — valid, keep it
with open(os.path.join(draft_dir, "scripts", "analyze.py"), "w") as f:
    f.write("#!/usr/bin/env python3\nimport argparse\nparser = argparse.ArgumentParser()\nparser.add_argument('--mode')\nparser.add_argument('--input')\nparser.add_argument('--ingest', action='store_true')\nparser.add_argument('--score', action='store_true')\nparser.add_argument('--alert', action='store_true')\nargs = parser.parse_args()\nprint('analyze.py executed')\n")

# assets/template.json — valid, keep it
with open(os.path.join(draft_dir, "assets", "template.json"), "w") as f:
    f.write('{\n  "transaction_id": "",\n  "amount": 0,\n  "currency": "USD"\n}\n')

# references/v2/advanced.md — exists but violates one-level-deep rule (agent must fix reference)
with open(os.path.join(draft_dir, "references", "v2", "advanced.md"), "w") as f:
    f.write("# Advanced Patterns\nAdvanced fraud detection patterns.\n")

# docs/notes.md — in forbidden 4th subdirectory
with open(os.path.join(draft_dir, "docs", "notes.md"), "w") as f:
    f.write("# Internal Notes\nDraft notes for the fraud detection skill.\n")

# references/api.md is referenced but MISSING — agent must create it or fix the reference

print("Workspace initialized.")
print(f"Draft skill at: {draft_dir}")
print(f"Description length: {len(long_description)}")