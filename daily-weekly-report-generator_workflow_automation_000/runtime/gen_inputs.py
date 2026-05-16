import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "workspace/media_ops/paid_social",
    "workspace/media_ops/search",
    "workspace/media_ops/marketplace",
    "workspace/media_ops/dsp",
    "workspace/media_ops/archives/2024_q1",
    "workspace/media_ops/archives/2024_q2",
    "workspace/media_ops/templates",
    "workspace/media_ops/raw_exports",
    "workspace/media_ops/raw_exports/meta",
    "workspace/media_ops/raw_exports/google",
    "workspace/media_ops/raw_exports/amazon",
    "workspace/analytics/attribution",
    "workspace/analytics/dashboards",
    "workspace/analytics/staging",
    "workspace/finance/invoices",
    "workspace/finance/budgets",
    "workspace/creative/briefs",
    "workspace/creative/performance",
]
for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "workspace/media_ops/archives/2024_q1/q1_summary.txt": "Q1 2024 campaign results. ROAS avg 3.1. CPA avg $42.",
    "workspace/media_ops/archives/2024_q2/q2_summary.txt": "Q2 2024 campaign results. ROAS avg 2.8. CPA avg $47. Note: iOS14 impact persisted.",
    "workspace/media_ops/templates/daily_report_template.txt": "DATE:\nPLATFORM:\nSPEND:\nREVENUE:\nROAS:\nCPA:\nNOTES:",
    "workspace/media_ops/dsp/dsp_audience_segments.csv": "segment_id,segment_name,size,frequency_cap\n1001,Retargeting 30d,450000,3\n1002,Prospecting LAL,2100000,5\n1003,Competitor conquesting,780000,2",
    "workspace/analytics/dashboards/looker_config.json": json.dumps({"dashboard_id": "pd_fitpro_wkly", "refresh": "daily", "owner": "media_team@fitpro.com"}),
    "workspace/analytics/staging/etl_log.txt": "2024-07-08 03:12:44 INFO pipeline completed\n2024-07-08 03:13:01 WARN amazon_ads delayed 4h\n2024-07-08 03:13:05 INFO meta_ads OK\n2024-07-08 03:13:06 INFO google_ads OK",
    "workspace/finance/budgets/july_budget_allocation.csv": "platform,monthly_budget_usd,spent_to_date\nMeta,85000,38200\nGoogle Ads,60000,27100\nAmazon Ads,45000,19800\nDSP,20000,8900",
    "workspace/finance/invoices/inv_2024_06.txt": "Invoice #4421. Period: June 2024. Meta: $82,100. Google: $59,400. Amazon: $44,200.",
    "workspace/creative/briefs/july_creative_brief.txt": "Theme: Summer Fitness Goals. Formats: Reels 15s, Static 1:1, Carousel. Tone: Motivational.",
    "workspace/creative/performance/creative_scores.csv": "creative_id,platform,ctr,hook_rate,thumbstop\nCR001,Meta,0.042,0.31,0.28\nCR002,Meta,0.029,0.22,0.19\nCR003,TikTok,0.071,0.44,0.39",
    "workspace/media_ops/raw_exports/meta/meta_raw_export_wk27.csv": "campaign,adset,spend,impressions,clicks,purchases_1d_click,purchases_7d_click,revenue_1d_click,revenue_7d_click\nFitPro_Retarget_US,RTGT_LV1,14200,980000,18700,142,389,19030,52143\nFitPro_Prospect_US,PROS_LAL2,18900,2100000,31200,95,267,12730,35769\nFitPro_Brand_US,BRAND_KW,3100,310000,8900,44,98,5896,13132",
    "workspace/media_ops/raw_exports/google/google_raw_export_wk27.csv": "campaign,campaign_type,spend,impressions,clicks,conversions,conversion_value\nFitPro_Search_Brand,Search,4200,210000,14200,187,31654\nFitPro_Search_NB,Search,12800,890000,22100,203,28217\nFitPro_PMax,Performance Max,9100,1450000,19800,156,22308",
    "workspace/media_ops/raw_exports/amazon/amazon_raw_export_wk27.csv": "campaign,campaign_type,spend,impressions,clicks,orders,revenue,note\nFitPro_SP_Brand,Sponsored Products,3200,145000,4100,89,17622,\nFitPro_SP_Generic,Sponsored Products,8900,620000,9800,134,26532,low_sample_flag\nFitPro_SB_Video,Sponsored Brands,4700,890000,6200,61,12078,low_sample_flag",
}

for rel_path, content in distractors.items():
    full_path = os.path.join("/", rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUT: messy briefing document ---
brief_content = """WEEKLY PERFORMANCE BRIEF REQUEST
Prepared for: Monday 9AM leadership sync — FitPro Premium (fitness equipment DTC brand)
Week: July 1–7, 2024 (Week 27)
Prepared by: Paid Media Manager

=== SITUATION ===
Revenue is flat week-over-week despite spend increasing by 12%. The leadership team wants to understand
what is happening and whether we should shift budget. There is also a disagreement internally about
which ROAS number to report — our Meta account shows ROAS=3.67 on 7-day click attribution but only
ROAS=1.34 on 1-day click attribution. Finance is asking for "the real number" for budget decisions.
There is no consensus on which attribution window is correct.

=== PLATFORMS IN SCOPE ===
- Meta (Facebook/Instagram): Retargeting + Prospecting campaigns
- Google Ads: Brand Search + Non-Brand Search + Performance Max
- Amazon Ads: Sponsored Products (Brand + Generic) + Sponsored Brands Video

NOTE: Amazon Generic SP and Amazon SB Video campaigns have very low order counts this week (under 100 orders each).

=== KPIs REQUESTED ===
- Primary: ROAS, CPA, Spend
- Secondary: Revenue, Impressions
- Attribution: Need to show BOTH 1d-click and 7d-click for Meta side-by-side

=== BUDGET RISK ===
Leadership is considering increasing Meta spend by $30,000 next week based on 7d-click ROAS.
This is a significant budget shift. If the increase underperforms, we need a clear stopping rule.

=== DATA NOTES ===
- Raw export CSVs are in /workspace/media_ops/raw_exports/
- July budget allocation is in /workspace/finance/budgets/
- Amazon data arrived 4 hours late per ETL log

=== DELIVERABLE ===
A single structured performance report file named: weekly_performance_report.md
This will be read live at the leadership meeting. Make it actionable.
"""

with open("/workspace/weekly_brief_request.txt", "w") as f:
    f.write(brief_content)

print("Workspace initialized. Files created:")
for rel_path in list(distractors.keys()) + ["workspace/weekly_brief_request.txt"]:
    print(f"  /{rel_path}")