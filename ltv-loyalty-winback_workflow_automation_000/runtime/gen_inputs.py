import os
import random
import csv
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Directory structure ---
dirs = [
    "data/customers",
    "data/inventory",
    "data/shipping",
    "reports/monthly",
    "reports/quarterly",
    "ops/fulfillment",
    "ops/returns",
    "marketing/campaigns/2023",
    "marketing/campaigns/2024",
    "references",
    "finance/reconciliation",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- MAIN INPUT 1: Messy customer purchase history CSV ---
# Reference date: 2024-06-15
ref_date = datetime(2024, 6, 15)

customers = []
# VIP customers (high LTV, top decile): 8 customers, LTV > 800
vip_data = [
    ("C001", "Harriet Bloom",    850.00,  150,  "2024-01-02"),  # 165d silent - high risk
    ("C002", "James Rutherford", 1200.50, 95,   "2024-02-14"),  # 122d silent - high risk
    ("C003", "Sophia Nakamura",  920.00,  110,  "2024-03-05"),  # 102d silent - high risk
    ("C004", "Erik Voss",        760.00,  88,   "2024-05-10"),  # 36d silent - ok (but near threshold)
    ("C005", "Lucia Ferreira",   1550.75, 200,  "2024-02-28"),  # 107d silent - high risk
    ("C006", "Omar Al-Rashid",   830.00,  120,  "2024-03-18"),  # 89d silent - at risk
    ("C007", "Nina Castillo",    990.25,  145,  "2024-01-20"),  # 147d silent - high risk
    ("C008", "Derek Huang",      870.50,  105,  "2024-03-20"),  # 87d silent - at risk
]
# Standard customers: 20 customers
standard_data = [
    ("C009",  "Priya Mehta",     210.00,  30,  "2024-03-10"),   # 97d silent - at risk
    ("C010",  "Liam O'Brien",    180.50,  22,  "2024-02-20"),   # 116d - high risk
    ("C011",  "Fatima Siddiqui", 95.00,   12,  "2024-04-01"),   # 75d
    ("C012",  "Ethan Croft",     320.00,  40,  "2024-01-15"),   # 152d - high risk
    ("C013",  "Yuki Tanaka",     150.00,  18,  "2024-03-25"),   # 82d - at risk
    ("C014",  "Aisha Nwosu",     88.00,   9,   "2024-04-20"),   # 56d
    ("C015",  "Carlos Rivera",   245.00,  28,  "2024-02-10"),   # 126d - high risk
    ("C016",  "Mei Lin",         130.75,  16,  "2024-03-01"),   # 106d - high risk
    ("C017",  "Samuel Okafor",   190.00,  23,  "2024-04-05"),   # 71d
    ("C018",  "Zoe Fischer",     75.00,   8,   "2024-04-18"),   # 58d
    ("C019",  "Ivan Petrov",     280.00,  35,  "2024-01-28"),   # 139d - high risk
    ("C020",  "Amara Diallo",    115.50,  14,  "2024-03-15"),   # 92d - at risk
    ("C021",  "Ben Whitfield",   60.00,   6,   "2024-05-01"),   # 45d
    ("C022",  "Chloe Dupont",    400.25,  50,  "2024-02-05"),   # 131d - high risk
    ("C023",  "Hassan Al-Farsi", 175.00,  20,  "2024-03-08"),   # 99d - at risk
    ("C024",  "Rosa Martínez",   95.25,   11,  "2024-04-12"),   # 64d
    ("C025",  "Tom Bergmann",    220.00,  27,  "2024-01-05"),   # 162d - high risk
    ("C026",  "Lin Xiao",        310.00,  38,  "2024-03-22"),   # 85d - at risk
    ("C027",  "Kelly Nguyen",    145.00,  17,  "2024-02-25"),   # 111d - high risk
    ("C028",  "Aaron McBride",   55.00,   5,   "2024-05-20"),   # 26d
]

all_customers = vip_data + standard_data

with open(workspace / "data/customers/purchase_history.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "customer_id", "customer_name", "cumulative_ltv_usd", "total_orders_12mo",
        "last_purchase_date", "signup_date", "preferred_channel"
    ])
    channels = ["email", "sms", "email", "app_push", "email", "sms"]
    for i, row in enumerate(all_customers):
        signup = (ref_date - timedelta(days=random.randint(400, 1200))).strftime("%Y-%m-%d")
        writer.writerow([
            row[0], row[1], row[2], row[3], row[4], signup,
            channels[i % len(channels)]
        ])

# --- MAIN INPUT 2: Tier and points CSV ---
# Some customers have points about to expire (within 14 days of ref date = by 2024-06-29)
# Points expiry triggers mandatory branch

points_data = [
    # customer_id, tier, points_balance, points_expiry_date
    ("C001", "Gold",     1200, "2024-06-22"),   # expires in 7 days - URGENT
    ("C002", "Platinum", 3500, "2024-07-10"),   # expires in 25 days
    ("C003", "Gold",     800,  "2024-06-20"),   # expires in 5 days - URGENT
    ("C004", "Gold",     500,  "2024-08-01"),
    ("C005", "Platinum", 5000, "2024-06-27"),   # expires in 12 days - URGENT
    ("C006", "Gold",     950,  "2024-07-15"),
    ("C007", "Gold",     1100, "2024-06-19"),   # expires in 4 days - URGENT
    ("C008", "Silver",   420,  "2024-07-20"),
    ("C009", "Silver",   200,  "2024-06-28"),   # expires in 13 days - URGENT
    ("C010", "Bronze",   80,   "2024-09-01"),
    ("C011", "Bronze",   50,   "2024-10-15"),
    ("C012", "Silver",   310,  "2024-07-05"),
    ("C013", "Bronze",   90,   "2024-08-10"),
    ("C015", "Silver",   240,  "2024-06-25"),   # expires in 10 days - URGENT
    ("C016", "Bronze",   60,   "2024-09-20"),
    ("C019", "Silver",   180,  "2024-07-08"),
    ("C022", "Silver",   290,  "2024-07-02"),
    ("C025", "Bronze",   40,   "2024-09-15"),
    ("C026", "Silver",   350,  "2024-06-29"),   # expires in 14 days - URGENT
    ("C027", "Bronze",   70,   "2024-08-25"),
]

with open(workspace / "data/customers/tier_points.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["customer_id", "tier", "points_balance", "points_expiry_date", "tier_since"])
    for row in points_data:
        tier_since = (ref_date - timedelta(days=random.randint(90, 730))).strftime("%Y-%m-%d")
        writer.writerow([row[0], row[1], row[2], row[3], tier_since])

# --- DISTRACTOR FILES ---

# 1. Monthly revenue report (distractor)
with open(workspace / "reports/monthly/revenue_june_2024.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["month", "total_revenue", "orders", "new_customers", "returning_customers"])
    writer.writerow(["2024-06", 48200.50, 312, 87, 225])
    writer.writerow(["2024-05", 51300.00, 328, 92, 236])
    writer.writerow(["2024-04", 44100.75, 290, 78, 212])

# 2. Inventory status (distractor)
with open(workspace / "data/inventory/stock_levels.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sku", "product_name", "stock_qty", "reorder_point", "category"])
    products = [
        ("PF-001", "Premium Salmon Kibble 5kg", 120, 30, "dry_food"),
        ("PF-002", "Grain-Free Turkey Pate", 85, 20, "wet_food"),
        ("PF-003", "Hip & Joint Supplement", 200, 50, "supplements"),
        ("AC-001", "Adjustable Harness M", 45, 10, "accessories"),
        ("TR-001", "Freeze-Dried Liver Treats", 300, 80, "treats"),
    ]
    for p in products:
        writer.writerow(p)

# 3. Shipping log (distractor)
with open(workspace / "data/shipping/shipments_q2_2024.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["order_id", "customer_id", "shipped_date", "carrier", "status", "delivery_days"])
    for i in range(20):
        writer.writerow([
            f"ORD-{9000+i}", f"C{random.randint(1,28):03d}",
            (ref_date - timedelta(days=random.randint(5, 90))).strftime("%Y-%m-%d"),
            random.choice(["FedEx", "UPS", "USPS"]),
            random.choice(["delivered", "delivered", "delivered", "returned"]),
            random.randint(2, 8)
        ])

# 4. Returns analysis (distractor)
with open(workspace / "ops/returns/return_reasons_q2.txt", "w") as f:
    f.write("Return Reasons Summary - Q2 2024\n")
    f.write("================================\n")
    f.write("Wrong size: 34%\n")
    f.write("Product not as described: 22%\n")
    f.write("Changed mind: 18%\n")
    f.write("Damaged in transit: 26%\n")
    f.write("\nTotal returns: 47\n")
    f.write("Return rate: 15.1%\n")

# 5. Affiliate reconciliation (distractor - explicitly NOT this skill)
with open(workspace / "finance/reconciliation/affiliate_q2_2024.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["affiliate_id", "partner_name", "clicks", "conversions", "commission_usd"])
    writer.writerow(["AFF-001", "PetBlog Network", 1200, 45, 337.50])
    writer.writerow(["AFF-002", "DogMom Influencer", 3400, 112, 840.00])
    writer.writerow(["AFF-003", "CatDad Reviews", 890, 28, 210.00])

# 6. Quarterly business review deck notes (distractor)
with open(workspace / "reports/quarterly/qbr_notes_q2_2024.txt", "w") as f:
    f.write("Q2 2024 Business Review Notes\n")
    f.write("================================\n")
    f.write("- Repeat purchase rate dropped from 38% to 29% YoY\n")
    f.write("- 90-day non-repurchase cohort grew 41% vs Q1\n")
    f.write("- Subscription box cancellations up 15%\n")
    f.write("- Top complaint: forgot about us / busy\n")
    f.write("- AOV stable at $54.20\n")
    f.write("- Marketing spend efficiency down 8%\n")

# 7. Ops fulfillment SLAs (distractor)
with open(workspace / "ops/fulfillment/sla_targets_2024.txt", "w") as f:
    f.write("Fulfillment SLA Targets 2024\n")
    f.write("Same-day dispatch cutoff: 2pm EST\n")
    f.write("Standard ground: 3-5 business days\n")
    f.write("Express: next business day\n")
    f.write("Error rate target: < 0.5%\n")

# 8. Campaign performance archive (distractor)
with open(workspace / "marketing/campaigns/2023/black_friday_2023_results.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["campaign", "sent", "open_rate", "click_rate", "conversion_rate", "revenue"])
    writer.writerow(["BF2023_email_burst", 8400, 0.31, 0.12, 0.034, 12400.00])
    writer.writerow(["BF2023_sms_flash", 3200, None, 0.18, 0.041, 5100.00])

# 9. 2024 active campaigns (distractor)
with open(workspace / "marketing/campaigns/2024/summer_promo_brief.txt", "w") as f:
    f.write("Summer Promo 2024 - Internal Brief\n")
    f.write("Campaign window: July 1 - July 31 2024\n")
    f.write("Offer: 20% off all supplements\n")
    f.write("Target: all active customers (last purchase < 60 days)\n")
    f.write("Note: Do NOT overlap with win-back flows\n")

# 10. Customer service scripts (distractor)
with open(workspace / "ops/fulfillment/cs_escalation_scripts.txt", "w") as f:
    f.write("CS Escalation Scripts v3.1\n")
    f.write("==========================\n")
    f.write("Script A: Order not received\n")
    f.write("Script B: Wrong item shipped\n")
    f.write("Script C: Subscription pause request\n")
    f.write("Script D: Loyalty points dispute\n")

# 11. A misleading 'loyalty_notes.txt' (distractor - incomplete, not the playbook)
with open(workspace / "references/loyalty_notes.txt", "w") as f:
    f.write("Loyalty Program Quick Reference (DRAFT - incomplete)\n")
    f.write("VIP threshold: TBD\n")
    f.write("Points expiry: rolling 90 days from last earn... wait, check with ops team\n")
    f.write("Tier names: Bronze, Silver, Gold, Platinum\n")
    f.write("DO NOT USE FOR CAMPAIGNS - outdated\n")

# 12. Finance distractor
with open(workspace / "finance/reconciliation/cogs_q2_2024.txt", "w") as f:
    f.write("COGS Summary Q2 2024\n")
    f.write("Dry food margin: 42%\n")
    f.write("Wet food margin: 38%\n")
    f.write("Supplements margin: 61%\n")
    f.write("Accessories margin: 55%\n")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")