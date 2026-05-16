import os
import random
import csv
from pathlib import Path

random.seed(42)

# ── root workspace ──────────────────────────────────────────────────────────
ws = Path("/workspace")
ws.mkdir(parents=True, exist_ok=True)

# ── realistic directory structure (distractor files) ────────────────────────
dirs = [
    "data/raw_orders",
    "data/marketing",
    "data/product",
    "reports/q1",
    "reports/q2",
    "finance/invoices",
    "finance/budgets",
    "ops/logistics",
    "ops/crm",
    "references",
    "scripts/legacy",
]
for d in dirs:
    (ws / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractor_data = {
    "data/product/sku_catalog.csv": (
        "sku_id,product_name,category,unit_cost,msrp\n"
        "SKU001,Salmon Kibble 2kg,dry_food,18.50,45.00\n"
        "SKU002,Chicken Wet Pouch 12pk,wet_food,22.00,54.00\n"
        "SKU003,Probiotic Supplement,supplement,8.00,28.00\n"
        "SKU004,Lamb Senior Formula 2kg,dry_food,20.00,49.00\n"
    ),
    "data/product/inventory_snapshot.csv": (
        "sku_id,warehouse,stock_units,reorder_point\n"
        "SKU001,SH_EAST,1200,300\n"
        "SKU002,SH_EAST,870,200\n"
        "SKU003,BJ_NORTH,430,100\n"
    ),
    "reports/q1/channel_summary.txt": (
        "Q1 Channel Performance (DRAFT - DO NOT DISTRIBUTE)\n"
        "Paid Social: 1,240 new customers\n"
        "SEO: 310 new customers\n"
        "Referral: 88 new customers\n"
        "Note: CAC figures need finance sign-off.\n"
    ),
    "reports/q2/notes.txt": (
        "Q2 review postponed. Awaiting updated retention data from CRM team.\n"
    ),
    "finance/budgets/fy2024_plan.txt": (
        "FY2024 Marketing Budget Allocation (PRELIMINARY)\n"
        "Paid Social: CNY 2,400,000\n"
        "SEO/Content: CNY 480,000\n"
        "Influencer: CNY 360,000\n"
        "Retention/Email: CNY 120,000\n"
    ),
    "finance/invoices/agency_nov.txt": (
        "Invoice #INV-2023-1147\nAgency: GrowthPulse Digital\n"
        "Service: Paid Social Management Nov 2023\nAmount: CNY 85,000\n"
        "Status: PAID\n"
    ),
    "ops/logistics/fulfillment_rates.csv": (
        "tier,weight_kg,base_cost_cny,remote_surcharge\n"
        "standard,0-2,12.00,5.00\n"
        "standard,2-5,18.00,8.00\n"
        "express,0-2,22.00,10.00\n"
    ),
    "ops/crm/segment_tags.csv": (
        "segment,tag,description\n"
        "high_value,HV,3+ orders LTM\n"
        "at_risk,AR,no order 90+ days\n"
        "new,NEW,first order <30 days\n"
    ),
    "scripts/legacy/old_ltv_v1.py": (
        "# DEPRECATED v1 LTV script – revenue-based only, do not use\n"
        "# avg_order_value * purchase_frequency * customer_lifespan\n"
        "def ltv_simple(aov, freq, lifespan):\n"
        "    return aov * freq * lifespan\n"
        "\n"
        "# This ignores COGS, returns, and full CAC components.\n"
        "# Replaced by new framework.\n"
    ),
    "scripts/legacy/cac_estimate_rough.txt": (
        "Rough CAC estimate FY2023 (ad spend only - INCOMPLETE)\n"
        "Total ad spend: CNY 1,800,000\n"
        "New customers acquired: 6,000\n"
        "Rough CAC = 300 CNY\n"
        "WARNING: Does not include agency fees, team cost, or discount vouchers.\n"
    ),
    "references/competitor_benchmarks.txt": (
        "Industry Benchmarks (Pet Food DTC, China Market, 2023)\n"
        "LTV:CAC healthy ratio: >= 3:1\n"
        "Payback period target: <= 6 months\n"
        "Average 12-month repurchase rate: 38%-55%\n"
        "Source: Internal research, not verified externally.\n"
    ),
}

for rel_path, content in distractor_data.items():
    (ws / rel_path).write_text(content, encoding="utf-8")

# ── CORE PROBLEM INPUT FILES ─────────────────────────────────────────────────

# 1. Raw orders CSV (last 12 months, paid social channel customers only)
#    Deliberately messy: mixed date formats, some missing gmv, refund flag
orders_header = [
    "order_id", "customer_id", "order_date", "channel_first_touch",
    "gmv_cny", "cogs_cny", "refund_flag", "discount_applied_cny",
    "fulfillment_cost_cny"
]

# We generate 380 synthetic orders from 120 paid-social customers
# Some customers have 1 order, some have up to 6 over 12 months
# This will produce realistic repeat-purchase data

customers = [f"C{str(i).zfill(4)}" for i in range(1, 121)]
order_rows = []
oid = 1000

random.seed(42)

for cid in customers:
    n_orders = random.choices([1, 2, 3, 4, 5, 6], weights=[30, 28, 22, 12, 5, 3])[0]
    for _ in range(n_orders):
        # Messy date formats
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        year = 2023
        if random.random() < 0.15:
            date_str = f"{day:02d}/{month:02d}/{year}"   # dd/mm/yyyy
        elif random.random() < 0.1:
            date_str = f"{year}.{month:02d}.{day:02d}"  # yyyy.mm.dd
        else:
            date_str = f"{year}-{month:02d}-{day:02d}"  # ISO

        gmv = round(random.uniform(38, 120), 2)
        # COGS is 42-55% of GMV
        cogs = round(gmv * random.uniform(0.42, 0.55), 2)
        refund = 1 if random.random() < 0.06 else 0
        discount = round(random.uniform(0, 15), 2) if random.random() < 0.35 else 0.0
        fulfillment = round(random.uniform(10, 20), 2)

        # Some rows have missing gmv (messy data)
        if random.random() < 0.04:
            gmv_val = ""
            cogs_val = ""
        else:
            gmv_val = gmv
            cogs_val = cogs

        order_rows.append([
            f"ORD{oid}", cid, date_str, "paid_social",
            gmv_val, cogs_val, refund, discount, fulfillment
        ])
        oid += 1

with open(ws / "data/raw_orders/paid_social_orders_2023.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(orders_header)
    writer.writerows(order_rows)

# 2. Marketing cost breakdown (deliberately fragmented, all components present)
marketing_cost_content = """# Paid Social Channel – Full Cost Breakdown FY2023
# Source: Finance & Marketing Ops

## Ad Spend (Platform Media Buy)
Platform: Meta (Facebook/Instagram)
Total Ad Spend: CNY 1,800,000
New Customers Acquired (attributed, last-click): 6,000

## Channel Service Fee
Agency: GrowthPulse Digital
Monthly Retainer: CNY 85,000 x 12 months = CNY 1,020,000
Performance Bonus (Q4): CNY 48,000
Total Channel Service Fee: CNY 1,068,000

## Internal Team Cost (Marketing headcount allocated to paid social)
FTE: 1.5 headcount
Average fully-loaded cost per FTE: CNY 280,000/year
Total Team Cost: CNY 420,000

## Discount & Voucher Subsidies
New customer welcome voucher: CNY 20 per customer
Total vouchers redeemed by new customers: 5,400 out of 6,000
Total Voucher Cost: CNY 108,000

## Summary
Note: The "rough CAC" figure circulating (CNY 300) is WRONG.
It only includes ad spend. Full blended CAC must include all four components above.
New customers acquired: 6,000
"""
(ws / "data/marketing/paid_social_cost_breakdown_2023.txt").write_text(
    marketing_cost_content, encoding="utf-8"
)

# 3. A brief business context memo
memo_content = """TO: Growth Analytics
FROM: CFO Office
SUBJECT: Paid Social Channel Evaluation – Action Required

We are considering doubling the paid social budget for FY2024.
Before we commit, we need a rigorous assessment of whether the
paid social customers we acquired in FY2023 are generating sustainable value.

Key questions for the analysis:
- What is the true 12-month LTV of a paid-social-acquired customer,
  measured on gross profit (not revenue)?
- What is the fully-loaded CAC for this channel (all cost components)?
- Is the LTV:CAC ratio healthy? What is the payback period?
- What is the single weakest assumption in our model?

The CFO wants a single report file with assumptions clearly stated,
the numbers, the risks, and a reusable Python script so we can
re-run this quarterly with updated data.

Data available:
- data/raw_orders/paid_social_orders_2023.csv
- data/marketing/paid_social_cost_breakdown_2023.txt

Please deliver the report as: ltv_cac_report.md
"""
(ws / "business_context_memo.txt").write_text(memo_content, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(list(ws.rglob('*')))} total entries")