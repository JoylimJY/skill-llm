import os
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/company_docs/legal",
    "workspace/company_docs/finance",
    "workspace/company_docs/hr",
    "workspace/product/roadmap",
    "workspace/product/specs",
    "workspace/marketing/campaigns",
    "workspace/marketing/brand",
    "workspace/marketing/social",
    "workspace/sales/decks",
    "workspace/sales/crm_exports",
    "workspace/research/competitors",
    "workspace/research/customer_interviews",
    "workspace/ops/infra",
    "workspace/ops/logs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- DISTRACTOR FILES ---

with open("workspace/company_docs/legal/nda_template.txt", "w") as f:
    f.write("NON-DISCLOSURE AGREEMENT\nThis agreement is between PawManager Inc. and the undersigned party...\n[Standard NDA boilerplate - not relevant to positioning]\n")

with open("workspace/company_docs/finance/q2_budget.csv", "w") as f:
    f.write("Category,Budget,Spent\nMarketing,50000,32000\nSales,80000,71000\nR&D,120000,98000\nOps,30000,28000\n")

with open("workspace/company_docs/hr/hiring_plan_2024.txt", "w") as f:
    f.write("Hiring Plan 2024\n- 2x Backend Engineers\n- 1x Marketing Manager\n- 1x Customer Success\nTarget: Q3 completion\n")

with open("workspace/product/roadmap/q3_roadmap.txt", "w") as f:
    f.write("Q3 2024 Roadmap\n- Telemedicine module (v0.3)\n- Insurance billing auto-fill (v1.2)\n- Mobile app for vets (v0.8)\n- SMS appointment reminders (done)\n")

with open("workspace/product/specs/api_spec_v2.yaml", "w") as f:
    f.write("openapi: 3.0.0\ninfo:\n  title: PawManager API\n  version: 2.1.0\npaths:\n  /appointments:\n    get:\n      summary: List appointments\n  /patients:\n    get:\n      summary: List animal patients\n")

with open("workspace/marketing/campaigns/email_campaign_draft.txt", "w") as f:
    f.write("Subject: Tired of double-bookings?\nBody: Hey Dr. Smith, we know running a vet clinic is chaos...\n[Draft - not finalized]\n")

with open("workspace/marketing/brand/logo_guidelines.txt", "w") as f:
    f.write("Brand Colors: #2A7DE1 (primary), #F5A623 (accent)\nFont: Inter 400/700\nLogo usage: minimum 40px height\nDo not stretch or recolor the logo.\n")

with open("workspace/marketing/social/twitter_posts_draft.txt", "w") as f:
    f.write("Tweet 1: 'Running a vet clinic shouldn't mean drowning in paperwork. #VetLife'\nTweet 2: 'Your patients have four legs. Your software shouldn't trip over two feet. #PawManager'\n")

with open("workspace/sales/decks/investor_pitch_notes.txt", "w") as f:
    f.write("Slide 3 talking points:\n- Market size: $4.2B vet practice management\n- We target independent clinics\n- Current MRR: $47k\n- NPS: 71\nDon't mention the failed enterprise pivot.\n")

with open("workspace/sales/crm_exports/leads_oct2024.csv", "w") as f:
    f.write("Name,Clinic,Stage,Notes\nDr. Carter,Happy Paws Clinic,Demo Scheduled,Owner of 1-location clinic\nDr. Nguyen,Eastside Animal Hospital,Closed Won,Switched from VetPro\nDr. Mills,Riverside Pets,Lost,Went with ezyVet - said needed multi-location\n")

with open("workspace/research/competitors/competitor_notes_raw.txt", "w") as f:
    f.write("""COMPETITOR RESEARCH NOTES (messy internal doc - not organized)

VetPro:
- been around since 2008
- massive feature set, huge enterprise focus
- used by large multi-location chains
- clunky UI, takes 3 months to onboard
- pricing: $800-$2000/mo
- wins: when clinics need deep reporting and have dedicated IT

ezyVet:
- cloud-based, popular in AU/NZ, growing in US
- good for multi-location clinics
- strong inventory management
- pricing: custom enterprise quotes
- support is slow, users complain on forums
- wins: when clinic is already scaling to 3+ locations

Cornerstone (IDEXX):
- comes bundled with IDEXX lab equipment
- most installed base of any vet software
- on-premise, not cloud
- almost no innovation in 5 years
- wins: when clinic already uses IDEXX labs and wants one vendor

Status quo / DIY:
- lots of small clinics use paper + Google Calendar + QuickBooks
- they hate it but scared of switching cost
- wins when: clinic owner is resistant to tech or has <2 vets

Our weaknesses (be honest):
- We don't have multi-location support yet
- Inventory management is basic
- No IDEXX lab integration yet
""")

with open("workspace/research/customer_interviews/interview_dr_patel.txt", "w") as f:
    f.write("""Customer Interview - Dr. Priya Patel, Happy Tails Animal Clinic (solo practice, 2 vets)
Date: Sept 12 2024
Interviewer: Jamie

Before PawManager: Used paper appointment book + QuickBooks + separate reminder call system
Biggest pain: "I was spending 90 minutes every evening just reconciling billing. It was eating my life."
What triggered switch: "A no-show tsunami in August cost me $3,400 in a single week."
What surprised her after: "I didn't expect the automated reminders to basically eliminate no-shows. That was the thing."
How she describes us to colleagues: "It's the vet software that actually thinks like a vet, not an accountant."
What almost stopped her: "The price felt scary for a small clinic. I needed to see the ROI fast."
Outcome: "No-shows down 80%. I go home at 6pm now instead of 8pm."
""")

with open("workspace/research/customer_interviews/interview_dr_okonkwo.txt", "w") as f:
    f.write("""Customer Interview - Dr. Felix Okonkwo, Greenfield Pet Care (1 location, 3 vets)
Date: Sept 19 2024
Interviewer: Jamie

Before PawManager: Was on VetPro for 6 years. "It took us 3 months and a consultant to get set up."
Biggest pain with old system: "Reporting was powerful but I never used 80% of it. The interface was built for someone with an MBA."
What triggered switch: "Hired a new vet tech who refused to use VetPro. Said it was from 2003."
What surprised him: "Setup was done in a weekend. I did it myself."
How he describes us: "Like VetPro if VetPro actually cared about small clinics."
Outcome: "Staff training time went from 3 weeks to 2 days."
""")

with open("workspace/ops/infra/deployment_notes.txt", "w") as f:
    f.write("Prod: AWS us-east-1, ECS Fargate\nStaging: t3.medium, auto-sleep after 30min idle\nDB: RDS Postgres 15.2, daily snapshots\nCDN: CloudFront\nMonitoring: Datadog\n")

with open("workspace/ops/logs/error_summary_oct.txt", "w") as f:
    f.write("Oct 2024 Error Summary\n- 3 billing sync failures (resolved)\n- 1 SMS gateway timeout (pagerduty #4421)\n- 0 data loss events\nMTTR avg: 18min\n")

# --- THE CORE PROBLEM FILE: messy product brief the agent must use ---
with open("workspace/product_brief_DRAFT_messy.txt", "w") as f:
    f.write("""PAWMANAGER - INTERNAL PRODUCT BRIEF (MESSY DRAFT - needs cleanup)
Last updated: someone in marketing, not sure who, October 2024

What is it?
PawManager is a cloud-based practice management platform for independent veterinary clinics.
It handles: scheduling, billing, patient records (SOAP notes), automated client reminders, and basic inventory.

Who uses it? 
We THINK it's for: owners of small independent vet clinics, 1-3 locations MAX, usually the vet IS the owner.
Typically 1-4 veterinarians on staff.
They're not IT people. They hate complexity.
Currently using: a mix of paper, old desktop software (Cornerstone), or cobbled-together Google tools.

Why do they switch?
No-shows are killing revenue. Billing is a nightmare. Staff hate training on complex legacy software.
The trigger: usually a bad month (lost revenue from no-shows, or a new hire who refuses to use the old system).

What makes us different?
- Setup in 1 weekend, not 3 months (unlike VetPro/Cornerstone)
- Designed for vet-owners who are also the clinicians, not enterprise HR managers
- Automated reminder system that actually works (SMS + email)
- Flat monthly pricing (no per-seat nonsense): $299/mo flat for up to 4 vets
- We don't try to do everything - we do the daily workflow stuff extremely well

What we are NOT good at:
- Multi-location management (we just don't have it)
- Complex inventory for large practices  
- IDEXX lab integration (on roadmap)
- Enterprise reporting / analytics

Current results customers report:
- No-show rates drop 60-80%
- Billing reconciliation time cut by ~2 hours/day
- New staff trained in 2 days vs 3 weeks on legacy software
- Vet-owners report leaving the clinic 1-2 hours earlier per day

Company stage: Series A, ~200 customers, mostly US-based independent clinics.

Random other stuff someone added:
- Our NPS is 71 (pretty good?)
- We're thinking about adding telehealth but not sure
- The name PawManager was almost "VetFlow" but we couldn't get the domain
- Pricing might change next year, don't commit to $299 in positioning
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")