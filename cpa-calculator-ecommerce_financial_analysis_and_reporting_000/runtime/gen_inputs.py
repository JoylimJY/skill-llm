import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "products",
    "campaigns/q4_launch",
    "campaigns/archive",
    "finance/2023",
    "finance/2024/q3",
    "finance/2024/q4",
    "marketing/briefs",
    "marketing/reports",
    "ops/fulfillment",
    "ops/returns",
    "legal",
    "analytics/funnels",
    "analytics/cohorts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── references/output-template.md  (the template agents MUST follow) ─────────
output_template = """\
# CPA 计算输出模板

## 1. 假设表 (Assumptions Table)

| 参数 | 值 |
|------|----|
| 售价 (Selling Price) | |
| 毛利率 (Gross Margin %) | |
| 履约成本 (Fulfillment Cost) | |
| 退款率 (Refund Rate %) | |
| 折扣 / 优惠 (Discount) | |
| 目标转化率 (Target CVR %) | |
| 复购贡献 (Repeat Purchase Contribution) | |

## 2. Break-even CPA

Break-even CPA = 单客户净利润 (Net Profit per Customer)

计算路径：
- 有效售价 = 售价 × (1 - 折扣率)
- 退款损失 = 有效售价 × 退款率
- 单客净利润 = 有效售价 × 毛利率 - 履约成本 - 退款损失 + 复购贡献

Break-even CPA = 单客净利润

## 3. Allowable CPA 区间

Allowable CPA = Break-even CPA × 安全系数 (Safety Factor)

- 保守 (Conservative): Break-even CPA × 0.5
- 稳健 (Moderate): Break-even CPA × 0.7
- 激进 (Aggressive): Break-even CPA × 0.9

## 4. 建议动作 (Recommended Actions)

针对以下维度给出具体建议：
- 定价 / 提价
- 折扣控制
- 转化率提升
- 退款率改善
- 出价策略

---
每个 SKU / Offer 输出一份独立报告。
"""

with open(os.path.join(BASE, "references/output-template.md"), "w") as f:
    f.write(output_template)

# ── products/sku_data_raw.json  (messy, realistic product data) ──────────────
# Three SKUs: starter_pack, subscription_bundle, premium_bundle
sku_raw = {
    "_note": "Raw export from Shopify admin — some fields use inconsistent naming, legacy columns retained for audit",
    "_export_date": "2024-10-01",
    "skus": [
        {
            "id": "SKU-001",
            "name": "Starter Pack",
            "list_price_usd": 49.00,
            "cogs_per_unit": 12.50,
            "shipping_and_handling": 4.80,
            "warehouse_pick_pack": 1.20,
            "promo_discount_pct": 10,          # percent, e.g. 10 = 10%
            "return_rate_pct": 8,              # percent
            "expected_cvr_pct": 2.5,           # landing page CVR
            "ltv_repeat_contribution": 0.00,   # no repeat for starter
            "notes": "Entry offer, Facebook cold traffic",
        },
        {
            "id": "SKU-002",
            "name": "Subscription Bundle (3-month)",
            "list_price_usd": 119.00,
            "cogs_per_unit": 28.00,
            "shipping_and_handling": 6.50,
            "warehouse_pick_pack": 2.10,
            "promo_discount_pct": 15,
            "return_rate_pct": 5,
            "expected_cvr_pct": 1.8,
            "ltv_repeat_contribution": 22.00,  # estimated 2nd-order margin contribution
            "notes": "Subscription upsell, email + retargeting",
        },
        {
            "id": "SKU-003",
            "name": "Premium Bundle (6-month VIP)",
            "list_price_usd": 198.00,
            "cogs_per_unit": 55.00,
            "shipping_and_handling": 8.20,
            "warehouse_pick_pack": 3.00,
            "promo_discount_pct": 5,
            "return_rate_pct": 12,             # higher — premium buyer remorse
            "expected_cvr_pct": 0.9,
            "ltv_repeat_contribution": 45.00,
            "notes": "High AOV, influencer + YouTube",
        },
    ]
}

with open(os.path.join(BASE, "products/sku_data_raw.json"), "w") as f:
    json.dump(sku_raw, f, indent=2, ensure_ascii=False)

# ── campaigns/q4_launch/brief.txt  (campaign context, distractor) ────────────
brief = """\
Q4 2024 Paid Acquisition Launch Brief
=====================================
Objective: Scale paid channels (Meta, Google, TikTok) for the nutraceutical line.
Budget: $150,000 total across 3 SKUs.
KPIs: ROAS > 2.5, Target CPA TBD (pending finance sign-off).
Timeline: Campaign live Nov 1 – Dec 31.
Owner: Growth team.

Pending: Finance to provide CPA guardrails per SKU before bid strategy is locked.
"""
with open(os.path.join(BASE, "campaigns/q4_launch/brief.txt"), "w") as f:
    f.write(brief)

# ── finance/2024/q4/margin_assumptions_DRAFT.csv  (distractor, incomplete) ───
margin_csv = """\
sku_id,gross_margin_pct,note
SKU-001,,,needs reconciliation with ops
SKU-002,,,TBD
SKU-003,,,pending COGS audit
"""
with open(os.path.join(BASE, "finance/2024/q4/margin_assumptions_DRAFT.csv"), "w") as f:
    f.write(margin_csv)

# ── ops/fulfillment/cost_center_2024.txt  (distractor) ───────────────────────
with open(os.path.join(BASE, "ops/fulfillment/cost_center_2024.txt"), "w") as f:
    f.write("Fulfillment cost codes — internal use only.\nSee Netsuite for actuals.\n")

# ── ops/returns/policy.txt  (distractor) ─────────────────────────────────────
with open(os.path.join(BASE, "ops/returns/policy.txt"), "w") as f:
    f.write("30-day return window. Customer pays return shipping.\nSee sku_data_raw.json for per-SKU rates.\n")

# ── marketing/briefs/channel_mix.txt  (distractor) ───────────────────────────
with open(os.path.join(BASE, "marketing/briefs/channel_mix.txt"), "w") as f:
    f.write("Meta 40%, Google 30%, TikTok 20%, Influencer 10%\n")

# ── analytics/funnels/cvr_history.csv  (distractor, old data) ────────────────
cvr_csv = "sku_id,month,cvr_pct\nSKU-001,2024-07,2.1\nSKU-001,2024-08,2.3\nSKU-002,2024-07,1.5\nSKU-003,2024-07,0.7\n"
with open(os.path.join(BASE, "analytics/funnels/cvr_history.csv"), "w") as f:
    f.write(cvr_csv)

# ── analytics/cohorts/ltv_model.txt  (distractor) ────────────────────────────
with open(os.path.join(BASE, "analytics/cohorts/ltv_model.txt"), "w") as f:
    f.write("LTV model v2 — cohort-level only. Use ltv_repeat_contribution in sku_data_raw.json for per-unit estimates.\n")

# ── legal/disclaimer.txt  (distractor) ───────────────────────────────────────
with open(os.path.join(BASE, "legal/disclaimer.txt"), "w") as f:
    f.write("All CPA figures are internal estimates and do not constitute financial advice.\n")

# ── campaigns/archive/2023_q4_results.txt  (distractor) ──────────────────────
with open(os.path.join(BASE, "campaigns/archive/2023_q4_results.txt"), "w") as f:
    f.write("2023 Q4: CPA avg $31. ROAS 2.8. No per-SKU breakdown available.\n")

# ── finance/2023/annual_summary.txt  (distractor) ────────────────────────────
with open(os.path.join(BASE, "finance/2023/annual_summary.txt"), "w") as f:
    f.write("FY2023 revenue: $4.2M. Gross margin: 58%. Fulfillment: 12% of revenue.\n")

# ── marketing/reports/q3_2024_post_mortem.txt  (distractor) ──────────────────
with open(os.path.join(BASE, "marketing/reports/q3_2024_post_mortem.txt"), "w") as f:
    f.write("Q3 2024: CPAs were above target for SKU-001 and SKU-003. Root cause TBD.\n")

print("Workspace generated successfully.")