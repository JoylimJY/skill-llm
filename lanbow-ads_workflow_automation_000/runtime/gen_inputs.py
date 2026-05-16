import os
import json
import yaml
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "ops/media/meta",
    "ops/media/google",
    "ops/media/tiktok",
    "ops/reporting/weekly",
    "ops/reporting/daily",
    "ops/creative/assets",
    "ops/creative/copy",
    "ops/finance/invoices",
    "ops/finance/budget_tracker",
    "ops/compliance/policy_flags",
    "ops/analytics/attribution",
    "ops/analytics/cohorts",
    "ops/tracking/pixels",
    "ops/tracking/server_side",
    "briefs/archived",
    "briefs/drafts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "ops/media/meta/audience_sets_v3.json": json.dumps({
        "lookalikes": ["LAL_purchasers_1pct", "LAL_adders_2pct"],
        "interests": ["fitness_equipment", "home_gym"],
        "retargeting": ["view_content_30d", "add_to_cart_7d"],
        "notes": "Deprecated segment list - superseded by v4"
    }, indent=2),

    "ops/media/google/keyword_lists_draft.txt": "\n".join([
        "home gym equipment",
        "buy treadmill online",
        "adjustable dumbbells",
        "resistance bands set",
        "exercise bike deals",
        "NOTE: These are broad match - review before launch"
    ]),

    "ops/media/tiktok/creative_rotation_log.csv": (
        "creative_id,impressions,clicks,ctr,status\n"
        "TT_VID_001,450000,12300,0.0273,active\n"
        "TT_VID_002,380000,8900,0.0234,active\n"
        "TT_VID_003,120000,2100,0.0175,paused_low_ctr\n"
        "TT_VID_004,0,0,0,pending_review\n"
    ),

    "ops/reporting/weekly/week22_summary.txt": (
        "Week 22 Summary - Internal Draft\n"
        "Total spend: $48,200\n"
        "Conversions: 1,104\n"
        "Blended CPA: $43.66\n"
        "Blended ROAS: 2.31\n"
        "NOTE: Attribution window discrepancy flagged by analytics team\n"
        "Status: NEEDS REVIEW before distribution"
    ),

    "ops/reporting/daily/day_over_day_deltas.json": json.dumps({
        "date": "2024-06-10",
        "spend_delta_pct": 28.4,
        "roas_delta_pct": -22.1,
        "cpa_delta_pct": 19.3,
        "impression_delta_pct": 31.2,
        "note": "Anomalous day - possible pixel misfire on checkout page"
    }, indent=2),

    "ops/creative/assets/asset_inventory.md": (
        "# Creative Asset Inventory\n\n"
        "## Video Assets\n"
        "- hero_30sec_v2.mp4 (approved)\n"
        "- product_demo_15sec.mp4 (approved)\n"
        "- testimonial_compilation_45sec.mp4 (pending legal)\n\n"
        "## Static Assets\n"
        "- lifestyle_banner_1200x628.jpg (approved)\n"
        "- product_white_bg_1080x1080.jpg (approved)\n\n"
        "## Status: 2 assets in legal review, do not run"
    ),

    "ops/creative/copy/headline_variants.txt": (
        "Headline Variants for A/B Test\n"
        "A: 'Transform Your Home Gym in 7 Days'\n"
        "B: 'Equipment That Grows With You'\n"
        "C: 'Free Shipping + 30-Day Returns'\n"
        "D: 'Limited Stock — Order Now'\n"
        "Control: 'Build Your Best Home Gym'\n"
        "TEST STATUS: Not yet launched - awaiting ops approval"
    ),

    "ops/finance/budget_tracker/q2_allocation.csv": (
        "channel,monthly_budget_usd,ytd_spend_usd,remaining_usd,pacing_status\n"
        "Meta,35000,18200,16800,on_track\n"
        "GoogleAds,25000,14100,10900,slightly_ahead\n"
        "TikTokAds,15000,9800,5200,ahead_of_pace\n"
        "Total,75000,42100,32900,\n"
    ),

    "ops/finance/invoices/agency_invoice_may.txt": (
        "Agency Invoice #INV-2024-0512\n"
        "Period: May 2024\n"
        "Management Fee: $4,200\n"
        "Performance Bonus: $800\n"
        "Total Due: $5,000\n"
        "Payment Terms: NET-30\n"
        "DO NOT SHARE externally"
    ),

    "ops/compliance/policy_flags/meta_account_health.json": json.dumps({
        "account_id": "ACT_88234719",
        "health_score": "yellow",
        "active_flags": ["billing_threshold_approaching", "ad_relevance_low_on_3_ads"],
        "suspended_ads": 0,
        "policy_violations": [],
        "recommended_action": "Review low relevance ads before scaling budget"
    }, indent=2),

    "ops/analytics/attribution/model_comparison.json": json.dumps({
        "models_tested": ["last_click", "data_driven", "linear", "time_decay"],
        "recommended": "data_driven",
        "confidence": "medium",
        "note": "Pixel firing rate dropped to 78% on June 9 - data_driven model less reliable for that day",
        "pending_validation": True
    }, indent=2),

    "ops/tracking/pixels/pixel_health_report.txt": (
        "Pixel Health Check - June 10 2024\n"
        "Meta Pixel: 78% fire rate (target: >95%) — DEGRADED\n"
        "Google Tag: 94% fire rate — OK\n"
        "TikTok Pixel: 81% fire rate — DEGRADED\n"
        "Root Cause: Checkout page JS error introduced in deploy v2.4.1\n"
        "Resolution ETA: 4-6 hours (dev team notified)\n"
        "IMPACT: Conversion underreporting on Meta and TikTok"
    ),

    "ops/tracking/server_side/s2s_status.txt": (
        "Server-Side Tracking Status\n"
        "Meta CAPI: ACTIVE - 92% event match score\n"
        "Google Enhanced Conversions: ACTIVE - 88% match\n"
        "TikTok Events API: INACTIVE - not yet configured\n"
        "Action Required: Enable TikTok Events API to compensate for pixel degradation"
    ),

    "briefs/archived/launch_brief_v1.txt": (
        "ARCHIVED - DO NOT USE\n"
        "Original launch brief for FitHome Pro campaign\n"
        "Superseded by v3 brief (see briefs/drafts/)\n"
        "Original CPA target: $50 (revised down to $42)\n"
        "Original ROAS target: 2.0 (revised up to 2.5)\n"
    ),

    "briefs/drafts/campaign_context_dump.txt": (
        "FitHome Pro — Campaign Operations Context Dump\n"
        "Last Updated: June 10, 2024 14:30 UTC\n\n"
        "CAMPAIGN OBJECTIVE: Improve ROAS on DTC purchases for FitHome Pro equipment line\n"
        "CHANNELS IN SCOPE: Meta (Facebook + Instagram), Google Ads, TikTok Ads\n"
        "BUDGET MODE: Intended staged scale — currently paused pending anomaly review\n\n"
        "CPA CEILING: $42 USD (hard limit per finance)\n"
        "ROAS FLOOR: 2.5 (minimum acceptable for scaling approval)\n\n"
        "CURRENT STATUS (as of today):\n"
        "- Spend surged +28.4% day-over-day (unexpected)\n"
        "- ROAS dropped -22.1% day-over-day (now at ~2.31, below floor)\n"
        "- CPA rose to ~$43.66 (above $42 ceiling)\n"
        "- Meta pixel degraded to 78% fire rate (checkout JS error)\n"
        "- TikTok pixel degraded to 81% fire rate\n"
        "- Google Tag healthy at 94%\n"
        "- Meta account health: yellow flag (billing threshold + low relevance ads)\n"
        "- TikTok Events API not configured (gaps in server-side coverage)\n"
        "- 3 headline creative variants ready but not launched (pending approval)\n"
        "- Attribution confidence: MEDIUM (pixel issues affect data-driven model)\n\n"
        "OPEN QUESTIONS:\n"
        "1. Should we pause TikTok spend until pixel is fixed?\n"
        "2. Can we still launch A/B test on headlines this week?\n"
        "3. How do we stage budget recovery after anomaly clears?\n"
        "4. What monitoring rules should be active during recovery?\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

print(f"Workspace generated with {len(distractors)} files across {len(dirs)} directories.")
print("Workspace root:", workspace)