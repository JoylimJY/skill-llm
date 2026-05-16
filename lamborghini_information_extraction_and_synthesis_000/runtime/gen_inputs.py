import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a deeply nested distractor directory structure
dirs = [
    "workspace/client_files/2023_reports",
    "workspace/client_files/2024_reports",
    "workspace/client_files/drafts",
    "workspace/research/competitors/ferrari",
    "workspace/research/competitors/mclaren",
    "workspace/research/competitors/porsche",
    "workspace/research/market_data",
    "workspace/internal/templates",
    "workspace/internal/old_briefs",
    "workspace/internal/archive/2022",
    "workspace/assets/logos",
    "workspace/assets/specs",
]

for d in dirs:
    os.makedirs(f"/{d}", exist_ok=True)

# Distractor files with plausible but WRONG/incomplete Lamborghini data
# These are intentionally misleading to test if agent reads SKILL.md vs. uses training data

distractor_1 = {
    "note": "DRAFT - DO NOT USE",
    "huracan_evo_price": "approximately 200 wan",
    "aventador_svj_price": "around 500 wan",
    "deposit": "around 20-30 wan",
    "wait_time": "6 months"
}
with open("/workspace/client_files/drafts/old_lamborghini_notes.json", "w") as f:
    json.dump(distractor_1, f, ensure_ascii=False, indent=2)

distractor_2 = """Ferrari vs Lamborghini Market Analysis 2022
- Ferrari Roma: 220万起
- Ferrari SF90: 480万起  
- Note: Lamborghini pricing updated in 2023, figures below may be outdated
- Aventador price: ~500万 (unconfirmed)
- Huracan: ~230万 (entry level estimate)
"""
with open("/workspace/research/competitors/ferrari/comparison_2022.txt", "w") as f:
    f.write(distractor_2)

distractor_3 = {
    "lamborghini_history": {
        "founded": "1962",  # WRONG - should be 1963
        "founder": "Ferruccio Lamborghini",
        "first_model": "350GT",  # WRONG - should be 350GTV
        "acquired_by_vw": "1999"  # WRONG - should be 1998
    }
}
with open("/workspace/research/market_data/brand_history_draft.json", "w") as f:
    json.dump(distractor_3, f, ensure_ascii=False, indent=2)

distractor_4 = """INTERNAL TEMPLATE - Luxury Car Brief Template v1.2
[CLIENT NAME]
[DATE]
Recommended models: 
- Entry supercar: ___
- Flagship supercar: ___
- SUV option: ___
Finance rate: typically 5-7% for luxury vehicles
Deposit: standard 10% of vehicle price
"""
with open("/workspace/internal/templates/luxury_brief_template.txt", "w") as f:
    f.write(distractor_4)

distractor_5 = {
    "porsche_911_turbo_s": {"price_wan": 280, "hp": 650, "0_100": 2.7},
    "mclaren_720s": {"price_wan": 320, "hp": 720, "0_100": 2.9},
    "ferrari_488": {"price_wan": 310, "hp": 660, "0_100": 3.0}
}
with open("/workspace/research/competitors/mclaren/competitor_specs.json", "w") as f:
    json.dump(distractor_5, f, ensure_ascii=False, indent=2)

distractor_6 = """Lamborghini Sian Technical Overview (OUTDATED)
The Sian uses a traditional lithium-ion battery hybrid system combined with the V12 engine.
Production: 63 units
Price: approximately $300M USD  # WRONG price and hybrid type
"""
with open("/workspace/research/market_data/sian_overview_outdated.txt", "w") as f:
    f.write(distractor_6)

distractor_7 = """Dealer Network Notes (2021)
Beijing: Yingjie Bao - Chaoyang District (address unclear)
Shanghai: Yongda - Pudong (exact address unknown)
Chengdu: Sanhe dealership - location TBD
"""
with open("/workspace/internal/old_briefs/dealer_network_2021.txt", "w") as f:
    f.write(distractor_7)

distractor_8 = {
    "urus_s": {"hp": 650, "0_100": 3.6},   # WRONG: should be 666Ps, 3.5s
    "urus_performante": {"hp": 666, "0_100": 3.4}  # WRONG: should be 3.3s
}
with open("/workspace/assets/specs/urus_specs_unverified.json", "w") as f:
    json.dump(distractor_8, f, ensure_ascii=False, indent=2)

distractor_9 = """Archive: 2022 Client Brief - Mr. Zhang
Recommended: Aventador SVJ
Price discussed: ~600万
Deposit paid: 30万
Wait time: estimated 8 months
Finance: 6% annual rate discussed
"""
with open("/workspace/internal/archive/2022/client_zhang_brief.txt", "w") as f:
    f.write(distractor_9)

distractor_10 = {
    "warranty": {
        "vehicle": "2 years",   # WRONG: should be 3 years
        "paint": "2 years",     # WRONG: should be 3 years  
        "parts": "1 year"       # WRONG: should be 2 years
    },
    "service_hotline": "400-800-1234"  # WRONG: should be 400-120-6699
}
with open("/workspace/client_files/2023_reports/warranty_summary_draft.json", "w") as f:
    json.dump(distractor_10, f, ensure_ascii=False, indent=2)

distractor_11 = """Porsche Cayenne vs Lamborghini Urus Comparison
Both are luxury SUVs with performance pedigree.
Porsche Cayenne Turbo GT: 640hp, 0-100 in 3.3s, price ~230万
Lamborghini Urus: approximately 650hp (unverified), 0-100 ~3.4s (estimated)
"""
with open("/workspace/research/competitors/porsche/suv_comparison.txt", "w") as f:
    f.write(distractor_11)

# The task instruction file - what the agent needs to produce
task_brief = """CLIENT BRIEF REQUEST
===================
Client: Mr. Wei Jiaming (High Net Worth Individual)
Prepared by: Apex Luxury Automotive Consultancy
Date: 2026-07-01

REQUEST:
Mr. Wei is seriously considering purchasing a Lamborghini and requires a comprehensive 
research brief before making his decision. Please compile an accurate, structured 
briefing document (lamborghini_client_brief.json) covering the following:

1. BRAND_OVERVIEW: 
   - Year founded, founder name, headquarters location, parent company (with acquisition year)
   - 2023 global sales figure

2. MODEL_COMPARISON:
   - For each of the following, provide exact horsepower (Ps), 0-100km/h time, top speed, and starting price (万元):
     * Huracán EVO
     * Huracán STO  
     * Aventador SVJ
     * Aventador Ultimae
     * Urus S
     * Urus Performante

3. LIMITED_EDITIONS:
   - For Centenario, Veneno, Sián, and Countach LPI 800-4:
     * Production quantity, price (USD), and one key technical characteristic

4. PURCHASE_PROCESS:
   - Required deposit range (万元), production wait time range (months)
   - Standard finance: minimum down payment percentage, available terms (months), annual interest rate floor
   - Customization: color options count, lead time range (months), cost range (万元)

5. AFTERSALES:
   - Vehicle warranty period (years), paint warranty (years), parts warranty (years)
   - Service hotline number
   - Small service interval and price range (元)

6. BRAND_MILESTONES:
   - List exactly these 5 milestone years and their events: 1963, 1966, 1990, 1998, 2018

7. CHINA_DEALERS:
   - Provide full details (city, dealer name, address) for all 6 listed Chinese dealers

The output file must be named exactly: lamborghini_client_brief.json
"""

with open("/workspace/client_files/CLIENT_BRIEF_REQUEST.txt", "w") as f:
    f.write(task_brief)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("/workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")