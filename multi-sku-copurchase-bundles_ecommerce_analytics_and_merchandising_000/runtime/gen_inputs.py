import os
import random
import csv
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "reports/q1",
    "reports/q2",
    "reports/archive",
    "references",
    "scripts/etl",
    "scripts/analytics",
    "marketing/copy_drafts",
    "marketing/campaigns",
    "ops/inventory",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "data/processed/cleaned_returns.csv").write_text(
    "order_id,sku,qty,return_reason\n1001,BOOT-HK42,1,wrong_size\n1002,SOCK-WL01,2,defective\n"
)
(WORKSPACE / "reports/q1/revenue_summary.txt").write_text(
    "Q1 Total Revenue: $482,310\nTop SKU: TENT-2P-GRN\nReturns: 3.2%\n"
)
(WORKSPACE / "reports/q2/margin_report.csv").write_text(
    "sku,margin_pct\nTENT-2P-GRN,42\nSLEEP-BAG-20F,38\nPAD-FOAM-RL,51\n"
)
(WORKSPACE / "reports/archive/2022_orders_summary.txt").write_text(
    "Archive: 2022 had 14,200 orders. Top bundle guess: tent+sleeping bag (anecdotal).\n"
)
(WORKSPACE / "references/pricing_rules.md").write_text(
    "# Pricing Rules\n- Never discount MAP items below 15% off MSRP.\n- Clearance SKUs excluded from bundles.\n"
)
(WORKSPACE / "references/catalog_snapshot.csv").write_text(
    "sku,name,msrp,category\n"
    "TENT-2P-GRN,2-Person Dome Tent Green,189.99,shelter\n"
    "SLEEP-BAG-20F,Sleeping Bag 20F,79.99,sleep\n"
    "PAD-FOAM-RL,Foam Sleeping Pad Roll,24.99,sleep\n"
    "BOOT-HK42,Hiking Boot 42,139.99,footwear\n"
    "SOCK-WL01,Wool Hiking Socks,14.99,footwear\n"
    "POLE-ALU-PR,Aluminum Trekking Poles Pair,49.99,accessories\n"
    "HEADLAMP-CR,Compact Rechargeable Headlamp,34.99,lighting\n"
    "FILTER-H2O,Water Filter Straw,29.99,hydration\n"
    "PACK-45L-BK,45L Backpack Black,159.99,carry\n"
    "RAINFLY-XT,Extra Rainfly Universal,39.99,shelter\n"
    "GAITERS-L,Trail Gaiters Large,22.99,footwear\n"
    "STOVE-CMP,Compact Camp Stove,54.99,cooking\n"
    "FUEL-CANN,Isobutane Fuel Canister,9.99,cooking\n"
)
(WORKSPACE / "scripts/etl/deduplicate.py").write_text(
    "# ETL stub: deduplication logic\nimport pandas as pd\n# TODO: implement\n"
)
(WORKSPACE / "scripts/analytics/rfm_model.py").write_text(
    "# RFM segmentation placeholder\n# Not yet implemented\n"
)
(WORKSPACE / "marketing/copy_drafts/email_blast_draft.txt").write_text(
    "Subject: Summer Hiking Deals!\nBody: Check out our latest gear...\n"
)
(WORKSPACE / "marketing/campaigns/spring_promo.md").write_text(
    "# Spring Promo 2024\n- 10% off all tents\n- Free shipping on orders > $100\n"
)
(WORKSPACE / "ops/inventory/stock_levels.csv").write_text(
    "sku,qty_on_hand,reorder_point\n"
    "TENT-2P-GRN,82,20\n"
    "SLEEP-BAG-20F,134,30\n"
    "PAD-FOAM-RL,210,50\n"
    "BOOT-HK42,55,15\n"
    "SOCK-WL01,390,80\n"
    "POLE-ALU-PR,67,15\n"
    "HEADLAMP-CR,148,30\n"
    "FILTER-H2O,201,40\n"
    "PACK-45L-BK,43,10\n"
    "RAINFLY-XT,29,10\n"
    "GAITERS-L,88,20\n"
    "STOVE-CMP,61,15\n"
    "FUEL-CANN,512,100\n"
)

# ── MAIN INPUT: messy order line-items CSV ───────────────────────────────────
# Intentionally messy: inconsistent column casing, some blank rows,
# duplicate entries, a few orders with typos in SKU (edge-case noise),
# timestamps in mixed formats, qty sometimes blank (treat as 1).

skus = [
    "TENT-2P-GRN", "SLEEP-BAG-20F", "PAD-FOAM-RL",
    "BOOT-HK42", "SOCK-WL01", "POLE-ALU-PR",
    "HEADLAMP-CR", "FILTER-H2O", "PACK-45L-BK",
    "RAINFLY-XT", "STOVE-CMP", "FUEL-CANN",
]

# Weighted co-purchase baskets (to ensure strong association signals)
# Pattern 1: TENT-2P-GRN + SLEEP-BAG-20F + PAD-FOAM-RL   (camping core, ~180 orders)
# Pattern 2: BOOT-HK42 + SOCK-WL01 + POLE-ALU-PR          (hiking set, ~140 orders)
# Pattern 3: STOVE-CMP + FUEL-CANN                         (cooking pair, ~160 orders)
# Pattern 4: PACK-45L-BK + HEADLAMP-CR + FILTER-H2O       (backpacking trio, ~110 orders)
# Pattern 5: RAINFLY-XT + TENT-2P-GRN                     (shelter add-on, ~90 orders)

rows = []
order_id = 5000

def make_ts(seed_offset):
    months = ["2024-01-", "2024-02-", "2024-03-", "2024-04-", "2024-05-"]
    m = months[(seed_offset) % len(months)]
    day = (seed_offset % 28) + 1
    return f"{m}{day:02d}"

# Pattern 1 orders
for i in range(180):
    order_id += 1
    ts = make_ts(i)
    basket = ["TENT-2P-GRN", "SLEEP-BAG-20F", "PAD-FOAM-RL"]
    if i % 7 == 0:
        basket.append("RAINFLY-XT")  # occasional add-on
    for sku in basket:
        qty = random.choice([1, 1, 1, 2])
        price = {"TENT-2P-GRN": 189.99, "SLEEP-BAG-20F": 79.99,
                 "PAD-FOAM-RL": 24.99, "RAINFLY-XT": 39.99}.get(sku, 9.99)
        rows.append([order_id, sku, qty, round(price * qty, 2), ts])

# Pattern 2 orders
for i in range(140):
    order_id += 1
    ts = make_ts(i + 200)
    basket = ["BOOT-HK42", "SOCK-WL01", "POLE-ALU-PR"]
    if i % 5 == 0:
        basket.append("HEADLAMP-CR")
    for sku in basket:
        qty = random.choice([1, 1, 2])
        price = {"BOOT-HK42": 139.99, "SOCK-WL01": 14.99,
                 "POLE-ALU-PR": 49.99, "HEADLAMP-CR": 34.99}.get(sku, 9.99)
        rows.append([order_id, sku, qty, round(price * qty, 2), ts])

# Pattern 3 orders
for i in range(160):
    order_id += 1
    ts = make_ts(i + 400)
    basket = ["STOVE-CMP", "FUEL-CANN"]
    if i % 4 == 0:
        basket.append("FILTER-H2O")
    for sku in basket:
        qty = random.choice([1, 1, 1, 3]) if sku == "FUEL-CANN" else 1
        price = {"STOVE-CMP": 54.99, "FUEL-CANN": 9.99,
                 "FILTER-H2O": 29.99}.get(sku, 9.99)
        rows.append([order_id, sku, qty, round(price * qty, 2), ts])

# Pattern 4 orders
for i in range(110):
    order_id += 1
    ts = make_ts(i + 600)
    basket = ["PACK-45L-BK", "HEADLAMP-CR", "FILTER-H2O"]
    for sku in basket:
        qty = 1
        price = {"PACK-45L-BK": 159.99, "HEADLAMP-CR": 34.99,
                 "FILTER-H2O": 29.99}.get(sku, 9.99)
        rows.append([order_id, sku, qty, round(price * qty, 2), ts])

# Single-SKU noise orders (reduce signal-to-noise)
noise_skus = ["PAD-FOAM-RL", "SOCK-WL01", "HEADLAMP-CR", "FUEL-CANN", "RAINFLY-XT"]
for i in range(80):
    order_id += 1
    sku = noise_skus[i % len(noise_skus)]
    ts = make_ts(i + 800)
    rows.append([order_id, sku, 1, 14.99, ts])

# Shuffle rows (not orders)
random.shuffle(rows)

# Write with intentional messiness
out_path = WORKSPACE / "data/raw/orders_export_Q1Q2_2024.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    # Messy header (mixed case, extra spaces)
    writer.writerow(["Order_ID", " line_sku ", "Qty", "Line_Total", "order_date"])
    for idx, row in enumerate(rows):
        # Insert occasional blank rows
        if idx % 97 == 0:
            writer.writerow([])
        # Occasional SKU with leading/trailing space
        if idx % 43 == 0:
            row[1] = " " + str(row[1]) + " "
        # Occasional missing qty (blank)
        if idx % 61 == 0:
            row[2] = ""
        writer.writerow(row)

print(f"Generated {len(rows)} order line rows across {order_id - 5000} orders.")
print("Workspace structure ready.")