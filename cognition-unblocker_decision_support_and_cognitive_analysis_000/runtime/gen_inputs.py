import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create deeply nested distractor directory structure ---
dirs = [
    "docs/company_policy",
    "docs/hr/benefits",
    "docs/hr/performance_reviews",
    "projects/alpha/specs",
    "projects/alpha/meetings",
    "projects/beta/design",
    "personal/notes/2023",
    "personal/notes/2024",
    "templates/analysis",
    "templates/reports",
    "archive/decisions/2022",
    "archive/decisions/2023",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Create distractor files ---
distractor_files = {
    "docs/company_policy/leave_policy.txt": "Annual leave: 15 days. Sick leave: 10 days. Maternity: 180 days.",
    "docs/company_policy/remote_work.txt": "Remote work is allowed up to 3 days per week for senior staff.",
    "docs/hr/benefits/health_insurance.txt": "Comprehensive health plan covers employee + spouse + 2 children.",
    "docs/hr/benefits/stock_options.txt": "Vesting schedule: 4 years with 1-year cliff.",
    "docs/hr/performance_reviews/template_2024.txt": "Q1: Goal Setting. Q2: Mid-year Check-in. Q4: Annual Review.",
    "projects/alpha/specs/requirements_v1.txt": "Feature A: user auth. Feature B: dashboard. Feature C: reporting.",
    "projects/alpha/specs/requirements_v2.txt": "Updated: Feature A v2, Feature D: API integration.",
    "projects/alpha/meetings/notes_jan.txt": "Sprint planning. Backlog grooming. Team velocity: 42 points.",
    "projects/beta/design/wireframes_notes.txt": "Login page, main dashboard, settings panel. Dark mode required.",
    "personal/notes/2023/journal.txt": "Feeling overwhelmed with current workload. Need to think about future.",
    "personal/notes/2024/goals.txt": "1. Learn more about entrepreneurship. 2. Save 6 months emergency fund.",
    "templates/analysis/swot_blank.txt": "STRENGTHS: \nWEAKNESSES: \nOPPORTUNITIES: \nTHREATS: ",
    "templates/analysis/pestle_blank.txt": "Political:\nEconomic:\nSocial:\nTechnological:\nLegal:\nEnvironmental:",
    "templates/reports/quarterly_template.txt": "Q[N] Report\nExecutive Summary:\nKey Metrics:\nChallenges:\nNext Steps:",
    "archive/decisions/2022/vendor_selection.txt": "Selected Vendor B over Vendor A based on cost and support quality.",
    "archive/decisions/2023/tech_stack.txt": "Chose React + FastAPI + PostgreSQL. Rationale: team familiarity.",
}

for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content, encoding="utf-8")

# --- Create the MAIN INPUT: the user scenario ---
user_scenario = """
[User Scenario - Decision Support Request]

Name: Li Wei (李伟)
Age: 32
Current Situation: Senior Software Engineer at a large state-owned telecom company (中兴通讯). 
Annual salary: ~400,000 RMB. Team of 5 reports to him. Has been in this role for 6 years.
Family: Married, one child age 3. Mortgage in Shenzhen (monthly payment: 12,000 RMB).
Savings: ~600,000 RMB liquid savings.

The Dilemma:
Li Wei has spent the last 8 months building an AI-powered productivity tool for enterprise clients on 
the side (nights and weekends). He has 3 paying pilot customers (each paying 2,000 RMB/month = 6,000 
RMB/month total MRR). Two potential customers have expressed serious interest but want to see full-time 
commitment before signing.

He is deeply conflicted about whether to quit his stable, well-paying job to pursue this startup full-time.

What he says he cares about most:
- "I don't want to regret not trying, but I also can't afford to fail — my family depends on my income."
- "I think the market window for this kind of AI tool might be 12-18 months before it gets crowded."
- "I've been feeling increasingly unfulfilled at work. The corporate bureaucracy is suffocating me."

What he's afraid of:
- Running out of money before the business becomes self-sustaining
- Damaging his career track record if the startup fails
- Putting too much pressure on his spouse and affecting their relationship

What he has going for him:
- Strong technical skills (AI/ML background)
- A mentor who is a successful serial entrepreneur willing to advise him
- His spouse is currently working (income: ~200,000 RMB/year)

He has NOT been able to make a decision after 3 months of thinking about it. He feels cognitively blocked.

Please produce a complete structured decision-analysis for Li Wei.

Output file: decision_analysis.md
"""

(workspace / "user_scenario.txt").write_text(user_scenario.strip(), encoding="utf-8")

# --- Create a partial/misleading template as a distractor ---
misleading_template = """# Decision Analysis Template (OLD FORMAT - DO NOT USE)

## Problem Statement
[Write problem here]

## Pros and Cons
| Option | Pros | Cons |
|--------|------|------|
| Option A | ... | ... |
| Option B | ... | ... |

## Recommendation
[Write recommendation here]

## Next Steps
[Write next steps here]
"""

(workspace / "templates/analysis/old_decision_template.md").write_text(misleading_template, encoding="utf-8")

# --- Create a fake "example output" that uses wrong structure ---
wrong_example = """# Example Decision Analysis (Incorrect Structure Example)

## Summary
The user is stuck between two choices.

## Options
1. Stay at job
2. Quit and start company

## My Recommendation
I recommend option 2 because entrepreneurship is rewarding.
"""

(workspace / "archive/decisions/2023/example_bad_analysis.md").write_text(wrong_example, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")