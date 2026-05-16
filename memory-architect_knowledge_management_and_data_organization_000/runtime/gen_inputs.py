import os
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Distractor files to simulate a real messy project ──────────────────────
dirs = [
    "workspace/deals/riverside",
    "workspace/deals/oakmont",
    "workspace/comps/2024",
    "workspace/comps/2025",
    "workspace/legal/contracts",
    "workspace/legal/disclosures",
    "workspace/financials/q1",
    "workspace/financials/q2",
    "workspace/marketing/flyers",
    "workspace/marketing/campaigns",
    "workspace/admin/logs",
    "workspace/admin/templates",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

distractors = {
    "workspace/deals/riverside/offer_v3.txt": "Offer price $1,250,000. Contingency: inspection by Aug 5.",
    "workspace/deals/oakmont/notes.txt": "Seller wants quick close. HOA docs pending.",
    "workspace/comps/2024/q4_summary.csv": "address,sqft,price\n123 Oak,1800,750000\n456 Elm,2100,890000",
    "workspace/comps/2025/jan_feb.csv": "address,sqft,price\n789 Pine,2200,920000",
    "workspace/legal/contracts/template_purchase.txt": "PURCHASE AGREEMENT TEMPLATE v2.1 ...",
    "workspace/legal/disclosures/spds_blank.txt": "Seller Property Disclosure Statement - Blank",
    "workspace/financials/q1/budget.txt": "Q1 Budget: Marketing $12,000 / Operations $8,500",
    "workspace/financials/q2/actuals.txt": "Q2 Actuals: Marketing $10,200 / Operations $9,100",
    "workspace/marketing/flyers/riverside_flyer.txt": "3BR/2BA Riverside gem — open house Sat 1-4pm",
    "workspace/marketing/campaigns/sept_campaign.txt": "Target: first-time buyers. Budget: $3,000.",
    "workspace/admin/logs/access_log_2025.txt": "2025-01-03 09:12 login:mwilson\n2025-01-04 10:05 login:tchen",
    "workspace/admin/templates/email_followup.txt": "Hi [NAME], Following up on our conversation about [PROPERTY]...",
}
for path, content in distractors.items():
    Path(path).write_text(content)

# ── The main MEMORY.md — intentionally messy, 220+ lines ───────────────────
memory_content = textwrap.dedent("""\
    # Shared Operations Memory — Realty Partners Group

    <!-- NO_REPLY: Do not auto-respond to emails tagged [HOLD] -->
    <!-- HEARTBEAT: Check active.md every session start -->

    ## Shortcuts & Emoji Conventions
    - 🔴 = Blocked / needs attention
    - 🟡 = In progress / waiting on someone
    - 🟢 = Cleared / done
    - 📋 = Document needed
    - 💬 = Follow-up call required

    ## MLS Upload Procedure
    1. Export CSV from internal CRM (File > Export > MLS Format)
    2. Run `python scripts/mls_validator.py --file export.csv --strict`
    3. Upload via portal: https://mls-internal.realtypartners.local/upload
    4. Confirm listing ID returned; paste into deal folder notes.txt
    5. Notify listing agent via Slack #listings channel

    ## Offer Submission Workflow
    1. Collect signed purchase agreement (PDF)
    2. Run `python scripts/offer_packager.py --deal DEAL_ID --agent AGENT_ID`
    3. Email package to `escrow@titleco-west.com` with subject "OFFER: [ADDRESS]"
    4. Log submission timestamp in deals/<address>/notes.txt
    5. Set calendar reminder for 3-business-day response window

    ## Weekly Digest Procedure
    - Every Monday 9am: run `python scripts/weekly_digest.py --send`
    - Recipients: team@realtypartners.local
    - Includes: new listings, pending offers, closed deals this week

    ## Current Active Deals

    ### Riverside Loft (789 Cascade Ave, Unit 4B)
    - Status: 🟡 Under contract — inspection scheduled Aug 12
    - Buyer: Marcus Webb (mwebb@gmail.com)
    - Listing Agent: Sandra Okonkwo
    - Offer Price: $1,175,000
    - Escrow: Title Co West, ref #TCW-2025-0814
    - Next action: Confirm inspection report received from inspector Hal Petrov

    ### Oakmont Colonial (44 Birchwood Lane)
    - Status: 🔴 Blocked — seller wants to delay close by 30 days
    - Seller: The Hargrove Family Trust (contact: Donna Hargrove, dhargrove@trustlaw.com)
    - Listing Agent: Tom Chen
    - List Price: $2,340,000
    - Issue: HOA document package not yet delivered
    - Next action: Chase HOA manager (Greenfield HOA, contact@greenfieldHOA.org)

    ### Sunridge Condo (12 Sunrise Blvd, Unit 9)
    - Status: 🟡 Active listing — 3 showings scheduled this week
    - Owner: Priya Nair (pnair@sunridgellc.com)
    - Listing Agent: Sandra Okonkwo
    - List Price: $675,000
    - Next action: Receive feedback forms from showing agents by Friday

    ## Waiting On
    - Hal Petrov (inspector): Riverside inspection report (due Aug 14)
    - Donna Hargrove: HOA doc package (overdue since Aug 1)
    - Priya Nair: Confirm open-house date preference

    ## Completed Deals

    ### Elmwood Duplex (33 Elmwood Dr) — CLOSED June 2025
    - Buyer: James Whitfield (jwhitfield@paceventures.com)
    - Seller: Monica Reyes (mreyes@gmail.com)
    - Close Price: $985,000
    - Listing Agent: Tom Chen
    - Notes: Smooth close; buyer waived final walkthrough

    ### Harbor View Penthouse (1 Marina Ct, PH2) — CLOSED April 2025
    - Buyer: Coastal Equity LLC (rep: Derek Sands, dsands@coastaleq.com)
    - Seller: NorthStar Properties Inc (rep: Linda Park, lpark@northstar.com)
    - Close Price: $3,100,000
    - Listing Agent: Sandra Okonkwo
    - Notes: Dual agency; required broker approval. Full commission split on file.

    ### Pinebrook Cottage (7 Pinebrook Rd) — CLOSED Jan 2025
    - Buyer: Reginald Osei (rosei@gmail.com)
    - Seller: Harmon & Bluth Holdings (rep: Gary Bluth, gbluth@harmonbluth.com)
    - Close Price: $540,000
    - Listing Agent: Marcus Webb (here acting as buyer's agent)
    - Notes: Cash purchase, no financing contingency

    ## People Directory

    ### Agents (Internal)
    | Name | Role | Email | Phone |
    |------|------|-------|-------|
    | Sandra Okonkwo | Senior Listing Agent | sokonkwo@realtypartners.local | 555-0101 |
    | Tom Chen | Listing Agent | tchen@realtypartners.local | 555-0102 |
    | Marcus Webb | Buyer's Agent | mwebb@realtypartners.local | 555-0103 |

    ### External Contacts
    | Name | Organization | Email | Role |
    |------|-------------|-------|------|
    | Hal Petrov | Petrov Inspections LLC | hpetrov@petrov-inspect.com | Inspector |
    | Derek Sands | Coastal Equity LLC | dsands@coastaleq.com | Buyer Rep |
    | Linda Park | NorthStar Properties Inc | lpark@northstar.com | Seller Rep |
    | Donna Hargrove | Hargrove Family Trust | dhargrove@trustlaw.com | Seller/Trustee |
    | Gary Bluth | Harmon & Bluth Holdings | gbluth@harmonbluth.com | Seller Rep |
    | James Whitfield | Pace Ventures | jwhitfield@paceventures.com | Buyer |
    | Reginald Osei | (private buyer) | rosei@gmail.com | Buyer |
    | Monica Reyes | (private seller) | mreyes@gmail.com | Seller |
    | Priya Nair | Sunridge LLC | pnair@sunridgellc.com | Property Owner |
    | Donna Hargrove | Hargrove Family Trust | dhargrove@trustlaw.com | Trustee |

    ## Organizations

    | Org | Type | Contact | Notes |
    |----|------|---------|-------|
    | Coastal Equity LLC | Investment firm | Derek Sands | Active buyer, interested in multifamily |
    | NorthStar Properties Inc | Seller org | Linda Park | Sold Harbor View; may list again Q4 |
    | Pace Ventures | Investment firm | James Whitfield | Closed Elmwood; looking for next deal |
    | Harmon & Bluth Holdings | Seller org | Gary Bluth | One deal done; no current listings |
    | Sunridge LLC | Owner LLC | Priya Nair | Active listing owner |
    | Hargrove Family Trust | Trust / Seller | Donna Hargrove | Oakmont deal in progress |
    | Petrov Inspections LLC | Service vendor | Hal Petrov | Preferred inspector |
    | Greenfield HOA | HOA | contact@greenfieldHOA.org | Oakmont Colonial HOA |
    | Title Co West | Escrow/Title | escrow@titleco-west.com | Current escrow for Riverside |

    ## Properties Reference

    | Address | Type | Status | Notes |
    |---------|------|--------|-------|
    | 789 Cascade Ave, Unit 4B | Condo/Loft | Under Contract | Riverside Loft deal |
    | 44 Birchwood Lane | Colonial | Active/Blocked | Oakmont Colonial deal |
    | 12 Sunrise Blvd, Unit 9 | Condo | Active Listing | Sunridge Condo |
    | 33 Elmwood Dr | Duplex | Closed June 2025 | Elmwood deal |
    | 1 Marina Ct, PH2 | Penthouse | Closed April 2025 | Harbor View deal |
    | 7 Pinebrook Rd | Cottage | Closed Jan 2025 | Pinebrook deal |

    ## Account & System Info

    | System | URL / ID | Notes |
    |--------|---------|-------|
    | MLS Portal | https://mls-internal.realtypartners.local | Internal only |
    | CRM | https://crm.realtypartners.local | Salesforce-based |
    | Slack Workspace | realtypartners.slack.com | #listings, #deals, #general |
    | Weekly Digest Script | scripts/weekly_digest.py | Runs Mondays 9am |
    | Offer Packager Script | scripts/offer_packager.py | See workflow above |
    | MLS Validator Script | scripts/mls_validator.py | See MLS upload workflow |
    | Title Co West Escrow Ref | TCW-2025-0814 | Riverside deal |

    ## Archived Notes — Old Decisions

    ### Aug 2024 — Commission Split Policy Updated
    - New policy: 50/50 split on dual-agency deals, requires broker sign-off
    - Documented in legal/contracts/commission_policy_2024.pdf
    - Effective immediately per broker Michael Wilson (mwilson@realtypartners.local)

    ### March 2024 — CRM Migration Completed
    - Migrated from HubSpot to Salesforce
    - All historical contacts imported; old HubSpot IDs archived in admin/legacy/
    - Primary contact for CRM issues: IT support (itsupport@realtypartners.local)

    ### Dec 2023 — Inspection Vendor Switch
    - Switched preferred inspector from Bayside Inspections to Petrov Inspections LLC
    - Reason: Bayside had two missed deadlines in Q3 2023
    - Hal Petrov: hpetrov@petrov-inspect.com, 555-0201

    ### Decision Log: Sunridge LLC Listing
    - Onboarded Priya Nair / Sunridge LLC as new listing client May 2025
    - Agreed to 2.5% listing commission
    - Assigned Sandra Okonkwo as lead agent
""")

Path("workspace/MEMORY.md").write_text(memory_content)

print("Workspace generated successfully.")
print(f"MEMORY.md line count: {len(memory_content.splitlines())}")