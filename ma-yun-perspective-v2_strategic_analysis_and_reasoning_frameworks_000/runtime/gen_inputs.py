import os
import json
import random

random.seed(42)

base = "/workspace"

# Create distractor directory structure
dirs = [
    "company/strategy/drafts",
    "company/strategy/archive",
    "company/finance/q1",
    "company/finance/q2",
    "company/hr/recruitment",
    "company/hr/culture",
    "company/product/roadmap",
    "company/product/specs",
    "company/marketing/campaigns",
    "company/legal/contracts",
    "frameworks/generic",
    "frameworks/competitor_analysis",
    "research/market",
    "research/trends",
    "presentations/board",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractor_files = {
    "company/strategy/drafts/generic_swot.txt": "SWOT Analysis Template\nStrengths:\nWeaknesses:\nOpportunities:\nThreats:",
    "company/strategy/archive/2023_pivot.txt": "In 2023 we considered pivoting to SaaS model. Decision deferred.",
    "company/finance/q1/revenue.csv": "month,revenue\nJan,12000\nFeb,15000\nMar,18000",
    "company/finance/q2/costs.csv": "month,cost\nApr,9000\nMay,11000\nJun,13000",
    "company/hr/recruitment/job_desc_cto.txt": "We are looking for a CTO with 10+ years experience in distributed systems.",
    "company/hr/culture/values_draft.txt": "Draft company values: Innovation, Integrity, Impact",
    "company/product/roadmap/2024_q3.txt": "Q3 Roadmap: Launch mobile app, expand to 3 new cities",
    "company/product/specs/api_v2.md": "# API v2 Specification\n## Endpoints\nGET /farmers\nPOST /orders",
    "company/marketing/campaigns/campaign_brief.txt": "Target: urban millennials aged 25-35. Message: Fresh produce directly from farms.",
    "company/legal/contracts/supplier_template.txt": "This agreement is between [PLATFORM] and [SUPPLIER]...",
    "frameworks/generic/porter_five_forces.txt": "Porter's Five Forces Analysis Framework\n1. Competitive Rivalry\n2. Supplier Power\n3. Buyer Power\n4. Threat of Substitution\n5. Threat of New Entry",
    "frameworks/competitor_analysis/jd_fresh.txt": "JD Fresh: B2C fresh produce platform, operates own logistics, strong in tier-1 cities.",
    "research/market/southeast_asia_agri.txt": "Southeast Asia agricultural market size: $320B. Digital penetration: 12%. Growth rate: 8% YoY.",
    "research/trends/platform_economy.txt": "Platform economy trends 2024: Super-apps, embedded finance, last-mile logistics innovation.",
    "presentations/board/q2_deck_notes.txt": "Board presentation notes: Emphasize unit economics, path to profitability, TAM expansion.",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(base, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# The main task input: a raw business pitch memo
pitch_memo = """
AGRIBRIDGE PLATFORM - STRATEGIC VALIDATION REQUEST
===================================================

Company: AgriBridge
Stage: Pre-Series A (currently bootstrapped, 18 months old)
Team: 6 people (2 tech, 2 ops, 1 sales, 1 founder/CEO)
Current Status: 230 farmers onboarded, 1,200 monthly active buyers, GMV $45K/month

THE BUSINESS:
AgriBridge is a digital marketplace connecting smallholder farmers in rural Vietnam and Indonesia 
with urban restaurants and grocery buyers. We handle discovery, negotiation, payment, and basic 
logistics coordination.

THE DILEMMA:
We have two competing strategic proposals from our advisory board:

OPTION A - "Go Deep" (Vertical Integration):
Build our own cold-chain logistics network, hire 50 drivers, lease 3 cold storage facilities.
Estimated cost: $2M over 18 months.
Rationale: Control quality, improve margins (from 8% to 22%), differentiate from competitors.
Projected outcome: Higher unit economics but slower growth, heavy capex.

OPTION B - "Go Wide" (Platform Expansion):  
Stay asset-light, open APIs to third-party logistics providers, add payment escrow for farmers,
integrate with existing cold-chain operators. Focus on onboarding 10,000 farmers in 24 months.
Estimated cost: $800K over 18 months.
Rationale: Network effects, platform defensibility, empower ecosystem participants.
Projected outcome: Lower margins per transaction but exponential user growth potential.

THE ASK:
We need a rigorous strategic analysis using the Ma Yun (Jack Ma) perspective framework. 
Please evaluate BOTH options against ALL 8 decision heuristics from the framework,
declare a recommended option, and flag any honest limitations of this analysis.

The output must be saved as: strategic_analysis.json
"""

with open(os.path.join(base, "agribridge_pitch.txt"), "w", encoding="utf-8") as f:
    f.write(pitch_memo)

# A partial/wrong example to mislead (incomplete heuristic list, wrong priority order)
wrong_example = {
    "analysis": {
        "heuristics_applied": ["vision_check", "customer_check", "team_check"],
        "recommendation": "Option A",
        "rationale": "Better margins and quality control align with long-term growth."
    }
}
with open(os.path.join(base, "company/strategy/drafts/wrong_analysis_example.json"), "w", encoding="utf-8") as f:
    json.dump(wrong_example, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files) + 2} files")