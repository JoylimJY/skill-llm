import os
import csv
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "finance/contracts/q1",
    "finance/contracts/q2",
    "finance/contracts/archive",
    "finance/reports/pending",
    "finance/reports/submitted",
    "analytics/scripts",
    "analytics/models",
    "config",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
# Log file
with open(os.path.join(WORKSPACE, "logs", "system.log"), "w") as f:
    f.write("2024-01-15 09:12:34 INFO  Audit pipeline started\n")
    f.write("2024-01-15 09:13:01 WARN  Contract 99001 flagged for review\n")
    f.write("2024-01-15 09:14:55 ERROR Contract 88720 failed validation\n")
    f.write("2024-01-15 09:15:10 INFO  Pipeline completed with 3 warnings\n")

# Old summary JSON (distractor)
with open(os.path.join(WORKSPACE, "finance/reports/submitted", "old_summary_2023.json"), "w") as f:
    json.dump({"year": 2023, "total_contracts": 1204, "flagged": 17, "status": "archived"}, f, indent=2)

# Random CSV distractor
with open(os.path.join(WORKSPACE, "finance/contracts/archive", "legacy_ids.csv"), "w") as f:
    f.write("contract_id,legacy_code,status\n")
    for i in range(8):
        f.write(f"{random.randint(10000,99999)},LC-{random.randint(100,999)},closed\n")

# Python script distractor
with open(os.path.join(WORKSPACE, "analytics/scripts", "old_factor_checker.py"), "w") as f:
    f.write("# Deprecated: use pywayne instead\n")
    f.write("def naive_factors(n):\n")
    f.write("    return [i for i in range(1, n+1) if n % i == 0]\n")
    f.write("# WARNING: This is too slow for large numbers\n")

# Another distractor
with open(os.path.join(WORKSPACE, "analytics/models", "regression_notes.txt"), "w") as f:
    f.write("Model v2 regression: RMSE=0.032, R2=0.991\n")
    f.write("Do not use for contract scoring.\n")

# Config distractor
with open(os.path.join(WORKSPACE, "config", "db_config.yaml"), "w") as f:
    f.write("database:\n  host: localhost\n  port: 5432\n  name: contracts_db\n")

# Q1 distractor
with open(os.path.join(WORKSPACE, "finance/contracts/q1", "q1_notes.txt"), "w") as f:
    f.write("Q1 contracts closed. Pending audit by finance team.\n")

# Q2 distractor
with open(os.path.join(WORKSPACE, "finance/contracts/q2", "q2_notes.txt"), "w") as f:
    f.write("Q2 contracts under review. See contracts.csv for IDs.\n")

# tmp placeholder
with open(os.path.join(WORKSPACE, "tmp", "scratch.txt"), "w") as f:
    f.write("temporary scratch space\n")

# analytics config pointing to pywayne
with open(os.path.join(WORKSPACE, "config", "analytics_config.json"), "w") as f:
    json.dump({
        "math_library": "pywayne",
        "module": "pywayne.maths",
        "functions_required": ["get_all_factors", "digitCount", "karatsuba_multiplication"],
        "description": "All numeric analysis must use pywayne.maths for compliance auditing."
    }, f, indent=2)

# --- THE MAIN PROBLEM FILE ---
# Contracts with known, deliberate factor counts:
# 1260 -> 36 factors (highest)
# 840  -> 32 factors (second highest)
# 720  -> 30 factors
# 900  -> 27 factors
# 504  -> 24 factors
# 360  -> 24 factors
# 630  -> 24 factors
# 660  -> 24 factors
# 756  -> 24 factors
# 600  -> 24 factors (2^3 * 3 * 5^2 => (3+1)(1+1)(2+1)=24)
# 480  -> 24 factors (2^5 * 3 * 5 => (5+1)(1+1)(1+1)=24)
# 420  -> 24 factors (2^2 * 3 * 5 * 7 => (2+1)(1+1)(1+1)(1+1)=24)
# 300  -> 18 factors (2^2 * 3 * 5^2 => (2+1)(1+1)(2+1)=18)
# 210  -> 16 factors
# 100  -> 9  factors

contracts = [
    ("C-1001", 1260, "Q2", "active"),
    ("C-1002", 840,  "Q2", "active"),
    ("C-1003", 720,  "Q1", "active"),
    ("C-1004", 900,  "Q2", "active"),
    ("C-1005", 504,  "Q1", "active"),
    ("C-1006", 360,  "Q1", "active"),
    ("C-1007", 630,  "Q2", "active"),
    ("C-1008", 660,  "Q1", "active"),
    ("C-1009", 756,  "Q2", "active"),
    ("C-1010", 600,  "Q1", "active"),
    ("C-1011", 480,  "Q2", "active"),
    ("C-1012", 420,  "Q1", "active"),
    ("C-1013", 300,  "Q2", "active"),
    ("C-1014", 210,  "Q1", "active"),
    ("C-1015", 100,  "Q2", "active"),
]

with open(os.path.join(WORKSPACE, "finance/contracts/contracts.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["contract_ref", "numeric_id", "quarter", "status"])
    for row in contracts:
        writer.writerow(row)

print("Workspace initialized successfully.")
print(f"Created {WORKSPACE}/finance/contracts/contracts.csv with {len(contracts)} contracts.")