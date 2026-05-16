import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "company/strategy/2024",
    "company/strategy/2023",
    "company/hr/onboarding",
    "company/hr/policies",
    "company/finance/q3",
    "company/finance/q2",
    "teams/engineering/okrs",
    "teams/engineering/sprints",
    "teams/product/okrs",
    "teams/product/roadmap",
    "teams/design/assets",
    "teams/design/specs",
    "archive/2023_q4",
    "archive/2023_q3",
    "reports/drafts",
    "reports/published",
    "tools/scripts",
    "tools/templates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "company/strategy/2024/vision.txt": "NovaBio: Accelerate life-saving diagnostics through software innovation.",
    "company/strategy/2023/annual_plan.txt": "Legacy plan from 2023. Do not use.",
    "company/hr/onboarding/checklist.txt": "Day 1: Setup laptop\nDay 2: Meet team\nDay 3: Shadow engineer",
    "company/hr/policies/pto_policy.md": "# PTO Policy\nEmployees accrue 15 days/year.",
    "company/finance/q3/budget_variance.csv": "Category,Budgeted,Actual\nR&D,500000,487000\nSales,200000,215000",
    "company/finance/q2/summary.txt": "Q2 closed with 3% under budget across all divisions.",
    "teams/engineering/sprints/sprint_22.txt": "Sprint 22: Focus on API stability and test coverage.",
    "teams/product/roadmap/2024_h2.txt": "H2 focus: ML-assisted diagnostics, HIPAA compliance module.",
    "teams/design/assets/brand_guidelines.txt": "Primary color: #1A73E8. Font: Inter.",
    "teams/design/specs/dashboard_v2.txt": "Dashboard redesign spec. See Figma link (internal).",
    "archive/2023_q4/retrospective.txt": "Q4 2023: Shipped 3/5 objectives. Main blocker: infra instability.",
    "archive/2023_q3/okr_snapshot.txt": "Q3 2023 snapshot archived. Average score: 0.58.",
    "tools/scripts/okr_export.sh": "#!/bin/bash\n# Exports OKRs from internal tool\necho 'Not configured'",
    "tools/templates/meeting_notes.txt": "Date:\nAttendees:\nAgenda:\nAction Items:",
    "reports/drafts/q2_eng_draft.txt": "Draft Q2 engineering report. In progress.",
    "reports/published/q1_all_teams.txt": "Q1 All-Teams Report: Published March 2024.",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Core problem input: messy raw Q3 OKR data ───────────────────────────────
# Deliberately contains:
# 1. A team with too many Objectives (6 > max 5)
# 2. A team with a KR count violation (7 KRs on one objective > max 5)
# 3. One team sandbagging (all scores 0.9-1.0, average well above 0.7)
# 4. One team in distress (average below 0.3)
# 5. Mixed scoring needing correct color-coding
# 6. Vague/qualitative KRs (a known antipattern)
# 7. Missing scoring data (null scores that need handling)

raw_okr_data = {
    "quarter": "Q3-2024",
    "company": "NovaBio",
    "division": "Engineering & Product",
    "teams": [
        {
            "team_name": "Platform Engineering",
            "team_lead": "Yusuf Adebayo",
            "objectives": [
                {
                    "id": "PE-O1",
                    "title": "Achieve rock-solid infrastructure reliability",
                    "key_results": [
                        {"id": "PE-O1-KR1", "description": "Reduce P1 incident count from 12 to under 3 per month", "target": 3, "unit": "incidents/month", "final_value": 2, "score": None},
                        {"id": "PE-O1-KR2", "description": "Achieve 99.95% uptime across all production services", "target": 99.95, "unit": "%", "final_value": 99.87, "score": None},
                        {"id": "PE-O1-KR3", "description": "Reduce mean-time-to-recovery (MTTR) from 45 min to under 10 min", "target": 10, "unit": "minutes", "final_value": 14, "score": None},
                    ]
                },
                {
                    "id": "PE-O2",
                    "title": "Make developers love the deployment pipeline",
                    "key_results": [
                        {"id": "PE-O2-KR1", "description": "Cut average CI/CD pipeline duration from 22 min to under 8 min", "target": 8, "unit": "minutes", "final_value": 7.5, "score": None},
                        {"id": "PE-O2-KR2", "description": "Improve developer NPS for platform tools from 22 to 55", "target": 55, "unit": "NPS", "final_value": 48, "score": None},
                        {"id": "PE-O2-KR3", "description": "Reduce deployment rollback rate from 18% to under 5%", "target": 5, "unit": "%", "final_value": 4.2, "score": None},
                        {"id": "PE-O2-KR4", "description": "Improve pipeline documentation coverage", "target": None, "unit": None, "final_value": None, "score": None, "note": "qualitative — no measurable target set"},
                    ]
                },
                {
                    "id": "PE-O3",
                    "title": "Drive security-first engineering culture",
                    "key_results": [
                        {"id": "PE-O3-KR1", "description": "Complete SOC2 Type II readiness audit with zero critical findings", "target": 0, "unit": "critical findings", "final_value": 0, "score": None},
                        {"id": "PE-O3-KR2", "description": "Achieve 100% of engineers completing security training by week 6", "target": 100, "unit": "%", "final_value": 100, "score": None},
                        {"id": "PE-O3-KR3", "description": "Reduce open critical CVEs from 31 to under 5", "target": 5, "unit": "CVEs", "final_value": 4, "score": None},
                    ]
                },
            ]
        },
        {
            "team_name": "Data & ML",
            "team_lead": "Priya Krishnaswamy",
            "objectives": [
                {
                    "id": "DML-O1",
                    "title": "Ship production-grade diagnostic ML model v2",
                    "key_results": [
                        {"id": "DML-O1-KR1", "description": "Achieve model sensitivity ≥ 0.91 on holdout test set", "target": 0.91, "unit": "sensitivity", "final_value": 0.78, "score": None},
                        {"id": "DML-O1-KR2", "description": "Reduce model inference latency from 340ms to under 80ms", "target": 80, "unit": "ms", "final_value": 210, "score": None},
                        {"id": "DML-O1-KR3", "description": "Complete external clinical validation with ≥ 2 hospital partners", "target": 2, "unit": "partners", "final_value": 0, "score": None},
                        {"id": "DML-O1-KR4", "description": "Publish 1 peer-reviewed paper on diagnostic model methodology", "target": 1, "unit": "papers", "final_value": 0, "score": None},
                        {"id": "DML-O1-KR5", "description": "Reduce model training pipeline from 14 hours to under 4 hours", "target": 4, "unit": "hours", "final_value": 5.5, "score": None},
                        {"id": "DML-O1-KR6", "description": "Achieve data quality score ≥ 95% across all training datasets", "target": 95, "unit": "%", "final_value": 88, "score": None},
                        {"id": "DML-O1-KR7", "description": "Document all model cards and bias assessments", "target": None, "unit": None, "final_value": None, "score": None, "note": "qualitative — no measurable target set"},
                    ]
                },
                {
                    "id": "DML-O2",
                    "title": "Build trusted data infrastructure",
                    "key_results": [
                        {"id": "DML-O2-KR1", "description": "Reduce data pipeline SLA breaches from 23/month to under 4/month", "target": 4, "unit": "breaches/month", "final_value": 18, "score": None},
                        {"id": "DML-O2-KR2", "description": "Achieve ≥ 90% data catalog coverage for all production datasets", "target": 90, "unit": "%", "final_value": 41, "score": None},
                        {"id": "DML-O2-KR3", "description": "Cut data onboarding time for new analysts from 3 weeks to 3 days", "target": 3, "unit": "days", "final_value": 12, "score": None},
                    ]
                },
            ]
        },
        {
            "team_name": "Product Management",
            "team_lead": "Tomás Herrera",
            "objectives": [
                {
                    "id": "PM-O1",
                    "title": "Deepen customer understanding to drive better product decisions",
                    "key_results": [
                        {"id": "PM-O1-KR1", "description": "Conduct ≥ 40 structured customer interviews across 3 segments", "target": 40, "unit": "interviews", "final_value": 41, "score": None},
                        {"id": "PM-O1-KR2", "description": "Achieve ≥ 72 NPS from active enterprise customers", "target": 72, "unit": "NPS", "final_value": 74, "score": None},
                        {"id": "PM-O1-KR3", "description": "Publish monthly product insight digest for 3 consecutive months", "target": 3, "unit": "digests", "final_value": 3, "score": None},
                    ]
                },
                {
                    "id": "PM-O2",
                    "title": "Launch the HIPAA compliance module on time",
                    "key_results": [
                        {"id": "PM-O2-KR1", "description": "Deliver all 23 compliance feature tickets by sprint 18", "target": 23, "unit": "tickets", "final_value": 23, "score": None},
                        {"id": "PM-O2-KR2", "description": "Achieve zero severity-1 bugs at GA launch", "target": 0, "unit": "S1 bugs", "final_value": 0, "score": None},
                        {"id": "PM-O2-KR3", "description": "Onboard ≥ 5 enterprise beta customers to compliance module", "target": 5, "unit": "customers", "final_value": 5, "score": None},
                    ]
                },
                {
                    "id": "PM-O3",
                    "title": "Improve cross-functional alignment on roadmap",
                    "key_results": [
                        {"id": "PM-O3-KR1", "description": "Run ≥ 10 product–engineering syncs with ≥ 80% attendance", "target": 10, "unit": "syncs", "final_value": 10, "score": None},
                        {"id": "PM-O3-KR2", "description": "Achieve ≥ 85% roadmap predictability score (items shipped vs. planned)", "target": 85, "unit": "%", "final_value": 87, "score": None},
                        {"id": "PM-O3-KR3", "description": "Reduce roadmap change requests mid-sprint from avg 8 to under 2", "target": 2, "unit": "changes/sprint", "final_value": 1.8, "score": None},
                    ]
                },
                {
                    "id": "PM-O4",
                    "title": "Grow product-qualified leads pipeline",
                    "key_results": [
                        {"id": "PM-O4-KR1", "description": "Generate ≥ 120 PQLs via in-product upgrade prompts", "target": 120, "unit": "PQLs", "final_value": 122, "score": None},
                        {"id": "PM-O4-KR2", "description": "Achieve ≥ 18% trial-to-paid conversion rate", "target": 18, "unit": "%", "final_value": 19.2, "score": None},
                        {"id": "PM-O4-KR3", "description": "Launch ≥ 3 self-serve onboarding improvements tracked by activation rate", "target": 3, "unit": "improvements", "final_value": 3, "score": None},
                    ]
                },
                {
                    "id": "PM-O5",
                    "title": "Build a world-class product operations function",
                    "key_results": [
                        {"id": "PM-O5-KR1", "description": "Implement OKR tracking tooling for product team", "target": None, "unit": None, "final_value": None, "score": None, "note": "qualitative — no measurable target set"},
                        {"id": "PM-O5-KR2", "description": "Achieve ≥ 90% on-time delivery of product specs (2 days before sprint start)", "target": 90, "unit": "%", "final_value": 93, "score": None},
                        {"id": "PM-O5-KR3", "description": "Hire and onboard 2 Associate PMs by week 8", "target": 2, "unit": "hires", "final_value": 2, "score": None},
                    ]
                },
                {
                    "id": "PM-O6",
                    "title": "Establish data-driven product culture",
                    "key_results": [
                        {"id": "PM-O6-KR1", "description": "Define and instrument ≥ 15 product analytics events", "target": 15, "unit": "events", "final_value": 16, "score": None},
                        {"id": "PM-O6-KR2", "description": "Have ≥ 80% of product decisions backed by quantitative data", "target": 80, "unit": "%", "final_value": 82, "score": None},
                        {"id": "PM-O6-KR3", "description": "Reduce time-to-insight for product analytics from 5 days to 1 day", "target": 1, "unit": "days", "final_value": 1, "score": None},
                    ]
                },
            ]
        },
    ]
}

# Write to the engineering/okrs folder
with open(os.path.join(workspace, "teams/engineering/okrs/q3_2024_raw.json"), "w") as f:
    json.dump(raw_okr_data, f, indent=2)

# Also write a brief context file
context = """Q3 2024 OKR Review — NovaBio Engineering & Product Division

This folder contains the raw OKR data export for Q3 2024.
The data was exported from our internal tracker and has NOT been scored or reviewed.

Key Results marked with a "note" field were submitted without measurable targets.
Scores are all null — these need to be computed based on final vs target values.

Please use this data to produce the Q3 retrospective analysis package.

Contact: strategy-ops@novabio.internal
"""
with open(os.path.join(workspace, "teams/engineering/okrs/CONTEXT.txt"), "w") as f:
    f.write(context)

# Write a partial/broken previous quarter example to serve as a misleading template
broken_prev = {
    "quarter": "Q2-2024",
    "note": "INCOMPLETE — scoring was done on 0-100% scale, NOT 0.0-1.0. DO NOT use this format.",
    "teams": [
        {"team": "Platform", "avg_score_pct": 72, "color": "green"},
        {"team": "Data & ML", "avg_score_pct": 45, "color": "yellow"},
    ]
}
with open(os.path.join(workspace, "teams/engineering/okrs/q2_2024_BROKEN_example.json"), "w") as f:
    json.dump(broken_prev, f, indent=2)

print("Workspace generated successfully.")