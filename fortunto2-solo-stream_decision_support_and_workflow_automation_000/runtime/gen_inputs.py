import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Deep distractor directory structure ---
dirs = [
    "src/core",
    "src/api/v1",
    "src/api/v2",
    "tests/unit",
    "tests/integration",
    "config/env",
    "config/staging",
    "docs/architecture",
    "docs/specs",
    "docs/meetings",
    "scripts/deploy",
    "scripts/migrate",
    "data/raw",
    "data/processed",
    ".github/workflows",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/core/engine.py": "# Core processing engine\nclass Engine:\n    def run(self): pass\n",
    "src/api/v1/routes.py": "# Legacy API routes\nfrom flask import Blueprint\nbp = Blueprint('v1', __name__)\n",
    "src/api/v2/routes.py": "# New API routes\nfrom flask import Blueprint\nbp = Blueprint('v2', __name__)\n",
    "tests/unit/test_engine.py": "import pytest\ndef test_placeholder(): assert True\n",
    "tests/integration/test_api.py": "import pytest\ndef test_api_health(): assert True\n",
    "config/env/.env.example": "DATABASE_URL=postgresql://localhost/prod\nSECRET_KEY=changeme\n",
    "config/staging/settings.yaml": "debug: false\nlog_level: INFO\ndatabase:\n  pool_size: 10\n",
    "docs/architecture/system_overview.md": "# System Architecture\n\nThis doc describes the high-level architecture.\n\n## Components\n- API Layer\n- Processing Engine\n- Database\n",
    "docs/specs/api_spec_v2.md": "# API Specification v2\n\n## Endpoints\n- GET /health\n- POST /analyze\n- GET /results/{id}\n",
    "docs/meetings/2024-01-15-standup.md": "# Standup Notes 2024-01-15\n\n- Discussed pipeline delays\n- Action: review infra costs\n",
    "docs/meetings/2024-02-03-investor-call.md": "# Investor Call Notes\n\n- Q: What is the revenue model?\n- A: SaaS subscription with usage tiers\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\ndocker-compose up -d\n",
    "scripts/migrate/run_migrations.sh": "#!/bin/bash\npython manage.py migrate\n",
    "data/raw/sample_metrics.csv": "date,dau,revenue\n2024-01-01,1200,3400\n2024-01-02,1350,3800\n2024-01-03,980,2900\n",
    "data/processed/aggregated_metrics.json": '{"total_dau": 3530, "total_revenue": 10100, "period": "2024-01"}\n',
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - run: python -m pytest\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- THE DECISION SCENARIO: messy, real-world context for the agent to parse ---
decision_scenario = """\
# Strategic Decision Briefing — CONFIDENTIAL
**Prepared by:** Priya Mehta, CEO, NovaBiomics Inc.
**Date of briefing:** 2024-06-12
**Decision under review:** Whether to pivot our product focus from the current consumer wellness app (B2C) to an enterprise-grade clinical trials data management platform (B2B).

---

## Background

NovaBiomics launched 18 months ago with a consumer-facing wellness tracking app, "PulseCheck." We have 14,000 MAU, $38K MRR, and are burning $120K/month. At current trajectory we have ~7 months of runway left.

Our engineering team (6 engineers, 2 data scientists) has deep expertise in HL7/FHIR clinical data standards from prior jobs at Roche and Flatiron Health. Three months ago, we were approached by a CRO (contract research organization) who asked if we could build a purpose-built data pipeline for multi-site Phase II/III trial ingestion. They hinted at a $400K pilot contract.

## What We Know For Certain
- The clinical data space is complex and highly regulated (21 CFR Part 11, HIPAA, GxP).
- Our team has genuine competence in FHIR pipelines — this is NOT a stretch technically.
- The CRO contact (Dr. Alvarez) is still warm; we have a follow-up call scheduled for June 20.
- B2C wellness is extremely crowded; Apple Health and Google Fit are squeezing us.
- We've spoken to 4 other CROs informally — 3 expressed pain with current EDC/data tools.

## What We Are Assuming
- That $400K pilot → $2M ARR is realistic within 18 months if pilot succeeds.
- That our team can ramp on GxP/validation requirements without external consultants.
- That we won't lose our consumer audience (we'd wind down PulseCheck gradually).

## Timeline & Reversibility
- Timeline: This is a 3-year strategic commitment minimum. Clinical sales cycles are 6-18 months.
- Reversibility: Pivoting back to B2C after 12 months in B2B is extremely difficult — brand, team culture, and investor narrative would all shift.
- If we do nothing, we likely run out of money in 7 months.

## Minimum Viable Action
- We could run a 6-week spike: assign 2 engineers to build a proof-of-concept FHIR ingestion pipeline for Dr. Alvarez's specific trial dataset.
- Total cost of spike: ~$40K fully-loaded (salary allocation + infra).
- If pilot fails or CRO goes cold, we lose $40K but gain validated market intelligence.

## Risk / Reward Analysis
- Worst case: Spike fails, CRO ghosts us, we've spent $40K and 6 weeks. We still have 5 months runway to try something else or shut down gracefully.
- Best case: Pilot converts, we have $400K+ and a referenceable client to raise Series A.
- Opportunity cost of NOT pivoting: Almost certain slow death in B2C. Apple's recent HealthKit expansion directly cannibalizes our core feature.
- Asymmetric upside: $40K risk, potential $2M ARR. 50:1 ratio.

## Stakeholder & Network Considerations
- Our lead investor (Sequoia scout) has explicitly said they prefer B2B health infrastructure plays.
- Two of our senior engineers are more excited about clinical data work — retention risk if we stay B2C.
- Our 14,000 B2C users would be impacted — gradual wind-down of PulseCheck, app sunset ~9 months.
- Dr. Alvarez's team (5 clinical data managers) would be direct beneficiaries of the new platform.
- Negative: Some early PulseCheck advocates (health influencers with ~50K followers) might publicly criticize the pivot.

## Personal / Foundational Alignment
- Priya: "I started this company to make clinical research faster, not to count steps. PulseCheck was a pivot I did under investor pressure. I want to go back to the mission."
- Co-founder Raj: "I'd rather spend 5 years building infrastructure that speeds up cancer drug trials than 5 years optimizing consumer engagement metrics."
- Both founders explicitly said they would regret NOT attempting the clinical platform.

---

## Requested Output
Please produce a formal structured analysis of this decision using the company's internal decision framework. The analysis should be saved to the project's decision log for board review. Use today's date. The output filename should be: `2024-06-12-novaBiomics-pivot-decision.md`
"""

scenario_path = workspace / "docs" / "strategic_decision_brief.md"
scenario_path.write_text(decision_scenario)

# Also add a partial/wrong old decision record as a distractor (wrong format, incomplete)
old_decision = """\
Decision: Hire a Head of Sales
Date: 2024-03-01
Pros:
- Faster enterprise sales
- Frees up founder time
Cons:
- Expensive
- Hard to find good fit
Verdict: Maybe
"""
(workspace / "docs" / "old_decision_draft.txt").write_text(old_decision)

print("Workspace generated successfully.")
print("Key file: /workspace/docs/strategic_decision_brief.md")