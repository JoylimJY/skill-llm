import os
import json
import csv
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "internal/brand_assets/logos",
    "internal/brand_assets/presentations",
    "internal/finance/q1_2024",
    "internal/finance/q2_2024",
    "internal/operations/khorgos_warehouse",
    "internal/operations/shipping_routes",
    "market_research/legacy_reports/2022",
    "market_research/legacy_reports/2023",
    "market_research/competitor_intel",
    "tools/templates",
    "tools/scripts",
    "compliance/certifications",
    "compliance/customs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
# Finance files
(workspace / "internal/finance/q1_2024/sales_summary_q1.csv").write_text(
    "region,units_sold,revenue_usd\nCentral Asia,342,4104000\nSoutheast Asia,0,0\nMENA,89,1068000\n"
)
(workspace / "internal/finance/q2_2024/sales_summary_q2.csv").write_text(
    "region,units_sold,revenue_usd\nCentral Asia,410,4920000\nSoutheast Asia,12,144000\nMENA,105,1260000\n"
)
(workspace / "internal/finance/q2_2024/fx_exposure_notes.txt").write_text(
    "UZS/CNY volatility: moderate. GEL stable. KGS mild depreciation expected Q3.\n"
    "Recommended: partial USD invoicing for Central Asia, EUR for Eastern Europe.\n"
)

# Operations files
(workspace / "internal/operations/khorgos_warehouse/inventory_snapshot.csv").write_text(
    "sku,model,powertrain,units_in_stock,avg_cost_usd\n"
    "EREV-01,Model-X EREV,Extended Range EV,87,14200\n"
    "PHEV-02,Model-Y PHEV,Plug-in Hybrid,134,12800\n"
    "ICE-03,Model-Z 1.5T,Gasoline,210,9500\n"
    "HEV-04,Model-W HEV,Hybrid,65,11300\n"
)
(workspace / "internal/operations/khorgos_warehouse/reorder_schedule.txt").write_text(
    "Next shipment from Changsha factory: 2024-09-15\nExpected: 200 EREV-01, 150 PHEV-02\nLogistics partner: COSCO + China-Europe Railway\n"
)
(workspace / "internal/operations/shipping_routes/port_schedule.csv").write_text(
    "destination_port,transit_days,cost_per_unit_usd,frequency\n"
    "Tashkent (rail),12,380,weekly\n"
    "Dar es Salaam,28,620,biweekly\n"
    "Ho Chi Minh City,18,510,weekly\n"
    "Mombasa,31,650,monthly\n"
    "Bogota,42,890,monthly\n"
    "Tbilisi (rail),10,340,weekly\n"
)

# Legacy market reports (outdated, messy)
(workspace / "market_research/legacy_reports/2022/uzbekistan_brief_2022.txt").write_text(
    "Market note (2022): EV tariff at 0% but infrastructure limited.\n"
    "Local partner Uzavtosanoat still dominant. Chinese brands <5% share.\n"
    "NOTE: Data outdated, do not use for current decisions.\n"
)
(workspace / "market_research/legacy_reports/2023/nigeria_assessment_draft.txt").write_text(
    "DRAFT - NOT FINALIZED\nNigeria: Right-hand drive market. Import duty on EVs: 35%.\n"
    "Fuel subsidy removal 2023 may shift consumer preference.\n"
    "Chinese brand activity: minimal.\n"
    "DRAFT STATUS: Legal review pending.\n"
)
(workspace / "market_research/legacy_reports/2023/vietnam_quick_scan.txt").write_text(
    "Vietnam quick scan (2023): Left-hand drive. EV tariff under ASEAN FTA: ~0-5%.\n"
    "VinFast dominant locally. BYD entered 2023. Market growth: rapid.\n"
    "Charging infra: growing in cities. Rural: poor.\n"
)
(workspace / "market_research/competitor_intel/byd_expansion_tracker.csv").write_text(
    "country,entry_year,models,dealer_count,est_market_share_pct\n"
    "Thailand,2022,Atto3+Han,38,4.2\n"
    "Vietnam,2023,Atto3,12,1.1\n"
    "Uzbekistan,2022,various,8,2.3\n"
    "Colombia,2023,Dolphin+Seal,15,0.8\n"
    "Kenya,2024,Atto3,3,0.2\n"
)
(workspace / "market_research/competitor_intel/chery_footprint_2024.txt").write_text(
    "Chery active markets 2024:\n- Uzbekistan (strong, via Ravon partnership)\n- Philippines (via local dealer)\n"
    "- Ethiopia (pilot batch, 50 units)\n- Colombia (distributor signed)\n- Kazakhstan (growing)\n"
)

# Brand assets (distractors)
(workspace / "internal/brand_assets/presentations/pitch_deck_template_notes.txt").write_text(
    "Slide 1: Executive Summary\nSlide 2: Market Opportunity\nSlide 3: Product Portfolio\n"
    "Slide 4: Go-to-Market Strategy\nSlide 5: Financial Projections\n"
    "NOTE: Update with market scorecard data once analysis complete.\n"
)
(workspace / "tools/templates/scorecard_template_blank.txt").write_text(
    "MARKET SCORECARD TEMPLATE\n"
    "[DO NOT USE - INCOMPLETE]\n"
    "Dimension | Weight | Score\n"
    "... fill in as per methodology ...\n"
)

# Compliance files
(workspace / "compliance/certifications/certification_matrix.csv").write_text(
    "country,standard,cert_body,est_months,est_cost_usd,oem_support\n"
    "Uzbekistan,GOST-R variant,UzStandard,3,8000,yes\n"
    "Ethiopia,ECE R10 partial,ETSA,6,15000,partial\n"
    "Vietnam,TCVN,VR,4,12000,yes\n"
    "Colombia,NTC,ICONTEC,5,18000,partial\n"
    "Kenya,Kenya Bureau of Standards,KEBS,5,14000,no\n"
    "Kyrgyzstan,GOST-R variant,KyrStan,2,6000,yes\n"
)
(workspace / "compliance/customs/tariff_exceptions_notes.txt").write_text(
    "Key tariff agreements:\n"
    "- EAEU zone (UZ, KG, KZ, AM, GE adjacent): 0% EV tariff for member states, GE has FTA benefits\n"
    "- ASEAN (VN, TH, PH): EV tariffs 0-10% depending on origin rules\n"
    "- Ethiopia: GSP+ may reduce tariff to 10% for Chinese OEMs with local assembly\n"
    "- Colombia: EV tariff 15% (under review for reduction in 2025)\n"
    "- Kenya: RHD market - standard import duty 35% for non-EAC manufactured vehicles\n"
    "NOTE: This file requires verification with current official sources.\n"
)

# --- THE CORE TASK INPUT: Raw candidate market data (messy, inconsistent) ---
# 6 candidate markets with raw data that requires:
# 1. One RHD market (Kenya) that must be eliminated at Layer 1
# 2. One market at exact tariff boundary (Colombia: 15%)
# 3. Missing/messy data fields
# 4. Various powertrain recommendation triggers

candidate_markets_data = [
    {
        "market_id": "UZB",
        "country": "Uzbekistan",
        "region": "Central Asia",
        "drive_side": "Left",
        "accepts_chinese_national_standard": True,
        "ev_hybrid_import_tariff_pct": 0,
        "gdp_billion_usd": 90.9,
        "gdp_per_capita_usd": 2470,
        "gdp_growth_pct": 6.0,
        "population_million": 36.8,
        "youth_population_pct_under35": 62,
        "annual_car_sales_units": 185000,
        "ev_penetration_pct": 3.2,
        "ev_market_growth_pct_yoy": 45,
        "fx_restriction_level": "moderate",  # mixed FX - convertible with restrictions
        "policy_subsidy": "partial",  # some EV incentives
        "charging_infra_score_1to5": 2,  # limited charging
        "chinese_brand_count_active": 4,  # Chery, BYD, SGMW, Geely
        "top_competitor_market_share_pct": 28,  # Chery dominant
        "certification_oem_support": True,
        "main_sales_channel": "independent_dealers",
        "fuel_price_usd_per_liter": 0.65,  # cheap fuel
        "climate": "continental_cold_winters",
        "logistics_from_khorgos": "rail_direct",
        "port_logistics_score_1to5": 5,
        "notes": "EAEU adjacent, strong Chery presence, some BYD. Market not fully saturated."
    },
    {
        "market_id": "ETH",
        "country": "Ethiopia",
        "region": "East Africa",
        "drive_side": "Right",  # <-- MUST BE ELIMINATED at Layer 1 (RHD)
        "accepts_chinese_national_standard": "unknown",
        "ev_hybrid_import_tariff_pct": 10,
        "gdp_billion_usd": 155.8,
        "gdp_per_capita_usd": 1200,
        "gdp_growth_pct": 7.2,
        "population_million": 128.0,
        "youth_population_pct_under35": 70,
        "annual_car_sales_units": 12000,
        "ev_penetration_pct": 0.5,
        "ev_market_growth_pct_yoy": 80,
        "fx_restriction_level": "severe",
        "policy_subsidy": "none",
        "charging_infra_score_1to5": 1,
        "chinese_brand_count_active": 1,
        "top_competitor_market_share_pct": 5,
        "certification_oem_support": "partial",
        "main_sales_channel": "government_tenders_and_fleet",
        "fuel_price_usd_per_liter": 0.90,
        "climate": "tropical_highland",
        "logistics_from_khorgos": "sea_plus_overland",
        "port_logistics_score_1to5": 2,
        "notes": "RHD country. High growth but severe FX controls. Pilot batch sent by Chery."
    },
    {
        "market_id": "VNM",
        "country": "Vietnam",
        "region": "Southeast Asia",
        "drive_side": "Right",  # <-- ALSO RHD - must be eliminated
        "accepts_chinese_national_standard": False,
        "ev_hybrid_import_tariff_pct": 8,
        "gdp_billion_usd": 430.0,
        "gdp_per_capita_usd": 4280,
        "gdp_growth_pct": 5.8,
        "population_million": 98.2,
        "youth_population_pct_under35": 55,
        "annual_car_sales_units": 380000,
        "ev_penetration_pct": 12.0,
        "ev_market_growth_pct_yoy": 95,
        "fx_restriction_level": "low",
        "policy_subsidy": "strong",
        "charging_infra_score_1to5": 3,
        "chinese_brand_count_active": 3,
        "top_competitor_market_share_pct": 15,
        "certification_oem_support": True,
        "main_sales_channel": "brand_showrooms",
        "fuel_price_usd_per_liter": 1.10,
        "climate": "tropical",
        "logistics_from_khorgos": "sea",
        "port_logistics_score_1to5": 4,
        "notes": "Vietnam drives on right side (LHD vehicles). Fast growing EV market. VinFast dominant."
    },
    {
        "market_id": "KGZ",
        "country": "Kyrgyzstan",
        "region": "Central Asia",
        "drive_side": "Left",
        "accepts_chinese_national_standard": True,
        "ev_hybrid_import_tariff_pct": 0,
        "gdp_billion_usd": 12.6,
        "gdp_per_capita_usd": 1780,
        "gdp_growth_pct": 4.5,
        "population_million": 7.1,
        "youth_population_pct_under35": 58,
        "annual_car_sales_units": 28000,
        "ev_penetration_pct": 1.1,
        "ev_market_growth_pct_yoy": 30,
        "fx_restriction_level": "moderate",
        "policy_subsidy": "none",
        "charging_infra_score_1to5": 1,
        "chinese_brand_count_active": 2,
        "top_competitor_market_share_pct": 12,
        "certification_oem_support": True,
        "main_sales_channel": "independent_dealers",
        "fuel_price_usd_per_liter": 0.55,  # very cheap fuel
        "climate": "continental_cold_winters",
        "logistics_from_khorgos": "rail_direct",
        "port_logistics_score_1to5": 5,
        "notes": "Small market, EAEU member, very cheap fuel, cold winters, limited charging."
    },
    {
        "market_id": "COL",
        "country": "Colombia",
        "region": "Latin America",
        "drive_side": "Left",
        "accepts_chinese_national_standard": False,
        "ev_hybrid_import_tariff_pct": 15,  # EXACTLY at boundary - allowed per ≤15% rule
        "gdp_billion_usd": 363.0,
        "gdp_per_capita_usd": 6840,
        "gdp_growth_pct": 2.1,
        "population_million": 52.2,
        "youth_population_pct_under35": 48,
        "annual_car_sales_units": 195000,
        "ev_penetration_pct": 2.8,
        "ev_market_growth_pct_yoy": 55,
        "fx_restriction_level": "low",
        "policy_subsidy": "partial",
        "charging_infra_score_1to5": 2,
        "chinese_brand_count_active": 3,
        "top_competitor_market_share_pct": 8,
        "certification_oem_support": "partial",
        "main_sales_channel": "independent_dealers_and_franchises",
        "fuel_price_usd_per_liter": 0.95,
        "climate": "tropical_varied",
        "logistics_from_khorgos": "sea_long_haul",
        "port_logistics_score_1to5": 3,
        "notes": "Tariff exactly 15%. Free FX. Needs NTC certification, OEM partial support only."
    },
    {
        "market_id": "GEO",
        "country": "Georgia",
        "region": "Caucasus",
        "drive_side": "Left",
        "accepts_chinese_national_standard": True,
        "ev_hybrid_import_tariff_pct": 0,
        "gdp_billion_usd": 28.5,
        "gdp_per_capita_usd": 7200,
        "gdp_growth_pct": 5.5,
        "population_million": 3.7,
        "youth_population_pct_under35": 44,
        "annual_car_sales_units": 42000,
        "ev_penetration_pct": 5.0,
        "ev_market_growth_pct_yoy": 38,
        "fx_restriction_level": "low",
        "policy_subsidy": "partial",
        "charging_infra_score_1to5": 3,
        "chinese_brand_count_active": 2,
        "top_competitor_market_share_pct": 10,
        "certification_oem_support": True,
        "main_sales_channel": "independent_dealers",
        "fuel_price_usd_per_liter": 1.05,
        "climate": "temperate_mild",
        "logistics_from_khorgos": "rail_direct",
        "port_logistics_score_1to5": 5,
        "notes": "Small but high-income market. Rail link from Khorgos. FTA proximity to EU."
    }
]

# Write messy JSON input
with open(workspace / "market_research/candidate_markets_raw.json", "w", encoding="utf-8") as f:
    json.dump(candidate_markets_data, f, indent=2, ensure_ascii=False)

# Also write a CSV version with some messiness (boolean inconsistency, mixed types)
csv_path = workspace / "market_research/candidate_markets_raw.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "market_id", "country", "region", "drive_side", "accepts_cn_std",
        "ev_tariff_pct", "gdp_bn_usd", "gdp_pc_usd", "gdp_growth_pct",
        "pop_million", "youth_pct", "car_sales_annual", "ev_penetration_pct",
        "ev_growth_yoy_pct", "fx_restriction", "policy_subsidy",
        "charging_infra_1to5", "cn_brand_count", "top_competitor_share_pct",
        "cert_oem_support", "fuel_price_usd_l", "climate", "logistics_mode",
        "port_logistics_1to5", "notes"
    ])
    for m in candidate_markets_data:
        writer.writerow([
            m["market_id"], m["country"], m["region"], m["drive_side"],
            m["accepts_chinese_national_standard"],
            m["ev_hybrid_import_tariff_pct"],
            m["gdp_billion_usd"], m["gdp_per_capita_usd"], m["gdp_growth_pct"],
            m["population_million"], m["youth_population_pct_under35"],
            m["annual_car_sales_units"], m["ev_penetration_pct"],
            m["ev_market_growth_pct_yoy"], m["fx_restriction_level"],
            m["policy_subsidy"], m["charging_infra_score_1to5"],
            m["chinese_brand_count_active"], m["top_competitor_market_share_pct"],
            m["certification_oem_support"], m["fuel_price_usd_per_liter"],
            m["climate"], m["logistics_from_khorgos"], m["port_logistics_score_1to5"],
            m.get("notes", "")
        ])

# Business context file (the actual task brief)
context = {
    "company_profile": {
        "business_type": "Chinese automotive brand overseas distributor",
        "brands_represented": ["Model-X (EREV)", "Model-Y (PHEV)", "Model-Z (Gasoline 1.5T)", "Model-W (HEV)"],
        "price_range_usd": {"min": 10000, "max": 22000},
        "annual_sales_target_units": 3000,
        "current_markets": ["Kazakhstan", "Russia (suspended)"],
        "best_performing_market": "Kazakhstan",
        "pain_points": ["Inventory buildup in Khorgos", "Kazakhstan market nearing saturation", "Russia exit due to sanctions"],
        "inventory_pressure": {
            "location": "Khorgos bonded warehouse",
            "urgent_sku": "ICE-03 (210 units gasoline)",
            "secondary_sku": "PHEV-02 (134 units plug-in hybrid)"
        },
        "supply_chain_nodes": ["Khorgos (primary)", "Changsha factory (source)"],
        "top_3_priorities": [
            "1. Quickly liquidate Khorgos inventory (especially ICE and PHEV units)",
            "2. Identify 2-3 new high-potential markets for long-term channel building",
            "3. Minimize certification and FX risk in new markets"
        ]
    },
    "task_instructions": "Using the 6 candidate markets in candidate_markets_raw.json, apply our standard market evaluation process to produce a comprehensive market analysis report named market_analysis_report.json. The report should cover market screening decisions, competitive positioning, powertrain recommendations, a scored priority ranking, a phased execution roadmap, and risk mitigation plans."
}

with open(workspace / "market_research/business_context.json", "w", encoding="utf-8") as f:
    json.dump(context, f, indent=2, ensure_ascii=False)

# Add a misleading old scorecard with WRONG weights as a distractor
wrong_scorecard = {
    "WARNING": "DEPRECATED - DO NOT USE",
    "version": "0.3-beta",
    "scoring_dimensions": {
        "market_size": "25%",
        "growth_rate": "25%",
        "policy": "20%",
        "certification": "10%",
        "competition": "10%",
        "payment": "5%",
        "logistics": "5%"
    },
    "threshold": 3.5,
    "note": "This was an old internal draft. Replaced by current methodology."
}
with open(workspace / "tools/templates/scorecard_DEPRECATED_v03.json", "w") as f:
    json.dump(wrong_scorecard, f, indent=2)

# Logistics route analysis (distractor)
(workspace / "internal/operations/shipping_routes/khorgos_route_analysis.txt").write_text(
    "Khorgos Free Trade Zone - Outbound Route Options:\n\n"
    "Route 1: Khorgos → Tashkent (Uzbekistan) - RAIL - 12 days - $380/unit - WEEKLY\n"
    "Route 2: Khorgos → Bishkek (Kyrgyzstan) - RAIL - 10 days - $340/unit - WEEKLY\n"
    "Route 3: Khorgos → Tbilisi (Georgia) - RAIL via Caspian ferry - 10 days - $340/unit - WEEKLY\n"
    "Route 4: Sea export via Shanghai → Bogota/Barranquilla (Colombia) - 42 days - $890/unit - MONTHLY\n"
    "Route 5: Sea export via Shanghai → Dar es Salaam (Tanzania/Ethiopia) - 28-35 days - $620-650/unit\n"
    "Note: Rail routes significantly reduce transit time for Central Asia / Caucasus.\n"
)

print("Workspace setup complete. All input files generated.")
print(f"Key input files:")
print(f"  - /workspace/market_research/candidate_markets_raw.json (6 candidate markets)")
print(f"  - /workspace/market_research/business_context.json (task brief)")