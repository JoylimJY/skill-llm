import os
import json
import random

random.seed(42)

BASE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "data/raw/sales/2024-01",
    "data/raw/sales/2024-02",
    "data/raw/sales/2024-03",
    "data/raw/metadata",
    "data/raw/configs/service_a",
    "data/raw/configs/service_b",
    "data/raw/configs/service_c",
    "data/processed",
    "logs",
    "archive/old_sales",
    "archive/old_configs",
    "tmp",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- DISTRACTOR FILES ---
# Old archive sales (different schema, should NOT be merged)
with open(os.path.join(BASE, "archive/old_sales/legacy_2023.csv"), "w") as f:
    f.write("transaction_id,amount,date\n")
    f.write("T001,99.99,2023-05-01\n")
    f.write("T002,149.50,2023-06-15\n")

# A partial JSON that looks like a config but is in archive (should NOT be merged)
with open(os.path.join(BASE, "archive/old_configs/deprecated.json"), "w") as f:
    json.dump({"version": "0.9", "deprecated": True, "timeout": 5000}, f, indent=2)

# Log files (distractors)
for i in range(1, 4):
    with open(os.path.join(BASE, f"logs/pipeline_{i}.log"), "w") as f:
        f.write(f"[INFO] Pipeline {i} started\n[INFO] Pipeline {i} completed\n")

# Temp/misc files
with open(os.path.join(BASE, "tmp/scratch.txt"), "w") as f:
    f.write("temporary notes\ndo not use\n")

with open(os.path.join(BASE, "scripts/old_merge.sh"), "w") as f:
    f.write("#!/bin/bash\n# deprecated script\necho 'do not run'\n")

# README-like but misleading (no hints)
with open(os.path.join(BASE, "data/raw/ABOUT.txt"), "w") as f:
    f.write("Raw data storage. Files may be incomplete. Contact data-eng@company.internal.\n")

# --- ACTUAL TASK INPUTS ---

# 1. Three CSV sales shards (same schema, each has a header)
sales_header = "id,product,region_id,units_sold,revenue\n"

sales_jan = [
    ("S001", "Widget-A", "R01", 120, 2400.00),
    ("S002", "Widget-B", "R02", 85, 1700.00),
    ("S003", "Gadget-X", "R01", 60, 3600.00),
]
sales_feb = [
    ("S004", "Widget-A", "R03", 200, 4000.00),
    ("S005", "Gadget-Y", "R02", 45, 5400.00),
]
sales_mar = [
    ("S006", "Widget-B", "R01", 310, 6200.00),
    ("S007", "Gadget-X", "R03", 75, 4500.00),
    ("S008", "Widget-A", "R02", 95, 1900.00),
]

def write_csv(path, header, rows):
    with open(path, "w") as f:
        f.write(header)
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")

write_csv(os.path.join(BASE, "data/raw/sales/2024-01/sales_jan.csv"), sales_header, sales_jan)
write_csv(os.path.join(BASE, "data/raw/sales/2024-02/sales_feb.csv"), sales_header, sales_feb)
write_csv(os.path.join(BASE, "data/raw/sales/2024-03/sales_mar.csv"), sales_header, sales_mar)

# 2. Region metadata lookup CSV (for join on region_id)
region_header = "region_id,region_name,country,sales_manager\n"
regions = [
    ("R01", "North-East", "USA", "Alice Chen"),
    ("R02", "West-Coast", "USA", "Bob Martinez"),
    ("R03", "South-Central", "USA", "Carol White"),
]
write_csv(os.path.join(BASE, "data/raw/metadata/regions.csv"), region_header, regions)

# Also put a distractor metadata file
with open(os.path.join(BASE, "data/raw/metadata/product_categories.csv"), "w") as f:
    f.write("product,category,launch_year\n")
    f.write("Widget-A,Consumer Electronics,2021\n")
    f.write("Widget-B,Consumer Electronics,2022\n")
    f.write("Gadget-X,Smart Home,2020\n")
    f.write("Gadget-Y,Smart Home,2023\n")

# 3. Three JSON config fragments (for deep merge)
# service_a: base config with nested settings
config_a = {
    "service_name": "analytics-pipeline",
    "version": "2.1.0",
    "database": {
        "host": "db-primary.internal",
        "port": 5432,
        "pool_size": 10
    },
    "features": {
        "caching": False,
        "retries": 3
    }
}
# service_b: overrides some nested keys, adds new ones
config_b = {
    "version": "2.1.0",
    "database": {
        "port": 5433,
        "name": "analytics_db"
    },
    "features": {
        "caching": True,
        "rate_limiting": True
    },
    "logging": {
        "level": "INFO",
        "format": "json"
    }
}
# service_c: adds more top-level and nested keys
config_c = {
    "deployment": {
        "region": "us-east-1",
        "replicas": 3
    },
    "features": {
        "metrics": True
    },
    "logging": {
        "destination": "cloudwatch"
    }
}

def write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

write_json(os.path.join(BASE, "data/raw/configs/service_a/config.json"), config_a)
write_json(os.path.join(BASE, "data/raw/configs/service_b/config.json"), config_b)
write_json(os.path.join(BASE, "data/raw/configs/service_c/config.json"), config_c)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for fname in files:
        print(" ", os.path.join(root, fname))