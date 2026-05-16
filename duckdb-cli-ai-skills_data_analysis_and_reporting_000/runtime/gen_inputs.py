#!/usr/bin/env python3
import os
import csv
import json
import random
import struct

# Fixed seed for determinism
random.seed(42)

workspace = "/workspace"

# ---- Create distractor directory structure ----
dirs = [
    "archive/2022/q1",
    "archive/2022/q2",
    "archive/2023/q1",
    "archive/2023/q4",
    "raw_data/incoming",
    "raw_data/processed",
    "reports/drafts",
    "config",
    "scripts",
    "temp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---- Distractor files ----
distractors = [
    ("archive/2022/q1/transactions_q1_2022.csv", "id,amount\n1,100\n2,200\n"),
    ("archive/2022/q2/transactions_q2_2022.csv", "id,amount\n3,150\n4,250\n"),
    ("archive/2023/q1/summary.json", '{"total": 9999, "region": "North"}'),
    ("archive/2023/q4/notes.txt", "End of year reconciliation pending.\nContact finance team.\n"),
    ("raw_data/incoming/upload_manifest.txt", "file1.csv\nfile2.csv\nfile3.parquet\n"),
    ("raw_data/processed/done.log", "2024-01-01 processed: 1000 rows\n2024-01-02 processed: 2000 rows\n"),
    ("reports/drafts/draft_report_v1.md", "# Draft\nThis is a placeholder report.\n"),
    ("config/db_settings.json", '{"host": "localhost", "port": 5432, "db": "retail"}'),
    ("config/etl_config.yaml", "pipeline:\n  source: s3\n  dest: warehouse\n  schedule: daily\n"),
    ("scripts/cleanup.sh", "#!/bin/bash\nrm -f /tmp/scratch_*\n"),
    ("temp/scratch_001.csv", "a,b,c\n1,2,3\n4,5,6\n"),
    ("temp/old_products.json", '[{"id": 999, "name": "Discontinued Widget", "price": 0}]'),
]
for relpath, content in distractors:
    with open(os.path.join(workspace, relpath), "w") as f:
        f.write(content)

# ---- Core input: transactions.csv (messy, with NULLs represented as empty strings) ----
# Columns: order_id, customer_id, product_id, quantity, unit_price, region, order_date
# Some rows have missing region (will be NULL in DuckDB)
transactions = []
regions = ["North", "South", "East", "West", None]
product_ids = [101, 102, 103, 104, 105, 106, 107, 108]

order_id = 1000
for i in range(200):
    cust_id = random.randint(1, 50)
    prod_id = random.choice(product_ids)
    qty = random.randint(1, 10)
    unit_price = round(random.uniform(20.0, 200.0), 2)
    region = random.choice(regions)
    date = f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    transactions.append({
        "order_id": order_id,
        "customer_id": cust_id,
        "product_id": prod_id,
        "quantity": qty,
        "unit_price": unit_price,
        "region": region if region is not None else "",
        "order_date": date,
    })
    order_id += 1

txn_path = os.path.join(workspace, "raw_data/incoming/transactions.csv")
with open(txn_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["order_id","customer_id","product_id","quantity","unit_price","region","order_date"])
    writer.writeheader()
    writer.writerows(transactions)

# ---- Core input: products.parquet (product catalog) ----
import pyarrow as pa
import pyarrow.parquet as pq

product_data = {
    "product_id": [101, 102, 103, 104, 105, 106, 107, 108],
    "product_name": ["Widget Alpha", "Widget Beta", "Gadget Pro", "Gadget Lite", "Doohickey X", "Doohickey Y", "Thingamajig A", "Thingamajig B"],
    "category": ["Widgets", "Widgets", "Gadgets", "Gadgets", "Doohickeys", "Doohickeys", "Thingamajigs", "Thingamajigs"],
    "msrp": [49.99, 79.99, 129.99, 89.99, 39.99, 59.99, 109.99, 149.99],
}
table = pa.table(product_data)
pq.write_table(table, os.path.join(workspace, "raw_data/incoming/products.parquet"))

# ---- Precompute expected values for eval reference ----
# Compute total_amount = quantity * unit_price for each transaction
# Then group by region, compute order_count and total_revenue
# Also identify high_value_orders: total_amount > 500

import collections

region_stats = collections.defaultdict(lambda: {"order_count": 0, "total_revenue": 0.0})
high_value_count = 0

for t in transactions:
    total = t["quantity"] * t["unit_price"]
    region_key = t["region"] if t["region"] != "" else None
    region_stats[region_key]["order_count"] += 1
    region_stats[region_key]["total_revenue"] += total
    if total > 500:
        high_value_count += 1

# Save expected values as a reference JSON (for eval script to use)
# Keys: region -> {order_count, total_revenue}
# Use string "NULL" for None key
ref = {}
for k, v in region_stats.items():
    key_str = k if k is not None else "NULL"
    ref[key_str] = {
        "order_count": v["order_count"],
        "total_revenue": round(v["total_revenue"], 2)
    }
ref["__high_value_count__"] = high_value_count

ref_path = os.path.join(workspace, "config/.eval_reference.json")
with open(ref_path, "w") as f:
    json.dump(ref, f, indent=2)

print("Workspace generated successfully.")
print(f"Transactions: {len(transactions)} rows")
print(f"High-value orders (total > 500): {high_value_count}")
print(f"Regions: {list(region_stats.keys())}")