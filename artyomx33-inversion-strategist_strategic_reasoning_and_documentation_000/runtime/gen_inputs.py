import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "projects/vertical-farms/ops",
    "projects/vertical-farms/finance",
    "projects/vertical-farms/marketing",
    "projects/vertical-farms/logistics",
    "strategy/archived",
    "strategy/current",
    "research/competitors",
    "research/market_data",
    "team/hiring",
    "team/onboarding",
    "admin/legal",
    "admin/compliance",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

(workspace / "projects/vertical-farms/finance/q3_budget.csv").write_text(
    "category,planned,actual\nseeds,5000,5200\nlighting,12000,11800\npackaging,3000,3400\nlogistics,8000,7900\n"
)

(workspace / "projects/vertical-farms/ops/sensor_log_week12.txt").write_text(
    "2024-03-18 08:00 | temp=22.1C | humidity=68% | CO2=420ppm\n"
    "2024-03-18 09:00 | temp=22.3C | humidity=67% | CO2=418ppm\n"
    "2024-03-18 10:00 | temp=23.1C | humidity=70% | CO2=425ppm\n"
)

(workspace / "projects/vertical-farms/marketing/instagram_captions_draft.txt").write_text(
    "Post 1: 'From seed to plate in 14 days. #urbanfarming #fresh'\n"
    "Post 2: 'Zero pesticides. Just pure growth. #verticafarming'\n"
    "Post 3: 'Your greens, delivered weekly. Subscribe now.'\n"
)

(workspace / "projects/vertical-farms/logistics/delivery_zones.txt").write_text(
    "Zone A: Downtown Core - Mon/Wed/Fri\n"
    "Zone B: Suburbs North - Tue/Thu\n"
    "Zone C: Suburbs South - Tue/Thu\n"
    "Note: cold chain required under 7C\n"
)

(workspace / "strategy/archived/2022_pivot_notes.md").write_text(
    "# 2022 Pivot Notes\nDecided to move from B2B (restaurants) to B2C (subscriptions).\nReason: margins better, more predictable revenue.\nRisk: customer acquisition cost unknown.\n"
)

(workspace / "strategy/current/okrs_2024.md").write_text(
    "# OKRs 2024\n\nO1: Reach 500 subscribers by end of Q4\nKR1: Launch subscription portal by March\nKR2: Onboard 50 subscribers in first month\nKR3: Achieve <5% weekly churn\n\n"
    "O2: Unit economics positive by Q3\nKR1: CAC < $40\nKR2: LTV > $200\n"
)

(workspace / "research/competitors/competitor_analysis_draft.txt").write_text(
    "GreenBox (NYC): $39/week, 3 SKUs. Strength: brand. Weakness: no customization.\n"
    "LocalLeaf (Chicago): $29/week, 6 SKUs. Strength: variety. Weakness: inconsistent supply.\n"
    "FarmDrop (London): subscription + marketplace. Strength: scale. Weakness: not local.\n"
)

(workspace / "research/market_data/urban_farming_trends_2024.txt").write_text(
    "Market size: $5.1B globally in 2023, projected $17.5B by 2030.\n"
    "Key drivers: food security, urbanization, consumer preference for local.\n"
    "Key barriers: high capex, energy costs, consumer awareness.\n"
)

(workspace / "team/hiring/open_roles_q2.txt").write_text(
    "1. Head of Customer Success - posted 2024-02-10\n"
    "2. Farm Operations Lead - posted 2024-02-15\n"
    "3. Part-time Delivery Coordinator - posted 2024-03-01\n"
)

(workspace / "team/onboarding/new_hire_checklist_template.txt").write_text(
    "Day 1: Office tour, system access, meet team\n"
    "Week 1: Shadow each department\n"
    "Month 1: First independent project\n"
)

(workspace / "admin/legal/subscription_terms_v2_draft.txt").write_text(
    "DRAFT - NOT FINAL\n"
    "Subscribers may pause up to 2 weeks/quarter.\n"
    "Cancellation requires 7 days notice.\n"
    "Refunds: only for non-delivered boxes.\n"
)

(workspace / "admin/compliance/food_safety_checklist.txt").write_text(
    "[ ] HACCP plan reviewed\n"
    "[ ] Cold chain temperature log maintained\n"
    "[ ] Allergen labeling compliant\n"
    "[ ] Staff food handler certifications current\n"
)

# --- THE CORE INPUT: Messy, unstructured goal brief ---

brief_content = """
INITIATIVE BRIEF — GreenSprint Subscription Box Launch
Prepared by: Maya Chen, Head of Growth
Date: 2024-03-20
Status: ROUGH DRAFT — needs strategy review

===== BACKGROUND =====
We have been running our vertical farm in the warehouse district for 18 months.
Currently selling to 3 local restaurants (B2B). Revenue is okay but lumpy and
dependent on chef relationships. We want to launch a direct-to-consumer weekly
subscription box ("GreenSprint Box") to households in our metro area.

===== THE GOAL =====
Successfully launch GreenSprint subscription box service and acquire
200 paying subscribers within the first 90 days of launch.

===== WHAT WE HAVE =====
- Working farm with capacity for ~300 boxes/week
- A small team: 2 farm ops, 1 part-time driver, 1 marketing contractor
- Basic Shopify store (not yet subscription-enabled)
- Some Instagram presence (~1,400 followers)
- Budget: $35,000 for launch phase
- Target launch: 8 weeks from now

===== KNOWN CONCERNS (brainstorm dump) =====
- We don't really know if people will actually subscribe vs one-time buy
- Cold chain logistics scare us — what if stuff arrives wilted?
- Not sure if our packaging is premium enough
- Haven't done any door-to-door or local marketing before
- Subscription billing plugin — haven't picked one yet
- What happens if farm has a bad crop week?
- Our driver has another job and may not scale
- We've never done customer support at this volume
- Pricing: $34/week feels right but we haven't tested it
- Don't know how to handle pauses/cancellations gracefully

===== WHAT WE NEED =====
Someone to do a thorough strategic review of this initiative and help us
understand all the ways this could go wrong — and what to do about each one.
This is for our team strategy offsite next week.

Maya
"""

(workspace / "projects/vertical-farms/greensprint_initiative_brief.txt").write_text(brief_content)

print("Workspace generated successfully.")
print(f"Core input: {workspace / 'projects/vertical-farms/greensprint_initiative_brief.txt'}")