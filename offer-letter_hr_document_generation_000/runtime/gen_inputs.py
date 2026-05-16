import os
import random

random.seed(42)

base = "/workspace"

# Create a realistic HR department directory structure with distractor files
dirs = [
    "hr/recruiting/2025/Q1",
    "hr/recruiting/2025/Q2",
    "hr/recruiting/archive/2024",
    "hr/onboarding/templates",
    "hr/onboarding/completed",
    "hr/payroll/configs",
    "hr/benefits/plans",
    "hr/legal/contracts",
    "hr/legal/nda_templates",
    "hr/headcount/approved",
    "hr/headcount/pipeline",
    "hr/performance/reviews/2024",
    "company/policies",
    "company/org_chart",
    "finance/compensation_bands",
    "finance/equity_pool",
    "it/new_hire_checklist",
    "it/equipment_requests",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ---- DISTRACTOR FILES ----

# 1. Old offer letter template (wrong format, different company)
with open(os.path.join(base, "hr/onboarding/templates/old_offer_template_2022.txt"), "w") as f:
    f.write("""OFFER LETTER TEMPLATE v2 (DEPRECATED - DO NOT USE)
To: [CANDIDATE]
Role: [ROLE]
Salary: [SALARY]
Start: [START]
Please sign and return.
HR Team
""")

# 2. Completed offer for different person (distractor)
with open(os.path.join(base, "hr/onboarding/completed/offer_james_wu_2024.txt"), "w") as f:
    f.write("""NovaBio Therapeutics
Offer to James Wu - Data Scientist
Salary: $130,000/year
Start: September 1, 2024
Signed and returned.
""")

# 3. Headcount approval memo
with open(os.path.join(base, "hr/headcount/approved/HC_2025_approved_roles.txt"), "w") as f:
    f.write("""APPROVED HEADCOUNT 2025

Role: Director of Clinical Operations
Dept: Clinical
Level: L7
Budget Band: $190,000 - $220,000
Equity Pool Allocation: 18,000 options
Status: OFFER PENDING - Candidate selected

Role: Senior Bioinformatics Engineer
Dept: R&D
Level: L5
Budget Band: $155,000 - $175,000
Status: Sourcing

Role: Regulatory Affairs Specialist
Dept: Legal/Regulatory
Level: L4
Budget Band: $110,000 - $130,000
Status: Interview stage
""")

# 4. Equity pool tracker
with open(os.path.join(base, "finance/equity_pool/equity_grants_2025.csv"), "w") as f:
    f.write("""candidate,role,options,vest_years,cliff_years,approved_by
James Wu,Data Scientist,8000,4,1,CFO
PENDING,Director Clinical Ops,18000,4,1,CFO
""")

# 5. Compensation bands
with open(os.path.join(base, "finance/compensation_bands/2025_bands.txt"), "w") as f:
    f.write("""2025 COMPENSATION BANDS - CONFIDENTIAL

L4: $100k-$130k base | Bonus: up to 10% | Options: 5,000-8,000
L5: $140k-$175k base | Bonus: up to 15% | Options: 8,000-14,000
L6: $170k-$210k base | Bonus: up to 20% | Options: 14,000-20,000
L7: $190k-$230k base | Bonus: up to 25% | Options: 16,000-22,000
""")

# 6. Benefits plan summary
with open(os.path.join(base, "hr/benefits/plans/2025_benefits_summary.txt"), "w") as f:
    f.write("""NOVABIO THERAPEUTICS - 2025 BENEFITS OVERVIEW

Medical/Dental/Vision: Aetna PPO - 90% employee / 75% dependent coverage
401(k): Fidelity platform - 5% company match, vesting immediate
PTO: 25 days annually + 11 federal holidays
Additional:
  - $2,000 annual learning & development stipend
  - Commuter benefits (pre-tax)
  - Life insurance (2x salary)
  - 12 weeks parental leave
""")

# 7. IT new hire checklist (distractor)
with open(os.path.join(base, "it/new_hire_checklist/standard_checklist.txt"), "w") as f:
    f.write("""NEW HIRE IT CHECKLIST
- Laptop provisioning (MacBook Pro 14")
- Email setup (@novabio.com)
- Slack access
- VPN credentials
- Badge access request
- Lab system access (if applicable)
""")

# 8. Legal NDA template (distractor)
with open(os.path.join(base, "hr/legal/nda_templates/standard_nda.txt"), "w") as f:
    f.write("""MUTUAL NON-DISCLOSURE AGREEMENT
Between NovaBio Therapeutics, Inc. and [PARTY]
...standard NDA boilerplate...
""")

# 9. Performance reviews distractor
with open(os.path.join(base, "hr/performance/reviews/2024/review_cycle_summary.txt"), "w") as f:
    f.write("""2024 Performance Review Summary
Completed: 142 reviews
Average score: 3.6/5.0
Top performers flagged for promotion consideration: 18
""")

# 10. Org chart note
with open(os.path.join(base, "company/org_chart/clinical_dept_structure.txt"), "w") as f:
    f.write("""CLINICAL OPERATIONS ORG CHART

SVP Clinical Development: Dr. Priya Nair
  |
  +-- Director of Clinical Operations: [VACANT - HIRING]
  |     Reports directly to: Dr. Priya Nair, SVP Clinical Development
  |
  +-- Clinical Trial Manager: Kenji Matsuda
  +-- CRA Lead: Beatriz Oliveira
""")

# 11. Recruiting pipeline notes
with open(os.path.join(base, "hr/recruiting/2025/Q2/pipeline_notes.txt"), "w") as f:
    f.write("""Q2 2025 RECRUITING PIPELINE NOTES

Director of Clinical Operations:
  - Top candidate: Dr. Marcus Webb
  - Interviews completed: 5 rounds (panel, technical, executive)
  - Reference checks: PASSED (3 refs contacted)
  - Background check: PENDING (to be initiated upon offer acceptance)
  - Work auth: US citizen, no sponsorship needed
  - Current employer: Novartis (notice period: 4 weeks)
  
Notes from final interview debrief (rec'd from Dr. Nair):
  "Marcus has deep Phase II/III trial oversight experience and led 
   a team of 12 at Novartis. Strong operational mindset. Recommend offer."
""")

# ---- THE MAIN PROBLEM: Messy, scattered intake form ----

# 12. Recruiter's raw intake notes (messy, incomplete structure)
with open(os.path.join(base, "hr/recruiting/2025/Q2/webb_offer_intake_DRAFT.txt"), "w") as f:
    f.write("""OFFER INTAKE NOTES - DRAFT - DO NOT CIRCULATE
Prepared by: Leticia Gomez, Talent Acquisition
Date of notes: May 19, 2025

CANDIDATE:
Full name: Dr. Marcus Webb (he/him)
Personal email: marcus.webb.phd@gmail.com  <-- for sending offer

ROLE INFO:
Title: Director of Clinical Operations
Dept: Clinical Operations
Reports to: Dr. Priya Nair (SVP, Clinical Development) -- confirmed with Priya 5/18
Location: South San Francisco office (hybrid ok - Mondays + Wednesdays in office)
FT exempt

COMPENSATION (approved by finance 5/16):
Base: $205,000 per year
Pay schedule: bi-weekly (26 periods)
Signing bonus: $15,000 - payable within 30 days of start date (subject to 1-year clawback if voluntary resignation)
Annual bonus target: 20% of base
Equity: 18,000 stock options, standard 4-year vest with 1-year cliff

PROPOSED START: August 4, 2025

OFFER EXPIRY: candidate must respond by June 2, 2025

CONTINGENCIES:
- background check (standard criminal + employment verification)
- i9 / work eligibility verification

BENEFITS: standard 2025 package (see benefits doc)

HIRING MANAGER CONTACT for letter sign-off:
Dr. Priya Nair
SVP, Clinical Development
priya.nair@novabio.com | (650) 555-0182

COMPANY ADDRESS FOR LETTERHEAD:
NovaBio Therapeutics, Inc.
400 Oyster Point Blvd, Suite 300
South San Francisco, CA 94080
""")

# 13. Finance approval email dump (additional distractor with some relevant data)
with open(os.path.join(base, "hr/recruiting/2025/Q2/finance_approval_email.txt"), "w") as f:
    f.write("""From: Carlos Mendez <c.mendez@novabio.com> (Finance)
To: Leticia Gomez <l.gomez@novabio.com>
Date: May 16, 2025
Subject: RE: Offer approval - Director Clinical Ops

Leticia,

Approved. Numbers are within band:
- Base: $205K
- Signing: $15K (standard clawback applies)
- Bonus: 20% target
- Options: 18,000 (pool allocation confirmed)

One note: please make sure the equity section references that full terms
are in the separate Option Agreement. That's a legal requirement on our end.

Thanks,
Carlos
""")

# 14. Company policy doc (distractor)
with open(os.path.join(base, "company/policies/at_will_employment_policy.txt"), "w") as f:
    f.write("""EMPLOYMENT POLICY - AT-WILL STATEMENT

All employment at NovaBio Therapeutics, Inc. is at-will, meaning either
party may terminate the employment relationship at any time, with or without
cause or advance notice, unless otherwise specified in a separate written
agreement signed by the CEO.

This offer letter does not constitute a contract of employment.
""")

# 15. Archived 2024 offer (distractor - different format)
with open(os.path.join(base, "hr/recruiting/archive/2024/offer_chen_archived.txt"), "w") as f:
    f.write("""ARCHIVED - SIGNED COPY
Candidate: Linda Chen | Role: Senior Scientist | Start: Jan 15, 2024
Salary: $148,000 | Bonus: 12% | Options: 9,000
Signed: Jan 8, 2024
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for file in files:
        filepath = os.path.join(root, file)
        print(f"  {filepath}")