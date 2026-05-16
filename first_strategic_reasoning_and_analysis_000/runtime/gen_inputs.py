import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────

dirs = [
    "company/strategy/2023",
    "company/strategy/2024",
    "company/ops/fleet",
    "company/ops/maintenance",
    "company/finance/q1",
    "company/finance/q2",
    "company/marketing/campaigns",
    "company/marketing/research",
    "company/product/roadmap",
    "company/product/specs",
    "company/legal",
    "company/hr",
    "data/raw",
    "data/processed",
    "notes/meetings",
    "notes/personal",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

distractor_files = {
    "company/strategy/2023/annual_goals.txt": (
        "Goal 1: Expand charging stations to 500 locations by end of year.\n"
        "Goal 2: Increase utilization rate to 70%.\n"
        "Goal 3: Partner with 3 major retail chains.\n"
        "Status: Partially achieved. Utilization stuck at 41%."
    ),
    "company/strategy/2024/q1_review.txt": (
        "Q1 2024 review: We deployed 120 new chargers. Revenue per charger down 12%.\n"
        "Competitor analysis: ChargePoint and EVgo both use hub-and-spoke station models.\n"
        "Recommendation: Follow industry standard — build more high-visibility highway stations."
    ),
    "company/ops/fleet/charger_inventory.csv": (
        "charger_id,location,type,install_date,avg_daily_sessions\n"
        "C001,Highway-I95,DC-Fast,2022-03-10,3.1\n"
        "C002,Retail-Mall-A,L2,2022-06-01,1.2\n"
        "C003,Hotel-Downtown,L2,2023-01-15,4.7\n"
        "C004,Highway-I80,DC-Fast,2023-05-20,2.9\n"
        "C005,Apartment-Complex-B,L2,2023-08-01,6.3\n"
    ),
    "company/ops/maintenance/incident_log.txt": (
        "2024-01-10: C001 offline 6h — cable fault\n"
        "2024-01-22: C003 offline 2h — firmware update\n"
        "2024-02-05: C002 offline 14h — vandalism\n"
        "2024-03-01: C004 offline 3h — network failure\n"
    ),
    "company/finance/q1/p_and_l.txt": (
        "Revenue Q1: $340,000\n"
        "COGS (electricity + maintenance): $290,000\n"
        "Gross Margin: 14.7%\n"
        "Note: Margins are thin. CFO recommends scaling volume to improve unit economics."
    ),
    "company/finance/q2/budget_proposal.txt": (
        "Proposed capex: $2.1M for 80 new DC-Fast chargers on highway corridors.\n"
        "Rationale: Highways = high visibility = brand awareness (like gas station branding).\n"
        "Expected ROI: 18 months based on industry benchmarks."
    ),
    "company/marketing/campaigns/summer_promo.txt": (
        "Campaign: Free charging weekends for new subscribers.\n"
        "Result: +8% new sign-ups, -22% margin on sessions.\n"
        "Insight: Price-sensitive customers churn after promo ends."
    ),
    "company/marketing/research/customer_survey_2024.txt": (
        "Top pain points (n=1,204 EV owners):\n"
        "1. Range anxiety during long trips (68%)\n"
        "2. Difficulty finding chargers near home/work (54%)\n"
        "3. Long wait times at busy stations (49%)\n"
        "4. Unreliable chargers / frequent outages (44%)\n"
        "Satisfaction with current network: 3.1/5.0"
    ),
    "company/product/roadmap/2024_features.txt": (
        "Feature 1: Mobile app reservation system (Q2)\n"
        "Feature 2: Dynamic pricing based on demand (Q3)\n"
        "Feature 3: Fleet management dashboard for B2B (Q4)\n"
        "All features modeled after ChargePoint's existing product suite."
    ),
    "company/product/specs/charger_spec_v3.txt": (
        "Model: VoltGrid Pro 150kW\n"
        "Input: 480V 3-phase\n"
        "Output: CCS + CHAdeMO + J1772\n"
        "Weight: 185 kg\n"
        "MTBF: 8,500 hours\n"
        "Cost per unit: $28,000"
    ),
    "company/legal/permits_tracker.txt": (
        "Pending permits: 14 locations\n"
        "Average permit approval time: 4.2 months\n"
        "Biggest blocker: Utility interconnection agreements (avg 6.1 months)"
    ),
    "company/hr/headcount_plan.txt": (
        "Current field techs: 12\n"
        "Planned hires Q3: 5 additional field techs\n"
        "Note: Turnover high (31% annualized). Competitive market for EV-trained technicians."
    ),
    "data/raw/competitor_pricing.csv": (
        "provider,location_type,price_per_kwh,session_fee\n"
        "ChargePoint,Highway,0.43,1.00\n"
        "EVgo,Highway,0.45,0.00\n"
        "Electrify America,Highway,0.48,0.00\n"
        "VoltGrid (us),Highway,0.41,1.00\n"
        "VoltGrid (us),Residential,0.29,0.00\n"
    ),
    "data/processed/utilization_by_type.json": json.dumps({
        "highway_dcfast": {"avg_sessions_per_day": 2.9, "avg_kwh_per_session": 38.2},
        "retail_l2": {"avg_sessions_per_day": 1.2, "avg_kwh_per_session": 11.4},
        "hotel_l2": {"avg_sessions_per_day": 4.7, "avg_kwh_per_session": 18.6},
        "residential_complex_l2": {"avg_sessions_per_day": 6.3, "avg_kwh_per_session": 22.1},
    }, indent=2),
    "notes/meetings/board_meeting_mar2024.txt": (
        "Board Q: Why aren't we growing faster?\n"
        "CEO: We need to be everywhere drivers are, like gas stations were in the 1960s.\n"
        "CFO: Our ROIC is below cost of capital. Need bigger scale.\n"
        "Board member: Tesla Supercharger built brand loyalty by placing chargers at destinations. "
        "Should we copy that?\n"
        "Decision: Commission a fresh strategic analysis to break the deadlock."
    ),
    "notes/personal/cto_scratchpad.txt": (
        "Random thought: Why do we assume people need to charge on the road?\n"
        "85% of EV charging happens at home. We're building highway stations for 15% of use cases.\n"
        "What if we flipped the model entirely?\n"
        "No time to write this up formally — need proper analysis."
    ),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── The central problem brief (messy, assumption-laden input) ────────────────

brief_content = """VOLTGRID ENERGY — STRATEGIC DECISION BRIEF
Prepared by: Strategy Team
Date: April 2024
Status: DRAFT — needs external analysis

=== THE SITUATION ===

VoltGrid Energy operates a network of EV charging stations across the northeastern US.
We have been growing our station count for 2 years but margins are declining and 
utilization remains stuck below 50%.

The board has approved $2.1M in capital for network expansion and wants a deployment plan.

=== CURRENT ASSUMPTIONS WE ARE OPERATING ON ===

1. More stations = more revenue. Scale is the answer.
2. Highway locations are most valuable because that's where drivers need charging most 
   (like gas stations on interstates).
3. We should match/beat competitor pricing to win market share.
4. The right metric is number of chargers deployed.
5. Building DC-Fast chargers on highways is the industry-standard approach, so it must 
   be correct for us too.
6. Our low margins are a scale problem — they will fix themselves as we grow.
7. Customer satisfaction will improve automatically as we add more stations.

=== THE QUESTION ===

Where should VoltGrid deploy the $2.1M in capital to maximize sustainable profitability?

=== WHAT WE HAVE TRIED ===

- Promotional pricing: boosted sign-ups but hurt margins.
- Partnered with 2 highway rest stops: low utilization (avg 2.9 sessions/day).
- Copied competitor feature roadmap: no differentiation, still losing on margins.

=== WHAT WE NEED ===

A rigorous analysis that challenges our assumptions and tells us what is actually true,
what we should stop believing, and what the right capital allocation strategy is.
Do not just benchmark against competitors. Think from the ground up.

=== DATA AVAILABLE ===
See: data/processed/utilization_by_type.json
See: company/ops/fleet/charger_inventory.csv
See: data/raw/competitor_pricing.csv
See: company/finance/q1/p_and_l.json
See: notes/personal/cto_scratchpad.txt
"""

with open(os.path.join(workspace, "strategic_brief.txt"), "w") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")