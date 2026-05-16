import os
import csv
import sqlite3
import hashlib
import random
import shutil
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "data/raw/transactions",
    "data/raw/archive",
    "data/raw/customers",
    "data/processed",
    "data/output",
    "logs",
    "config",
    "scripts",
    "tmp/staging",
    "tmp/scratch",
    "reports/monthly",
    "reports/quarterly",
]
for d in dirs:
    Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "logs/pipeline.log": "2024-01-15 08:00:00 INFO  Pipeline started\n2024-01-15 08:01:00 WARN  Slow query detected\n",
    "config/pipeline.yaml": "pipeline:\n  name: cdp-ingest\n  version: 2\n  schedule: daily\n",
    "config/db_config.ini": "[database]\nhost=localhost\nport=5432\nname=cdp\n",
    "reports/monthly/jan_summary.txt": "Total events: 1,245,033\nUnique customers: 88,201\n",
    "reports/quarterly/q1_kpis.txt": "CAC: $42.10\nLTV: $380.00\nChurn: 3.2%\n",
    "tmp/scratch/temp_merge.csv": "id,value\n1,alpha\n2,beta\n",
    "tmp/staging/stage_note.txt": "Staging area — do not commit\n",
    "data/processed/README_IGNORE.txt": "This folder is for processed outputs only.\n",
    "scripts/run_pipeline.sh": "#!/bin/bash\necho 'pipeline not yet implemented'\n",
    "logs/error.log": "",
    "config/feature_flags.json": '{"enable_fuzzy": false, "strict_mode": true}\n',
    "reports/monthly/feb_summary.txt": "Total events: 1,312,400\nUnique customers: 91,005\n",
}
for rel, content in distractors.items():
    p = Path(WORKSPACE, rel)
    p.write_text(content)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 1 — messy transaction log CSV  (CLI / sort+uniq dedup)
# Agent must deduplicate by transaction_id keeping first occurrence,
# preserve the header, and write to data/output/clean_transactions.csv
# ══════════════════════════════════════════════════════════════════════════════
TRANSACTIONS = [
    ("TXN001", "2024-03-01", "cust_A", "99.99", "USD"),
    ("TXN002", "2024-03-01", "cust_B", "149.50", "USD"),
    ("TXN003", "2024-03-02", "cust_C", "200.00", "EUR"),
    ("TXN004", "2024-03-02", "cust_D", "75.00",  "USD"),
    ("TXN005", "2024-03-03", "cust_E", "310.00", "GBP"),
    ("TXN006", "2024-03-03", "cust_A", "55.00",  "USD"),
    ("TXN007", "2024-03-04", "cust_F", "420.00", "EUR"),
    ("TXN008", "2024-03-04", "cust_G", "18.99",  "USD"),
    ("TXN009", "2024-03-05", "cust_H", "600.00", "USD"),
    ("TXN010", "2024-03-05", "cust_I", "33.33",  "USD"),
]
# Introduce duplicates: some exact, some with trailing whitespace noise
duplicates = [
    ("TXN003", "2024-03-02", "cust_C", "200.00", "EUR"),   # exact dup
    ("TXN001", "2024-03-01", "cust_A", "99.99",  "USD"),   # exact dup
    ("TXN007", "2024-03-04", "cust_F", "420.00", "EUR"),   # exact dup
    ("TXN002", "2024-03-01", "cust_B", "149.50", "USD"),   # exact dup
    ("TXN010", "2024-03-05", "cust_I", "33.33",  "USD"),   # exact dup
]
all_rows = TRANSACTIONS + duplicates
random.shuffle(all_rows)

txn_path = Path(WORKSPACE, "data/raw/transactions/transactions.csv")
with open(txn_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["transaction_id", "date", "customer_id", "amount", "currency"])
    writer.writerows(all_rows)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — file archive with duplicate files (hash-based exact dedup)
# Agent must identify duplicate files by MD5 hash, keep exactly ONE copy of
# each unique file, and write a manifest: data/output/dedup_manifest.txt
# Format per the skill's exact pattern:  <md5hash>  <kept_filepath>
# Duplicated files should NOT appear in the manifest (only unique files listed)
# ══════════════════════════════════════════════════════════════════════════════
file_contents = {
    "invoice_2024_001.pdf.txt":  "INVOICE#001 | Amount: $500 | Date: 2024-01-10",
    "invoice_2024_002.pdf.txt":  "INVOICE#002 | Amount: $750 | Date: 2024-01-15",
    "invoice_2024_003.pdf.txt":  "INVOICE#003 | Amount: $200 | Date: 2024-01-20",
    "receipt_march_A.txt":       "RECEIPT-A | Store: XYZ | Total: $99",
    "receipt_march_B.txt":       "RECEIPT-B | Store: ABC | Total: $145",
    "contract_v1.txt":           "CONTRACT v1 | Client: ACME | Signed: 2024-02-01",
    "contract_v2.txt":           "CONTRACT v1 | Client: ACME | Signed: 2024-02-01",  # same content as v1
    "report_final.txt":          "REPORT | Q1 2024 | Revenue: $1.2M",
    "report_final_copy.txt":     "REPORT | Q1 2024 | Revenue: $1.2M",               # same as report_final
    "terms_conditions.txt":      "TERMS AND CONDITIONS v3.1 | Effective: 2024-01-01",
    "terms_backup.txt":          "TERMS AND CONDITIONS v3.1 | Effective: 2024-01-01",# same
    "unique_asset.txt":          "UNIQUE ASSET | ID: UA-9900 | Value: $9,999",
}
archive_dir = Path(WORKSPACE, "data/raw/archive")
for fname, content in file_contents.items():
    (archive_dir / fname).write_text(content)

# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — customer SQLite database (SQL ROW_NUMBER dedup)
# Table: customers (id INTEGER PK, customer_id TEXT, name TEXT, email TEXT,
#                   created_at TEXT, is_active INTEGER)
# Duplicates: same customer_id, different id; keep the row with the lowest id
# Agent must write a new clean table or query result to:
#   data/output/clean_customers.db  (table: customers_clean)
# ══════════════════════════════════════════════════════════════════════════════
db_path = Path(WORKSPACE, "data/raw/customers/customers.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS customers")
cur.execute("""
    CREATE TABLE customers (
        id          INTEGER PRIMARY KEY,
        customer_id TEXT,
        name        TEXT,
        email       TEXT,
        created_at  TEXT,
        is_active   INTEGER
    )
""")

base_customers = [
    ("cust_A", "Alice Martin",   "alice@example.com",  "2023-06-01", 1),
    ("cust_B", "Bob Torres",     "bob@example.com",    "2023-06-15", 1),
    ("cust_C", "Carol Nguyen",   "carol@example.com",  "2023-07-01", 0),
    ("cust_D", "David Kim",      "david@example.com",  "2023-07-10", 1),
    ("cust_E", "Eva Rossi",      "eva@example.com",    "2023-08-01", 1),
    ("cust_F", "Frank Müller",   "frank@example.com",  "2023-08-20", 1),
    ("cust_G", "Grace Li",       "grace@example.com",  "2023-09-01", 0),
    ("cust_H", "Hideo Tanaka",   "hideo@example.com",  "2023-09-15", 1),
    ("cust_I", "Irene Dubois",   "irene@example.com",  "2023-10-01", 1),
    ("cust_J", "James O'Brien",  "james@example.com",  "2023-10-10", 1),
]
# Some records will be duplicated (same customer_id, later id, possibly different email)
dup_customers = [
    ("cust_A", "Alice Martin",   "alice_new@example.com", "2024-01-05", 1),
    ("cust_C", "Carol Nguyen",   "carol@example.com",     "2024-01-06", 1),
    ("cust_F", "Frank Muller",   "frank@example.com",     "2024-02-01", 0),
    ("cust_I", "Irene Dubois",   "irene2@example.com",    "2024-02-10", 1),
]
all_customers = base_customers + dup_customers
# Assign IDs in shuffled order to make the "lowest id = first ingested" logic non-trivial
shuffled_idx = list(range(len(all_customers)))
random.shuffle(shuffled_idx)
rows_with_id = [(shuffled_idx[i]+1,) + all_customers[i] for i in range(len(all_customers))]
rows_with_id.sort(key=lambda r: r[0])

cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", rows_with_id)
conn.commit()
conn.close()

print("Workspace generated successfully.")
print(f"  Transactions CSV : {txn_path}")
print(f"  Archive dir      : {archive_dir}")
print(f"  Customers DB     : {db_path}")