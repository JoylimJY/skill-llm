import os
import json
import csv
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "companies/starlogic",
    "companies/starlogic/financials",
    "companies/starlogic/marketing",
    "companies/starlogic/hr",
    "companies/archived",
    "companies/archived/2021",
    "research/macro",
    "research/sector",
    "templates",
    "reports/drafts",
    "reports/final",
    "admin",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── CORE INPUT FILES (agent must read these) ─────────────────────────────────

# 1. Company profile
company_profile = """# StarLogic Semiconductors – Company Profile

**Full Name:** StarLogic Semiconductors Co., Ltd.
**Founded:** 2009
**Headquarters:** Shenzhen, China
**Industry:** Semiconductor / Fabless Chip Design
**Primary Products:** AI inference chips, edge computing SoCs, industrial MCUs

## Business Description
StarLogic is a fabless semiconductor company specialising in AI inference chips for edge devices
and industrial automation. The company designs chips in-house but outsources fabrication to TSMC
and SMIC. It holds a portfolio of 47 registered patents in China and the US, and in 2019 obtained
an exclusive government-issued production licence for military-grade encryption chips under the
Chinese State Cryptography Administration (SCA). This licence is non-transferable and covers a
10-year exclusivity window (valid until 2029).

StarLogic's chips are deeply embedded into customers' hardware reference designs, making
re-design with a competitor chip a 12–18 month engineering effort. The company serves 320+
enterprise clients across automotive, industrial, and telecom sectors.

Pricing power: Has consistent ability to raise chip prices 5–8% annually without losing volume.
Customer switching cost: HIGH (re-design + re-certification costs average $2.1M per customer).
Market share (AI edge inference chips, China): 31% as of latest annual report.
"""

with open(os.path.join(BASE, "companies/starlogic/company_profile.md"), "w") as f:
    f.write(company_profile)

# 2. Competitors list
competitors_data = [
    {"name": "Cambrian Technology", "ticker": "688256.SH", "hq": "Shanghai"},
    {"name": "Horizon Robotics", "ticker": "9660.HK", "hq": "Beijing"},
    {"name": "Bitmain", "ticker": "PRIVATE", "hq": "Beijing"},
    {"name": "Nvidia (China ops)", "ticker": "NVDA", "hq": "Santa Clara"},
    {"name": "Rockchip", "ticker": "PRIVATE", "hq": "Fuzhou"},
]
with open(os.path.join(BASE, "companies/starlogic/competitors.json"), "w") as f:
    json.dump(competitors_data, f, indent=2, ensure_ascii=False)

# 3. Competitive advantages summary
competitive_advantages = """# StarLogic Competitive Advantages

1. Proprietary NeuralFlow architecture delivers 3.2x energy efficiency vs nearest competitor
2. State Cryptography Administration exclusive licence for military-grade chips (valid 2019-2029)
3. Deep integration into customer hardware reference designs – average re-design cost $2.1M
4. 47 granted patents covering core inference pipeline and memory subsystem
5. Recognised brand among Tier-1 automotive OEMs in China (Top-3 preferred supplier)
6. Distribution network: 1,200+ authorised resellers across 28 provinces
7. R&D headcount: 1,800 engineers (65% with postgrad degrees)

Note: No significant platform or marketplace network effect has been identified. Customer
adoption does NOT increase the product's value for other customers.
"""
with open(os.path.join(BASE, "companies/starlogic/competitive_advantages.txt"), "w") as f:
    f.write(competitive_advantages)

# 4. Historical financial metrics (KEY for trend analysis)
financial_metrics = {
    "company": "StarLogic Semiconductors",
    "currency": "CNY million",
    "metrics": {
        "market_share_pct": {
            "current": 31,
            "three_years_ago": 38,
            "note": "AI edge inference chips, China domestic market"
        },
        "gross_margin_pct": {
            "current": 54.2,
            "three_years_ago": 53.8,
            "note": "Relatively stable"
        },
        "roe_pct": {
            "current": 14.1,
            "three_years_ago": 21.3,
            "note": "Declined significantly due to increased R&D capex cycle"
        },
        "customer_retention_rate_pct": {
            "current": 87,
            "three_years_ago": 91,
            "note": "Slight decline; two large telecom clients moved to Cambrian"
        }
    }
}
with open(os.path.join(BASE, "companies/starlogic/financials/historical_metrics.json"), "w") as f:
    json.dump(financial_metrics, f, indent=2, ensure_ascii=False)

# 5. Pricing power document
pricing_doc = """StarLogic Pricing Power Assessment (Internal – Q4 2025)

Historical Price Changes:
- 2022: +6.5% blended ASP increase
- 2023: +5.2% blended ASP increase  
- 2024: +7.8% blended ASP increase (driven by military-grade product premium)

Assessment: StarLogic DOES have pricing power. The combination of high switching costs
and the SCA licence allows above-market price increases without volume loss in core segments.
"""
with open(os.path.join(BASE, "companies/starlogic/financials/pricing_power.txt"), "w") as f:
    f.write(pricing_doc)

# ── DISTRACTOR FILES ─────────────────────────────────────────────────────────

# HR distractor
hr_content = """StarLogic HR Report 2025

Headcount: 4,200 total employees
Turnover rate: 8.2%
Average tenure: 4.6 years
Key hires: 12 ex-Qualcomm engineers, 3 ex-Apple SoC architects

Retention initiatives:
- ESOP covering top 15% performers
- Dual-ladder career track (IC vs management)

NOTE: Management quality is EXCELLENT but this does not constitute a structural moat per
standard investment frameworks.
"""
with open(os.path.join(BASE, "companies/starlogic/hr/hr_report_2025.txt"), "w") as f:
    f.write(hr_content)

# Marketing distractor
marketing_content = """Q3 2025 Marketing Campaign Results

Campaign: "Edge AI Everywhere"
Budget spent: CNY 45M
Brand recall (aided): 72% among target audience
NPS score: 58 (industry avg: 41)

Social media: 320K followers on LinkedIn, 1.2M on WeChat Official Account
Press coverage: Featured in 14 tier-1 tech publications

Note: Strong short-term brand campaign results. Marketing team requests additional budget.
"""
with open(os.path.join(BASE, "companies/starlogic/marketing/q3_campaign_results.txt"), "w") as f:
    f.write(marketing_content)

# Old draft analysis (misleading/outdated)
old_draft = """DRAFT - DO NOT USE - StarLogic Preliminary Analysis (2022)

Moat Score: 22/25 (outdated, pre-market share erosion)
Brand: 4, Network: 0, Switching: 5, Scale: 4, Franchise: 5
Recommendation: 强烈推荐

THIS DOCUMENT IS SUPERSEDED. Market conditions have changed significantly.
Do not use these figures.
"""
with open(os.path.join(BASE, "reports/drafts/starlogic_draft_2022.txt"), "w") as f:
    f.write(old_draft)

# Macro research distractor
macro_content = """Semiconductor Sector Outlook 2026

Global chip market expected to grow 8-12% CAGR through 2028.
AI inference at edge projected to be fastest growing segment.
Geopolitical risks: US export controls may impact TSMC supply chain.
Domestic Chinese fab capacity improving but 2-3 nodes behind leading edge.
"""
with open(os.path.join(BASE, "research/macro/semiconductor_outlook_2026.txt"), "w") as f:
    f.write(macro_content)

# Sector research distractor
sector_content = """Edge AI Competitive Landscape – Research Note

Key players: StarLogic, Cambrian, Horizon, Bitmain, Nvidia
Market growing rapidly but competition intensifying.
Cambrian recently won 2 major telecom contracts previously held by StarLogic.
Nvidia expanding China-specific product line (H20 derivatives).
StarLogic faces pricing pressure in non-military segments.
"""
with open(os.path.join(BASE, "research/sector/edge_ai_landscape.txt"), "w") as f:
    f.write(sector_content)

# Template file (distractor)
template_content = """# Generic Company Analysis Template

1. Executive Summary
2. Business Overview
3. Financial Performance
4. Risk Assessment
5. Conclusion

[Fill in sections above]
"""
with open(os.path.join(BASE, "templates/generic_analysis_template.md"), "w") as f:
    f.write(template_content)

# Admin distractor
admin_content = """Meeting Notes – Investment Committee 2026-01-15

Agenda:
1. Q4 portfolio review
2. New position sizing framework
3. ESG policy update

Action items:
- Complete StarLogic deep-dive before next meeting
- Update valuation models for inflation assumptions
"""
with open(os.path.join(BASE, "admin/meeting_notes_2026_01_15.txt"), "w") as f:
    f.write(admin_content)

# Archived 2021 competitor report
archived_content = """Cambrian Technology – 2021 Analysis
(ARCHIVED - for reference only)

Score: 16/25
Strong in network effects for cloud AI, weaker in edge.
"""
with open(os.path.join(BASE, "companies/archived/2021/cambrian_2021.txt"), "w") as f:
    f.write(archived_content)

# Another distractor: valuation model placeholder
valuation_content = """StarLogic Intrinsic Value Model (PLACEHOLDER)

DCF assumptions not yet populated.
Requires moat analysis to be completed first.
WACC: TBD
Terminal growth: TBD
"""
with open(os.path.join(BASE, "companies/starlogic/financials/valuation_placeholder.txt"), "w") as f:
    f.write(valuation_content)

# ESG report distractor
esg_content = """StarLogic ESG Summary 2025

Carbon emissions: 12,400 tCO2e (Scope 1+2)
Renewable energy: 38% of facility power
Water recycling: 65% in fab-adjacent operations
Board diversity: 2 of 9 directors are women

ESG rating: BB (MSCI)
"""
with open(os.path.join(BASE, "companies/starlogic/esg_summary_2025.txt"), "w") as f:
    f.write(esg_content)

print("Workspace generated successfully.")
print(f"Files created in {BASE}")