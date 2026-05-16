import os
import random
import json

random.seed(42)

BASE = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "clients/active/lexcorp",
    "clients/active/lexcorp/contracts",
    "clients/active/lexcorp/invoices",
    "clients/archived/oldclient_2022",
    "internal/templates/old_templates",
    "internal/templates/deprecated",
    "internal/processes/legacy",
    "internal/processes/playbooks",
    "team/cs_team",
    "team/sales_handoffs",
    "metrics/quarterly",
    "metrics/annual",
    "tools/integrations",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# Distractor files
distractors = {
    "clients/active/lexcorp/contracts/MSA_v3_final.txt": "Master Service Agreement - LexCorp - Signed 2024-01-10\nContract Value: $180,000/year\nTerm: 24 months\nPayment: Net 30",
    "clients/active/lexcorp/invoices/INV_001.txt": "Invoice #001 - LexCorp\nAmount Due: $15,000\nDue Date: 2024-02-10",
    "clients/archived/oldclient_2022/summary.txt": "OldClient churned after 6 months. Root cause: poor onboarding, no kickoff meeting held.",
    "internal/templates/old_templates/welcome_email_v1.txt": "Dear Customer,\nWelcome! Please log in at your convenience.\n\nBest,\nThe Team\n\n[DEPRECATED - Do not use]",
    "internal/templates/deprecated/onboarding_v1_checklist.txt": "1. Send welcome email\n2. Schedule kickoff\n3. Done\n\n[DEPRECATED]",
    "internal/processes/legacy/old_process.txt": "Old process: Call client, send PDF, wait.\nStatus: RETIRED 2023-Q2",
    "internal/processes/playbooks/sales_to_cs_handoff.txt": "Sales hands off to CS after contract signed.\nCS must initiate contact within 24 hours.\nHandoff form must be completed.",
    "team/cs_team/roster.txt": "CS Team:\n- Sarah Mitchell (Lead CSM)\n- James Okonkwo (Onboarding Specialist)\n- Maria Tran (Technical Implementation)\n- Ben Carlisle (Support Lead)",
    "team/sales_handoffs/lexcorp_handoff.txt": "Client: Harrington & Associates Law Firm\nAE: Derek Foss\nClose Date: 2024-06-01\nContract: $95,000/year, 12 months\nProduct: ContractIQ Pro (Legal Document Automation)\nKey Contact: Patricia Harrington (Managing Partner)\nChampion: Tom Yuen (IT Director)\nBusiness Need: Automate NDA and contract review workflows\nSpecial Notes: Firm has 120 attorneys. Compliance-heavy environment. Expects white-glove service.\nTech Stack: Microsoft 365, existing DocuSign integration",
    "metrics/quarterly/q1_2024.txt": "Q1 2024 Onboarding Metrics:\nAvg TTFV: 18 days\nAvg Completion Rate: 71%\nAvg CSAT at Day 30: 7.8/10\nTop churn risk: clients who miss week-1 setup milestone",
    "metrics/annual/2023_annual_report.txt": "2023: 43 new clients onboarded.\nChurn in first 90 days: 9 clients (21%).\nCommon failure: no structured onboarding plan.",
    "tools/integrations/ms365_integration_notes.txt": "ContractIQ integrates with MS365 via OAuth2.\nSetup requires tenant admin consent.\nTypical setup time: 2-3 business days.",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- CREATE THE MAIN PROBLEM INPUT: Messy client status report ---
# This is a raw, unstructured status dump for Harrington & Associates
# It contains signals of onboarding risks that the agent must identify

messy_status_report = """
=== HARRINGTON & ASSOCIATES — ONBOARDING STATUS DUMP ===
Generated: 2024-06-22 (Day 21 of onboarding)
CSM: Sarah Mitchell
Note: This is raw notes from Slack, emails, and CRM. Not cleaned.

--- RAW NOTES ---

Jun 3 (Day 2): Sent welcome email. No reply yet from Patricia or Tom.
Jun 5 (Day 4): Still no reply. James tried calling, got voicemail. Left message.
Jun 7 (Day 6): Tom Yuen finally replied. Says he's "swamped" and can't do kickoff until "sometime next week maybe."
Jun 10 (Day 9): Kickoff STILL NOT SCHEDULED. Week-1 milestone (MS365 integration setup) NOT STARTED.
Jun 12 (Day 11): Got email from Patricia — she says they also want ContractIQ to handle their lease agreements and litigation hold workflows. That was NOT in the original scope.
Jun 14 (Day 13): Tom scheduled kickoff for Jun 17. 
Jun 17 (Day 16): Kickoff happened but Tom wasn't there — sent junior IT guy (Dave) who "doesn't have admin credentials." Meeting was inconclusive. MS365 integration still blocked.
Jun 19 (Day 18): Heard through Derek (AE) that Tom Yuen is interviewing at another firm. Possible departure imminent.
Jun 20 (Day 19): Patricia asked if we can add litigation hold automation to the contract. Derek said maybe. No official change order yet.
Jun 21 (Day 20): Zero logins recorded in ContractIQ dashboard for any Harrington user in past 7 days.
Jun 22 (Day 21): Week-1 AND Week-2 milestones both missed. No training session completed. Day 14 milestone celebration obviously not sent. Support has received 0 tickets (but also 0 logins - bad sign, not good sign).

--- OPEN ITEMS ---
- MS365 tenant admin consent: BLOCKED (no admin present)
- First attorney user training: NOT SCHEDULED
- NDA workflow template setup: NOT STARTED
- Champion availability: UNCERTAIN (Tom possibly leaving)
"""

status_report_path = os.path.join(BASE, "clients/active/lexcorp/harrington_status_report.txt")
with open(status_report_path, "w") as f:
    f.write(messy_status_report)

# Also drop a client brief in the sales handoff folder for context (already done above)
# Add a partial/broken old onboarding attempt by a previous CSM
broken_old_plan = """
HARRINGTON ONBOARDING PLAN (DRAFT - ABANDONED)
Started by: previous CSM (left company)

Week 1:
1. Send welcome
2. Do kickoff
3. Setup stuff

Week 2:
- Training?
- Check in?

[FILE INCOMPLETE - previous CSM left before finishing]
"""
with open(os.path.join(BASE, "clients/active/lexcorp/OLD_onboarding_draft_INCOMPLETE.txt"), "w") as f:
    f.write(broken_old_plan)

print("Workspace generated successfully.")
print(f"Files created in {BASE}")