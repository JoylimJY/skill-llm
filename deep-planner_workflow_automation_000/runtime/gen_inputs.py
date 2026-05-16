import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Distractor directory structure ──────────────────────────────────────────
dirs = [
    "projects/saas-launch/briefs",
    "projects/saas-launch/research/raw",
    "projects/saas-launch/research/processed",
    "projects/saas-launch/marketing",
    "projects/legacy-q3/reports",
    "projects/legacy-q3/data",
    "team/onboarding",
    "team/retrospectives",
    "archive/2023/planning",
    "archive/2023/design",
    "tools/scripts",
    "tools/templates",
    ".todolist",   # pre-existing .todolist dir with an interrupted task
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "projects/saas-launch/briefs/product-brief-v2.md": """# Product Brief v2
## Overview
ClearMetrics is a B2B analytics SaaS targeting mid-market finance teams.
Launch target: Q3 2025.

## Problem Statement
Finance teams spend 40% of their time in spreadsheets that break.

## Proposed Solution
Automated KPI dashboards with anomaly detection.
""",

    "projects/saas-launch/briefs/stakeholder-list.txt": """CFO - sponsor
VP Engineering - technical lead
Head of Product - owner
Marketing Lead - GTM
Sales Director - pipeline
""",

    "projects/saas-launch/research/raw/competitor-notes.txt": """Competitors noted (rough):
- Mosaic FP&A: strong forecasting, weak integrations
- Pigment: visual, expensive
- Anaplan: enterprise, complex
- Vena Solutions: Excel-native, familiar but clunky
NOTE: prices not confirmed, gathered from rep conversations
""",

    "projects/saas-launch/research/raw/interview-notes-2024-11-15.md": """# Customer Interview Notes
Interviewee: Head of FP&A, Series B startup
Pain: exports from ERP are always 2 days stale
Wants: real-time Slack alerts when budget deviation > 5%
""",

    "projects/saas-launch/research/processed/segment-sizing.csv": """segment,tam_estimate,confidence
mid-market,2.1B,low
enterprise,8.4B,medium
smb,0.6B,high
""",

    "projects/saas-launch/marketing/gtm-draft.md": """# GTM Draft
Channel priority: outbound SDR, content, partnerships
Budget: TBD pending finance approval
""",

    "projects/legacy-q3/reports/q3-analysis.md": """# Q3 Analysis
Revenue: $1.2M ARR
Churn: 4.2%
NPS: 34
""",

    "projects/legacy-q3/data/raw-export-2024-09-30.csv": """date,event,value
2024-09-01,signup,142
2024-09-15,churn,12
2024-09-30,expansion,3
""",

    "team/onboarding/new-hire-checklist.md": """# New Hire Checklist
- [ ] Slack access
- [ ] Notion access
- [ ] 1:1 with manager (week 1)
- [ ] Shadow a customer call (week 2)
""",

    "team/retrospectives/retro-2025-01.md": """# Retro Jan 2025
What went well: shipped dashboard v2 on time
What didn't: QA bottleneck on last day
Action: add staging freeze 48h before release
""",

    "archive/2023/planning/roadmap-2023.md": """# 2023 Roadmap (archived)
Q1: Data connectors
Q2: Custom alerts
Q3: Mobile app (deprioritized)
Q4: SSO & enterprise auth
""",

    "archive/2023/design/wireframes-notes.txt": """Wireframes in Figma (see link in Notion).
Notes from designer: avoid red/green for colorblind accessibility.
""",

    "tools/scripts/data-clean.py": """# placeholder: data cleaning utilities
import pandas as pd

def clean_csv(path):
    df = pd.read_csv(path)
    return df.dropna()
""",

    "tools/templates/report-template.md": """# Report Template
## Executive Summary
## Findings
## Recommendations
## Appendix
""",
}

for rel_path, content in distractor_files.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ── 3. THE KEY TRAP: a pre-existing in-progress .todolist file ─────────────────
# This file was "interrupted" mid-task — the agent MUST detect it in Step 0
interrupted_date = "20250108"
interrupted_filename = f"{interrupted_date}-competitive-pricing-research.md"
interrupted_content = """# Competitive Pricing Research
Created: 2025-01-08 14:22
Status: in-progress

## Goal
Compile a pricing comparison table for ClearMetrics vs top 4 competitors to inform Q3 pricing strategy.

## TodoList
- [x] 1. Identify top 4 competitors from analyst reports `web search`
- [x] 2. Scrape public pricing pages for each competitor `browser`
- [ ] 3. Normalize pricing tiers into a comparison table `internal reasoning` ← current
- [ ] 4. Identify pricing gaps and positioning opportunities `internal reasoning`
- [ ] 5. Write pricing recommendation memo `content creation`

## Assumptions & Confirmations
- Assumed: "top competitors" means those with overlapping ICP (mid-market finance)
- Confirmed: scope is public pricing only, no sales rep calls

## Progress
2/5 steps completed
"""

(workspace / ".todolist" / interrupted_filename).write_text(interrupted_content)

# ── 4. A second older completed .todolist (distractor — should NOT be surfaced) ──
old_completed_filename = "20241203-onboarding-content-audit.md"
old_completed_content = """# Onboarding Content Audit
Created: 2024-12-03 09:00
Status: completed

## Goal
Audit all onboarding docs for accuracy and flag outdated sections.

## TodoList
- [x] 1. List all onboarding documents `internal reasoning`
- [x] 2. Check each for last-updated date `internal reasoning`
- [x] 3. Flag sections referencing deprecated features `internal reasoning`

## Assumptions & Confirmations
- Assumed: "onboarding docs" means team/onboarding/ folder only

## Progress
3/3 steps completed
"""
(workspace / ".todolist" / old_completed_filename).write_text(old_completed_content)

print("Workspace generated successfully.")
print(f"Files in .todolist/: {list((workspace / '.todolist').iterdir())}")