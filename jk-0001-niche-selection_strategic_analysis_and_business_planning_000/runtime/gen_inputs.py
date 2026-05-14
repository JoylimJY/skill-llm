import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "market_research/archives/2022",
    "market_research/archives/2023",
    "market_research/competitor_notes",
    "founder_notes/brainstorms",
    "founder_notes/calls",
    "financials/projections",
    "financials/burn_rate",
    "marketing/drafts",
    "marketing/assets",
    "product/roadmap",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractors = {
    "market_research/archives/2022/old_survey.txt": "Survey results from 2022. N=45. Mostly legal ops teams.",
    "market_research/archives/2023/competitor_matrix.csv": "tool,price,users\nLexion,99,5000\nIroncladN,199,3000",
    "market_research/competitor_notes/notes.txt": "Ironclad: enterprise focus. DocuSign: signing only. Clio: law firms specifically.",
    "founder_notes/calls/call_log_oct.txt": "Called Marcus (HR director). He said onboarding is painful. Spent $800/mo on Rippling.",
    "founder_notes/calls/call_log_nov.txt": "Spoke to Lisa (freelance dev). Uses Notion + Toggl. Doesn't pay for project tracking.",
    "founder_notes/brainstorms/random_ideas.txt": "Idea: newsletter for solopreneurs. Idea: marketplace for legal templates.",
    "financials/projections/q1_2025.txt": "Revenue target: $5k MRR by March.",
    "financials/burn_rate/monthly.txt": "Monthly expenses: $1200. Runway: 14 months.",
    "marketing/drafts/tagline_ideas.txt": "Draft 1: 'Focus is your superpower.'\nDraft 2: 'Own your niche.'",
    "marketing/assets/brand_colors.txt": "Primary: #2D3748. Accent: #38B2AC.",
    "product/roadmap/v1_features.txt": "MVP: contract parser, client portal, invoice generator.",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── MAIN INPUT FILE: messy raw niche brainstorm notes ─────────────────────
# Each niche has raw assessor scores (1-5) on 6 dimensions (NOT yet weighted).
# Also includes raw validation check notes (pass/fail per check).
# The data is intentionally messy: inconsistent formatting, some niches
# have obvious issues, narrative mixed with numbers.

niche_brainstorm = """\
NICHE BRAINSTORM SESSION — Draft Notes (Unprocessed)
Founder: Alex Reyes | Date: 2025-01-15
Status: RAW — needs scoring and validation

=== INSTRUCTIONS FOR ANALYST ===
Score each niche on six criteria (1-5 each), compute a single weighted total,
pick the top 3 by weighted score, run validation checks on those three,
eliminate any that fail, then write a positioning statement for the winner.
Do NOT skip the weighting — raw averages will mislead you.

================================================================================
NICHE 01: Contract review automation for independent consultants
Scores (raw, 1-5):
  Pain intensity: 5
  Personal advantage: 4
  Market size: 3
  Monetization potential: 4
  Competition landscape: 3
  Growth trajectory: 4

Validation notes:
  [CHECK-1 Search volume] Google Trends shows sustained growth for "contract review software" — PASS
  [CHECK-2 Community] r/consulting has 180K members, active daily threads about bad client contracts — PASS
  [CHECK-3 Competitor gap] Lexion, Ironclad exist but both target enterprise; solo consultant segment ignored — PASS
  [CHECK-4 Pricing] DocuSign $25/mo, Lexion $99/mo — room for a $39/mo solo-focused tier — PASS
  [CHECK-5 Real interviews] Spoke to 3 consultants; all described contract disputes as "nightmare fuel" — PASS

================================================================================
NICHE 02: Invoicing and payment recovery for freelance videographers
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 2
  Market size: 3
  Monetization potential: 3
  Competition landscape: 2
  Growth trajectory: 3

Validation notes:
  [CHECK-1 Search volume] "Freelance videographer invoicing" — very low volume, declining trend — FAIL
  [CHECK-2 Community] r/videography: 95K members but payment discussion rare — FAIL
  [CHECK-3 Competitor gap] FreshBooks, HoneyBook already dominant; no clear gap found — FAIL
  [CHECK-4 Pricing] Market expects <$15/mo — FAIL
  [CHECK-5 Real interviews] Only reached 1 person; lukewarm interest — FAIL

================================================================================
NICHE 03: Employee onboarding workflow builder for HR teams at startups (10-50 employees)
Scores (raw, 1-5):
  Pain intensity: 5
  Personal advantage: 3
  Market size: 5
  Monetization potential: 5
  Competition landscape: 2
  Growth trajectory: 4

Validation notes:
  [CHECK-1 Search volume] "startup onboarding software" trending upward — PASS
  [CHECK-2 Community] Multiple active Slack groups for HR pros; problems discussed daily — PASS
  [CHECK-3 Competitor gap] Rippling, BambooHR too heavy; gap = lightweight, fast-setup for 10-50 headcount — PASS
  [CHECK-4 Pricing] BambooHR charges $6-8/employee/mo; market has budget — PASS
  [CHECK-5 Real interviews] Interviewed 3 HR coordinators; all said setup takes weeks with current tools — PASS

================================================================================
NICHE 04: SEO content brief generator for boutique marketing agencies
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 3
  Market size: 4
  Monetization potential: 4
  Competition landscape: 4
  Growth trajectory: 3

Validation notes:
  [CHECK-1 Search volume] "SEO content brief" — moderate volume, stable — PASS
  [CHECK-2 Community] r/SEO has 200K members, brief quality debated regularly — PASS
  [CHECK-3 Competitor gap] Clearscope, MarketMuse exist; gap = agency-specific team collaboration features — PASS
  [CHECK-4 Pricing] Clearscope $170/mo; smaller agencies cannot afford — market for $49/mo tier — PASS
  [CHECK-5 Real interviews] Could not reach anyone; no interviews conducted — FAIL

================================================================================
NICHE 05: Lease abstraction tool for independent commercial real estate brokers
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 2
  Market size: 2
  Monetization potential: 3
  Competition landscape: 3
  Growth trajectory: 2

Validation notes:
  [CHECK-1 Search volume] Niche terms; very low search volume — FAIL
  [CHECK-2 Community] No active online communities found — FAIL
  [CHECK-3 Competitor gap] CoStar dominates; unclear differentiation — FAIL
  [CHECK-4 Pricing] Brokers price-sensitive; market expects enterprise pricing — FAIL
  [CHECK-5 Real interviews] No interviews conducted — FAIL

================================================================================
NICHE 06: Client reporting dashboard for solo financial advisors (RIAs)
Scores (raw, 1-5):
  Pain intensity: 5
  Personal advantage: 5
  Market size: 3
  Monetization potential: 5
  Competition landscape: 3
  Growth trajectory: 3

Validation notes:
  [CHECK-1 Search volume] "RIA client reporting software" — low but stable — PASS
  [CHECK-2 Community] NAPFA and XY Planning Network forums active — PASS
  [CHECK-3 Competitor gap] Orion, Riskalyze too costly; gap = solo advisor pricing (<$99/mo) — PASS
  [CHECK-4 Pricing] Orion charges $200+/mo; plenty of room — PASS
  [CHECK-5 Real interviews] Interviewed 4 RIAs; 3 said current tools are "bloated and expensive" — PASS

================================================================================
NICHE 07: Project status page generator for freelance web developers
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 4
  Market size: 4
  Monetization potential: 3
  Competition landscape: 3
  Growth trajectory: 4

Validation notes:
  [CHECK-1 Search volume] "client project status page" — rising trend — PASS
  [CHECK-2 Community] r/freelance 300K members, client communication frustration common — PASS
  [CHECK-3 Competitor gap] Basecamp/ClickUp too heavy for solo devs; no lightweight client-only view — PASS
  [CHECK-4 Pricing] Developers willing to pay $19-49/mo for professional client tools — PASS
  [CHECK-5 Real interviews] 2 interviews conducted; both said "I've been looking for exactly this" — PASS

================================================================================
NICHE 08: Subscription churn prediction tool for bootstrapped B2B SaaS founders
Scores (raw, 1-5):
  Pain intensity: 5
  Personal advantage: 4
  Market size: 3
  Monetization potential: 4
  Competition landscape: 3
  Growth trajectory: 5

Validation notes:
  [CHECK-1 Search volume] "churn prediction SaaS" — growing volume — PASS
  [CHECK-2 Community] r/SaaS, IndieHackers very active around churn topics — PASS
  [CHECK-3 Competitor gap] ChurnZero, Gainsight enterprise-only; no solo/bootstrapped option — PASS
  [CHECK-4 Pricing] Founders already pay for Stripe, Baremetrics; budget exists for churn tools — PASS
  [CHECK-5 Real interviews] Interviewed 3 founders; 2 said churn tracking is done in messy spreadsheets — PASS

================================================================================
NICHE 09: Scheduling and tip-splitting tool for food truck operators
Scores (raw, 1-5):
  Pain intensity: 3
  Personal advantage: 1
  Market size: 2
  Monetization potential: 2
  Competition landscape: 2
  Growth trajectory: 2

Validation notes:
  [CHECK-1 Search volume] Minimal search volume — FAIL
  [CHECK-2 Community] Small Facebook groups only — FAIL
  [CHECK-3 Competitor gap] Square already covers most needs — FAIL
  [CHECK-4 Pricing] Very price-sensitive segment; expects free tools — FAIL
  [CHECK-5 Real interviews] No interviews — FAIL

================================================================================
NICHE 10: Proposal generation tool for boutique interior design studios
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 2
  Market size: 3
  Monetization potential: 3
  Competition landscape: 2
  Growth trajectory: 3

Validation notes:
  [CHECK-1 Search volume] "interior design proposal software" — moderate, stable — PASS
  [CHECK-2 Community] Houzz Pro community and ASID forums active — PASS
  [CHECK-3 Competitor gap] Studio Designer, Ivy exist but expensive and complex — PASS
  [CHECK-4 Pricing] Studios pay $100-300/mo for current tools; room to undercut — PASS
  [CHECK-5 Real interviews] No interviews conducted — FAIL

================================================================================
NICHE 11: Cold outreach sequence builder for independent B2B sales consultants
Scores (raw, 1-5):
  Pain intensity: 4
  Personal advantage: 3
  Market size: 4
  Monetization potential: 4
  Competition landscape: 4
  Growth trajectory: 4

Validation notes:
  [CHECK-1 Search volume] "B2B cold email sequence" — high and growing — PASS
  [CHECK-2 Community] r/sales, LinkedIn Sales communities very active — PASS
  [CHECK-3 Competitor gap] Outreach, Salesloft enterprise-priced; gap = solo consultant tier at $29/mo — PASS
  [CHECK-4 Pricing] Sales consultants invest heavily in tools; budget confirmed — PASS
  [CHECK-5 Real interviews] No interviews; too busy to schedule calls — FAIL

================================================================================
NICHE 12: Compliance checklist automation for solo employment law attorneys
Scores (raw, 1-5):
  Pain intensity: 5
  Personal advantage: 2
  Market size: 2
  Monetization potential: 4
  Competition landscape: 2
  Growth trajectory: 3

Validation notes:
  [CHECK-1 Search volume] Very niche; minimal data — FAIL
  [CHECK-2 Community] No public community; attorneys use closed bar association channels — FAIL
  [CHECK-3 Competitor gap] Clio Manage covers most needs already — FAIL
  [CHECK-4 Pricing] Attorneys will pay premium — PASS
  [CHECK-5 Real interviews] 2 interviewed; interested but very risk-averse buyers — PASS
"""

with open(os.path.join(workspace, "founder_notes/brainstorms/niche_candidates_raw.txt"), "w") as f:
    f.write(niche_brainstorm)

print("Workspace initialized successfully.")
print(f"Main input file: {workspace}/founder_notes/brainstorms/niche_candidates_raw.txt")