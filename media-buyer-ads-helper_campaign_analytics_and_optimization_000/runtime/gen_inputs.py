import json
import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "accounts/meta/campaigns",
    "accounts/google/campaigns",
    "accounts/tiktok/campaigns",
    "accounts/amazon/legacy",
    "reports/weekly",
    "reports/monthly",
    "creatives/video",
    "creatives/static",
    "finance/invoices",
    "finance/budgets",
    "analytics/attribution",
    "analytics/funnel",
    "ops/runbooks",
    "ops/alerts_old",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (irrelevant noise) ---
distractors = [
    ("reports/weekly/wk24_summary.txt", "Weekly summary - manually compiled. No action needed."),
    ("reports/monthly/june_finance.csv", "campaign,spend,revenue\ncamp_001,12000,38000\ncamp_002,8500,22000"),
    ("creatives/video/asset_log.txt", "video_001.mp4 - approved\nvideo_002.mp4 - rejected (policy)\nvideo_003.mp4 - pending"),
    ("creatives/static/banner_sizes.txt", "300x250, 728x90, 160x600, 320x50"),
    ("finance/invoices/inv_2026_06.txt", "Invoice #4421 - Meta Ads - $45,000 - PAID"),
    ("finance/budgets/q3_plan.txt", "Q3 budget plan: Meta 40%, Google 35%, TikTok 25%"),
    ("analytics/attribution/model_notes.txt", "Using last-click model. Considering shift to data-driven."),
    ("analytics/funnel/conversion_stages.txt", "Awareness -> Consideration -> Purchase -> Retention"),
    ("ops/runbooks/escalation_contacts.txt", "On-call: media_ops@brand.com\nEscalation: head_of_media@brand.com"),
    ("ops/alerts_old/deprecated_thresholds.txt", "OLD RULES - DO NOT USE\nspend_spike: 50%\nconv_drop: 40%"),
    ("accounts/amazon/legacy/old_structure.txt", "Legacy Amazon account structure - migrated 2024. Archive only."),
    ("accounts/meta/campaigns/paused_campaigns.txt", "PAUSED: SALE_2025_Q4_RETARGET, BRAND_AWARENESS_2025_H2"),
]
for path, content in distractors:
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- PROBLEM INPUT 1: Account Structure Snapshot (messy, fragmented, naming violations) ---
account_structure = {
    "account_id": "META-ACT-887612",
    "platform": "Meta",
    "snapshot_date": "2026-07-15",
    "campaigns": [
        {
            "campaign_id": "cmp_001",
            "name": "summer sale",  # naming violation: no platform prefix, lowercase, no date
            "objective": "conversions",
            "status": "active",
            "budget_usd": 120,  # very low budget, high complexity signal
            "adsets": [
                {"adset_id": "as_001", "name": "broad 18-45", "audience": "broad", "bid_strategy": "target_cpa", "target_cpa": 28.0},
                {"adset_id": "as_002", "name": "retarget site visitors", "audience": "retarget", "bid_strategy": "target_cpa", "target_cpa": 28.0},
                {"adset_id": "as_003", "name": "lookalike 1pct", "audience": "lookalike_1pct", "bid_strategy": "target_cpa", "target_cpa": 28.0},
                {"adset_id": "as_004", "name": "lookalike 3pct", "audience": "lookalike_3pct", "bid_strategy": "target_cpa", "target_cpa": 28.0},
                {"adset_id": "as_005", "name": "interest fashion", "audience": "interest_fashion", "bid_strategy": "lowest_cost", "target_cpa": None},
                {"adset_id": "as_006", "name": "interest beauty", "audience": "interest_beauty", "bid_strategy": "lowest_cost", "target_cpa": None},
                {"adset_id": "as_007", "name": "retarget add to cart", "audience": "retarget_atc", "bid_strategy": "target_cpa", "target_cpa": 28.0},
            ]
        },
        {
            "campaign_id": "cmp_002",
            "name": "META_BRAND_AWARENESS_JULY2026",
            "objective": "reach",
            "status": "active",
            "budget_usd": 500,
            "adsets": [
                {"adset_id": "as_010", "name": "META_BRAND_BROAD_JULY2026", "audience": "broad", "bid_strategy": "cost_cap", "target_cpa": 5.0},
            ]
        },
        {
            "campaign_id": "cmp_003",
            "name": "google retarget",  # naming violation
            "objective": "conversions",
            "status": "active",
            "budget_usd": 80,  # very low
            "adsets": [
                {"adset_id": "as_020", "name": "goog ret cart", "audience": "retarget_cart", "bid_strategy": "target_cpa", "target_cpa": 30.0},
                {"adset_id": "as_021", "name": "goog ret pdp", "audience": "retarget_pdp", "bid_strategy": "target_cpa", "target_cpa": 30.0},
                {"adset_id": "as_022", "name": "goog ret checkout", "audience": "retarget_checkout", "bid_strategy": "target_cpa", "target_cpa": 30.0},
                {"adset_id": "as_023", "name": "goog broad match", "audience": "broad_match_kw", "bid_strategy": "maximize_conversions", "target_cpa": None},
            ]
        }
    ],
    "total_active_adsets": 12,
    "total_daily_budget_usd": 700
}
with open(os.path.join(workspace, "accounts/meta/campaigns/account_structure_snapshot.json"), "w") as f:
    json.dump(account_structure, f, indent=2)

# --- PROBLEM INPUT 2: Bidding Config (mixed strategies, misalignment) ---
bidding_config = {
    "platform": "Meta",
    "account_id": "META-ACT-887612",
    "kpi_objective": "blended_roas",
    "target_roas": 3.5,
    "bid_strategies_in_use": [
        {"adset_id": "as_001", "strategy": "target_cpa", "value": 28.0, "comment": "legacy setting"},
        {"adset_id": "as_002", "strategy": "target_cpa", "value": 28.0, "comment": "legacy setting"},
        {"adset_id": "as_003", "strategy": "target_cpa", "value": 28.0, "comment": ""},
        {"adset_id": "as_004", "strategy": "target_cpa", "value": 28.0, "comment": ""},
        {"adset_id": "as_005", "strategy": "lowest_cost", "value": None, "comment": "no bid cap set"},
        {"adset_id": "as_006", "strategy": "lowest_cost", "value": None, "comment": "no bid cap set"},
        {"adset_id": "as_007", "strategy": "target_cpa", "value": 28.0, "comment": ""},
        {"adset_id": "as_010", "strategy": "cost_cap", "value": 5.0, "comment": "awareness campaign using cost_cap - misaligned with reach objective"},
        {"adset_id": "as_020", "strategy": "target_cpa", "value": 30.0, "comment": ""},
        {"adset_id": "as_021", "strategy": "target_cpa", "value": 30.0, "comment": ""},
        {"adset_id": "as_022", "strategy": "target_cpa", "value": 30.0, "comment": ""},
        {"adset_id": "as_023", "strategy": "maximize_conversions", "value": None, "comment": "broad match with no constraints"}
    ],
    "notes": "KPI is ROAS but most adsets use target_cpa — potential misalignment. No ROAS-based bid strategy in use."
}
with open(os.path.join(workspace, "accounts/meta/campaigns/bidding_config.json"), "w") as f:
    json.dump(bidding_config, f, indent=2)

# --- PROBLEM INPUT 3: Budget Allocation Snapshot (fragmented) ---
budget_allocation = {
    "snapshot_date": "2026-07-15",
    "total_daily_budget_usd": 700,
    "allocations": [
        {"campaign_id": "cmp_001", "name": "summer sale", "daily_budget": 120, "adset_count": 7, "budget_per_adset": 17.14},
        {"campaign_id": "cmp_002", "name": "META_BRAND_AWARENESS_JULY2026", "daily_budget": 500, "adset_count": 1, "budget_per_adset": 500},
        {"campaign_id": "cmp_003", "name": "google retarget", "daily_budget": 80, "adset_count": 4, "budget_per_adset": 20}
    ],
    "fragmentation_notes": "cmp_001 has 7 adsets sharing $120/day ($17/adset) — below minimum learning threshold of $50/adset for target_cpa. cmp_003 has 4 adsets sharing $80/day ($20/adset) — same issue.",
    "overlap_flags": [
        "as_001 (broad 18-45) and as_005 (interest fashion) may have audience overlap",
        "as_003 (lookalike 1pct) and as_004 (lookalike 3pct) have partial overlap"
    ]
}
with open(os.path.join(workspace, "accounts/meta/campaigns/budget_allocation_snapshot.json"), "w") as f:
    json.dump(budget_allocation, f, indent=2)

# --- PROBLEM INPUT 4: Recent Performance Series (with anomaly embedded) ---
performance_series = {
    "account_id": "META-ACT-887612",
    "platform": "Meta",
    "period": "2026-07-08 to 2026-07-15",
    "daily_data": [
        {"date": "2026-07-08", "spend": 680, "conversions": 38, "revenue": 2380, "cpa": 17.89, "roas": 3.50, "cpc": 1.12},
        {"date": "2026-07-09", "spend": 695, "conversions": 41, "revenue": 2450, "cpa": 16.95, "roas": 3.53, "cpc": 1.09},
        {"date": "2026-07-10", "spend": 702, "conversions": 39, "revenue": 2430, "cpa": 18.00, "roas": 3.46, "cpc": 1.14},
        {"date": "2026-07-11", "spend": 688, "conversions": 37, "revenue": 2310, "cpa": 18.59, "roas": 3.36, "cpc": 1.18},
        {"date": "2026-07-12", "spend": 710, "conversions": 40, "revenue": 2490, "cpa": 17.75, "roas": 3.51, "cpc": 1.10},
        {"date": "2026-07-13", "spend": 695, "conversions": 38, "revenue": 2400, "cpa": 18.29, "roas": 3.45, "cpc": 1.13},
        {"date": "2026-07-14", "spend": 698, "conversions": 36, "revenue": 2280, "cpa": 19.39, "roas": 3.27, "cpc": 1.22},
        # Anomaly day: spend spikes 43%, conversions drop 33%
        {"date": "2026-07-15", "spend": 998, "conversions": 24, "revenue": 1510, "cpa": 41.58, "roas": 1.51, "cpc": 2.31}
    ],
    "cpa_variance_pct": 45.2,
    "roas_trend": "declining",
    "anomaly_detected": False  # intentionally marked False to test if agent catches it
}
with open(os.path.join(workspace, "accounts/meta/campaigns/recent_performance_series.json"), "w") as f:
    json.dump(performance_series, f, indent=2)

# --- PROBLEM INPUT 5: Test History (weak, inconclusive) ---
test_history = {
    "tests": [
        {
            "test_id": "AB-2026-04",
            "variable": "audience",
            "cells": {"control": "lookalike_1pct", "challenger": "broad"},
            "duration_days": 5,
            "winner": "challenger",
            "confidence": 0.71,
            "notes": "Declared winner at 71% confidence — below 95% threshold."
        },
        {
            "test_id": "AB-2026-05",
            "variable": "creative_format",
            "cells": {"control": "static_banner", "challenger": "video_reel"},
            "duration_days": 3,
            "winner": "challenger",
            "confidence": 0.68,
            "notes": "Underpowered test. Only 3 days, low spend."
        }
    ],
    "issues": "Both prior tests declared winners below statistical significance threshold. Results are unreliable."
}
with open(os.path.join(workspace, "accounts/meta/campaigns/test_history.json"), "w") as f:
    json.dump(test_history, f, indent=2)

# --- PROBLEM INPUT 6: Alert Thresholds config (partially empty — agent must fill gaps) ---
alert_thresholds = {
    "account_id": "META-ACT-887612",
    "defined_rules": [
        {"metric": "cpc_increase_pct", "threshold": 20, "severity": "medium", "action": "review_bidding"},
    ],
    "undefined_rules": ["spend_spike", "conversion_drop", "roas_drop"],
    "notes": "Spend spike and conversion drop rules were never formally configured. Need to be added."
}
with open(os.path.join(workspace, "accounts/meta/campaigns/alert_thresholds.json"), "w") as f:
    json.dump(alert_thresholds, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created across {len(dirs)} directories with {len(distractors)} distractor files.")