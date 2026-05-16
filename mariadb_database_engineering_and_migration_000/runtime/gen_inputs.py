import os
import json
import csv
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic distractor directory structure ---
dirs = [
    "legacy_reports/2022/Q1",
    "legacy_reports/2022/Q2",
    "legacy_reports/2023/Q3",
    "archive/old_scripts",
    "archive/backups",
    "config/db",
    "config/app",
    "etl/transforms",
    "etl/loaders",
    "docs/schema",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "legacy_reports/2022/Q1/summary.txt": "Old Q1 2022 report. No longer maintained.",
    "legacy_reports/2022/Q2/prices.csv": "drug_id,price\n1,10.5\n2,8.2\n3,15.0",
    "legacy_reports/2023/Q3/inventory.txt": "Manual count: 200 units aspirin, 50 units ibuprofen",
    "archive/old_scripts/migrate_v1.sql": "-- Old migration, do not use\nDROP TABLE IF EXISTS old_inventory;",
    "archive/old_scripts/seed_data.py": "# Deprecated seeder\nprint('deprecated')",
    "archive/backups/dump_2023.sql.gz.info": "Backup taken 2023-12-01, size: 4.2GB",
    "config/db/old_connection.ini": "[database]\nhost=10.0.0.1\nport=3306\nuser=root\npassword=REDACTED",
    "config/app/feature_flags.json": json.dumps({"enable_audit": False, "use_sequences": False}),
    "etl/transforms/normalize_prices.py": "# Placeholder for price normalization transform\npass",
    "etl/loaders/bulk_loader.sh": "#!/bin/bash\necho 'Bulk loader not configured'",
    "docs/schema/erd_v2.txt": "ERD: drug_batches -> branch_sales -> pharmacy_branches",
    "docs/schema/deprecated_schema.sql": """
CREATE TABLE old_drug_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_name VARCHAR(100),
    price DECIMAL(10,2),
    branch_id INT
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
""",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- The messy raw input: pharmacy inventory CSV (wrong charset hints, no audit, plain IDs) ---
# This represents the "legacy data" the agent needs to migrate into a proper schema

branches = [
    (1, "Alpha Pharmacy", "New York"),
    (2, "Beta Pharmacy", "Los Ángeles"),   # intentional accent
    (3, "Gamma Pharmacy", "São Paulo"),    # intentional special chars
    (4, "Delta Pharmacy", "München"),      # intentional umlaut
]

drugs = [
    ("Aspirin 100mg",   "aspirin",   "10.50", '{"dosage_mg": 100, "form": "tablet"}'),
    ("Ibuprofen 400mg", "ibuprofen", "8.20",  '{"dosage_mg": 400, "form": "capsule"}'),
    ("Amoxicillin 500mg","amoxicillin","15.00",'{"dosage_mg": 500, "form": "capsule"}'),
    ("Metformin 850mg", "metformin", "5.75",  '{"dosage_mg": 850, "form": "tablet"}'),
    ("Atorvastatin 20mg","atorvastatin","22.30",'{"dosage_mg": 20, "form": "tablet"}'),
]

# Raw inventory CSV
inventory_rows = []
batch_id = 1000
for b_id, b_name, b_city in branches:
    for d_name, d_slug, d_price, d_meta in drugs:
        inventory_rows.append({
            "batch_ref": f"BATCH-{batch_id}",
            "drug_name": d_name,
            "branch_id": b_id,
            "branch_name": b_name,
            "unit_price": d_price,
            "metadata_json": d_meta,
            "stock_qty": random.randint(50, 300),
        })
        batch_id += 1

csv_path = os.path.join(workspace, "raw_inventory.csv")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["batch_ref","drug_name","branch_id","branch_name","unit_price","metadata_json","stock_qty"])
    writer.writeheader()
    writer.writerows(inventory_rows)

# Sales data CSV (for running totals window function)
sales_rows = []
sale_id = 1
for b_id, b_name, b_city in branches:
    for d_name, d_slug, d_price, d_meta in drugs:
        qty_sold = random.randint(5, 40)
        sales_rows.append({
            "sale_id": sale_id,
            "branch_id": b_id,
            "drug_slug": d_slug,
            "qty_sold": qty_sold,
            "sale_amount": round(float(d_price) * qty_sold, 2),
            "sale_date": f"2024-0{random.randint(1,6)}-{random.randint(1,28):02d}",
        })
        sale_id += 1

sales_csv_path = os.path.join(workspace, "raw_sales.csv")
with open(sales_csv_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["sale_id","branch_id","drug_slug","qty_sold","sale_amount","sale_date"])
    writer.writeheader()
    writer.writerows(sales_rows)

# Price update log: these are the NEW prices after a "price revision" event
# Agent needs to update drug_batches to these prices AFTER initial insert
# so that the temporal history shows both old and new prices
price_updates = {
    "Aspirin 100mg":    "12.00",
    "Ibuprofen 400mg":  "9.50",
    "Amoxicillin 500mg":"17.50",
    "Metformin 850mg":  "6.25",
    "Atorvastatin 20mg":"25.00",
}

import json as _json
with open(os.path.join(workspace, "price_revision.json"), "w") as f:
    _json.dump(price_updates, f, indent=2)

# Task specification file (business requirements — no technical hints)
task_spec = """PHARMACY INVENTORY SYSTEM — MIGRATION TASK SPEC
================================================

Context:
Our pharmacy chain operates across 4 branches and manages a catalog of drugs.
We are migrating from a legacy flat-file system to a proper relational database.

Requirements from the business:
1. BATCH ID GENERATION: Drug batch IDs must be generated from a centralized
   counter that never reuses numbers, even if a transaction is rolled back.
   Source data is in raw_inventory.csv.

2. PRICE HISTORY AUDIT: Regulators require us to query the exact price of any
   drug batch AS IT WAS at any past timestamp. After loading the initial data,
   apply the price revisions from price_revision.json, so two versions exist.

3. SALES RUNNING TOTAL REPORT: For each branch, produce a running cumulative
   sales amount ordered by sale_date. Source data is in raw_sales.csv.

4. DOSAGE EXTRACTION: Produce a report extracting the numeric dosage value
   from the metadata stored alongside each drug batch.

5. UNICODE: Branch names and drug names include accented characters and emoji
   reactions may be added in future. Ensure full Unicode support end-to-end.

Output files required:
- historical_prices.tsv   : batch_ref, drug_name, branch_id, old_price (before revision)
- running_totals.tsv      : branch_id, drug_slug, sale_date, sale_amount, running_total
- dosage_report.tsv       : batch_ref, drug_name, dosage_mg
"""

with open(os.path.join(workspace, "TASK_SPEC.txt"), "w") as f:
    f.write(task_spec)

print("Workspace generated successfully.")
print(f"Files created: raw_inventory.csv, raw_sales.csv, price_revision.json, TASK_SPEC.txt")
print(f"Distractor files: {len(distractor_files)}")