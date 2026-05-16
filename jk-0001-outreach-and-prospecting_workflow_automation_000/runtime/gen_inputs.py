import os
import random
import json

random.seed(42)

base = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "company/finance",
    "company/legal",
    "company/marketing/assets",
    "company/marketing/campaigns/2023",
    "company/marketing/campaigns/2024",
    "company/ops/vendors",
    "company/ops/hr",
    "clients/existing",
    "clients/pipeline",
    "research/biotech_landscape",
    "research/competitor_analysis",
    "templates/old_drafts",
    "templates/rejected",
    "meeting_notes",
    "misc",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "company/finance/q3_2024_budget.csv": (
        "Category,Q3 Budget,Q3 Actual\nPayroll,120000,118500\nSoftware,8000,7200\nMarketing,15000,11000\n"
    ),
    "company/finance/burn_rate_notes.txt": (
        "Current monthly burn: ~$42k. Runway ~14 months at current rate. Need to close 2 new clients by Q2.\n"
    ),
    "company/legal/nda_template.txt": (
        "MUTUAL NON-DISCLOSURE AGREEMENT\nThis agreement entered into as of [DATE] between [PARTY A] and [PARTY B]...\n"
    ),
    "company/marketing/assets/logo_usage.txt": (
        "Logo must appear on all outbound communications. Brand colors: #2C3E50 and #E74C3C.\n"
    ),
    "company/marketing/campaigns/2023/newsletter_q4.txt": (
        "Subject: Year-End Insights for Biotech Finance Teams\nHi team, here is our Q4 newsletter...\n"
    ),
    "company/marketing/campaigns/2024/inbound_leads_jan.csv": (
        "Name,Company,Email,Source\nDr. Sarah Kim,NovaBio,s.kim@novabio.com,LinkedIn\nMark Chen,HeliXPath,m.chen@helixpath.com,Website\n"
    ),
    "company/ops/vendors/software_subscriptions.txt": (
        "Apollo.io - $99/mo\nNotion - $16/mo\nQuickBooks - $30/mo\nSlack - $87/mo\n"
    ),
    "company/ops/hr/contractor_agreement_v2.txt": (
        "This Independent Contractor Agreement (ICA) is made between [CONSULTANT NAME] and [CLIENT]...\n"
    ),
    "clients/existing/meridian_pharma_notes.txt": (
        "Client since: March 2023. Monthly retainer: $6,500. POC: Janet Olufemi (CFO).\nScope: monthly close, board reporting, fundraising model.\n"
    ),
    "clients/existing/celltrace_bio_contract.txt": (
        "Contract value: $8,200/month. Signed: June 2024. Term: 12 months. Services: fractional CFO, cap table mgmt.\n"
    ),
    "clients/pipeline/cold_contacts_dump.csv": (
        "Name,Title,Company,LinkedIn,Notes\n"
        "Alex Turner,CEO,QuantumCell,linkedin.com/in/alexturner,Series A announced Nov 2024\n"
        "Priya Nair,COO,ZephyrGene,linkedin.com/in/priyanair,Hiring VP Finance per job post\n"
        "Tom Walsh,Founder,BioLoops,linkedin.com/in/tomwalsh,Posted about fundraising stress on LinkedIn\n"
        "Sandra Lee,CEO,NexaTherapeutics,linkedin.com/in/sandralee,Recent Crunchbase: $12M Series A\n"
    ),
    "research/biotech_landscape/series_a_trends_2024.txt": (
        "2024 Series A median: $14M. Lead investors: a16z Bio, OrbiMed, RA Capital.\n"
        "Key pain: CEOs handling finance solo post-raise. 78% lack dedicated CFO until Series B.\n"
    ),
    "research/competitor_analysis/other_fractional_cfos.txt": (
        "Competitors: CFO Hub, Danforth Advisors, Ampleo.\n"
        "Weakness: generalist focus, not biotech-specific. Average response time: 48h+.\n"
        "Our edge: biotech-only, board-deck fluency, fundraising model expertise.\n"
    ),
    "templates/old_drafts/cold_email_attempt1.txt": (
        "Subject: Synergy Opportunity\n\nHi [Name],\n\nI hope this email finds you well. "
        "I am reaching out today because I believe there may be a fantastic synergy opportunity between us. "
        "I am a seasoned CFO professional with over 15 years of experience in the life sciences space. "
        "My company offers a comprehensive suite of fractional CFO services that could really move the needle "
        "for a fast-growing company like yours. I would love to schedule a 45-minute discovery call at your "
        "earliest convenience to explore how we might work together.\n\nBest regards,\nJohn Whitmore, CPA, CFA\nWhitmore Financial Advisory LLC\n"
    ),
    "templates/old_drafts/linkedin_pitch_v1.txt": (
        "Hi [Name], I'd love to connect with you! I am a fractional CFO specializing in biotech. "
        "I have helped many companies like yours achieve their financial goals. "
        "I think we could have a great synergy. Would you be open to a call? Looking forward to connecting!\n"
    ),
    "templates/rejected/sequence_attempt_v1.txt": (
        "Touch 1 (Day 1): Send cold email\nTouch 2 (Day 2): Follow-up email\nTouch 3 (Day 3): Call\nTouch 4 (Day 4): Email again\n"
        "Note: Rejected — too aggressive, same channel repeated, no value added\n"
    ),
    "meeting_notes/kickoff_strategy_2025-01-15.txt": (
        "Goals for 2025: Land 3 new fractional CFO clients in biotech.\n"
        "Strategy: outbound to Series A/B biotechs without a full-time CFO.\n"
        "Target: CEOs and COOs at companies 10-60 employees.\n"
        "Budget pain: post-raise compliance, board reporting, cash flow modeling.\n"
    ),
    "misc/random_contacts.txt": (
        "David Park - VC at OrbiMed (not a prospect, just a contact)\n"
        "Lisa Fernandez - lawyer, does biotech IP work\n"
        "Bob Nguyen - ex-colleague, now at Genentech\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(base, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── the main task brief ───────────────────────────────────────────────────────
brief = {
    "consultant": "Jordan Whitmore",
    "service": "Fractional CFO services",
    "niche": "Series A and Series B biotech startups",
    "value_proposition": (
        "Helps biotech founders navigate the financial complexity that comes right after a raise: "
        "board reporting, burn rate modeling, investor compliance, and fundraising readiness for the next round. "
        "Typically saves founders 15-20 hours/month and prevents costly financial surprises at the worst time."
    ),
    "target_contacts_for_sequence": {
        "name": "Alex Turner",
        "title": "CEO",
        "company": "QuantumCell",
        "trigger": "Just announced a $9M Series A in November 2024",
        "pain_signal": "QuantumCell is actively hiring a VP of Finance per their LinkedIn job posting — "
                       "a strong signal they are currently managing finances manually at CEO level.",
        "linkedin_post_reference": "Alex posted last week: 'Post-raise life: exciting and terrifying at the same time. "
                                   "So much to build, so little time.' — publicly signaling the overwhelm."
    },
    "instructions": (
        "Using the context above, produce the full outreach kit described in the task prompt. "
        "Save the output as outreach_kit.json in the workspace root."
    )
}

with open(os.path.join(base, "task_brief.json"), "w") as f:
    json.dump(brief, f, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_, files in os.walk(base):
    for file in files:
        print(f"  {os.path.join(root, file)}")