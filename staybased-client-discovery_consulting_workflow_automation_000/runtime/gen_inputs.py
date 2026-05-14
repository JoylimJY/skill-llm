import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "workspace/clients/archived/2023",
    "workspace/clients/archived/2024",
    "workspace/clients/active",
    "workspace/proposals/drafts",
    "workspace/proposals/sent",
    "workspace/templates",
    "workspace/notes/meetings",
    "workspace/notes/research",
    "workspace/artifacts",
    "workspace/admin/invoices",
    "workspace/admin/contracts",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/clients/archived/2023/fintech_co_summary.txt": (
        "Client: FinTech Co\nStatus: Closed - Won\nProject: Reconciliation automation\nValue: $14,000\nNotes: Great client, prompt payer."
    ),
    "workspace/clients/archived/2024/retailer_notes.txt": (
        "Retailer X - Discovery call March 2024\nResult: Disqualified - no budget\nRed flags: 0 decision-maker clarity, wanted free pilot"
    ),
    "workspace/clients/active/healthcare_sas.txt": (
        "Healthcare SaaS - Ongoing engagement\nContract value: $3,200/mo\nRenewal date: 2025-09-01"
    ),
    "workspace/proposals/drafts/template_v2.md": (
        "# Proposal Template\n## Executive Summary\n[INSERT SUMMARY]\n## Scope\n[INSERT SCOPE]\n## Investment\n[INSERT PRICE]"
    ),
    "workspace/proposals/sent/acme_proposal_jan25.pdf.txt": (
        "Sent to ACME Corp 2025-01-15. Value: $8,500. Status: Awaiting signature."
    ),
    "workspace/templates/discovery_questions_generic.txt": (
        "1. What do you do?\n2. What's your budget?\n3. What's your timeline?\n(Generic template - not specific to any phase)"
    ),
    "workspace/notes/meetings/team_standup_notes.txt": (
        "Weekly standup 2025-06-02\n- Review pipeline\n- Follow up with two warm leads\n- Update CRM\nAction items: send proposal to DataCorp"
    ),
    "workspace/notes/research/ecommerce_market_trends.txt": (
        "E-commerce data engineering trends 2025:\n- Real-time inventory sync\n- Shopify analytics integrations\n- Data lakehouse adoption rising\n- Snowflake vs Databricks debate ongoing"
    ),
    "workspace/admin/invoices/inv_2025_003.txt": (
        "Invoice #2025-003\nClient: LogiTech Solutions\nAmount: $4,200\nStatus: Paid 2025-05-10"
    ),
    "workspace/admin/contracts/standard_msa_v3.txt": (
        "MASTER SERVICES AGREEMENT v3\n1. Scope of Work defined per SOW.\n2. Payment net 30.\n3. IP transfers upon final payment.\n4. Termination clause: 30-day notice."
    ),
    "workspace/notes/research/competitor_rates.txt": (
        "Market rate survey Q1 2025:\n- Data pipeline consulting: $120-$250/hr\n- BI/dashboards: $90-$180/hr\n- Data warehouse migration: $15K-$60K project\n- Retainers common at $2K-$5K/mo"
    ),
    "workspace/clients/active/globex_onboarding.txt": (
        "Globex Corp - Onboarding checklist\n[x] Contract signed\n[x] Access provisioned\n[ ] Kickoff call scheduled\n[ ] Stakeholder intro meeting"
    ),
}

for path, content in distractor_files.items():
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# --- THE MAIN INPUT: Raw, messy call notes ---
raw_call_notes = """\
call notes — kartik / SnapShelf (ecommerce SaaS) — 2025-06-09
took the call via zoom, started ~10 mins late bc he was on another call

--- rough notes below, not cleaned up ---

- company: SnapShelf, they sell inventory management software to small/mid-size online retailers
- kartik is "Head of Growth" but also kind of handles ops stuff
- been around ~4 years, team of about 22 people
- heard about us through a linkedin post apparently, one of our old blog posts

WHY reaching out now:
  says their data pipeline "just keeps breaking" -- specifically the ETL from Shopify + Amazon seller central into their internal postgres DB
  this has been a problem for 6-7 months apparently
  they tried to fix it in-house but their backend eng team doesnt have the bandwidth
  also hired a contractor back in feb (someone from upwork) who "couldnt figure it out"
  then hired ANOTHER contractor in april who also couldnt deliver
  kartik blames the contractors but idk... pattern is suspicious

problem details:
  - pipeline fails 2-3x per week
  - each failure requires 4-6 hrs of manual data reconciliation by their ops team
  - theyre losing visibility into inventory levels which is causing stockouts
  - stockouts are directly hurting their customer churn ("we think we've lost like 3-4 enterprise clients over this")
  - no real monitoring in place currently

THEN he started expanding scope mid-call:
  "oh and while you're at it, we'd also want to rebuild the entire dashboard layer in metabase"
  "actually we might also need to migrate the postgres to snowflake eventually, probably part of this project too"
  no mention of additional budget when he said these things, i asked "would that affect your budget?" and he just said "we'll figure out the details later"

what success looks like (his words):
  "pipeline runs clean, no more manual fixes" -- but he couldnt give me a specific metric
  when i asked about KPIs he said "i mean, just that it works i guess"
  pressed him on what % uptime or error rate they'd accept -- he said he didnt know
  emotional: "my ops team is going to quit if we dont fix this"

budget conversation:
  super reluctant to talk numbers
  eventually said "we have around $800 set aside for this"
  i said that seems low for the scope he described, he said "well we've already spent a lot on the other contractors"
  did NOT budge

timeline:
  "we need this done by end of this week ideally" (call was monday)
  i pointed out that was 4 business days
  he said "ok fine, two weeks max, we really cant wait longer"

decision-making:
  he said he can approve up to $1000 on his own
  anything above needs sign-off from their CTO (maya) and potentially the CEO
  he mentioned the CEO "doesnt really like spending on contractors right now"

questions he asked me:
  "have you done shopify integrations before" -- yes
  "can you start this week" -- i said lets talk scope first
  "would you do a small test task first to see if you're a good fit" -- red flag??

misc observations:
  - kartik talks fast, interrupted me twice
  - seemed genuinely stressed about the ops situation
  - the stockout/churn connection is real and quantifiable if we dig
  - hes not the real decision maker for anything meaningful (above $1k)
  - scope creep was VERY evident during call
  - no clarity on what "done" means

end of call: no next step set, kartik said "ill think about it and reach back out"
"""

notes_path = Path("workspace/notes/meetings/snapshelf_call_20250609.txt")
notes_path.write_text(raw_call_notes)

print("Workspace generated successfully.")
print(f"Main input file: {notes_path}")
print(f"Total distractor files: {len(distractor_files)}")