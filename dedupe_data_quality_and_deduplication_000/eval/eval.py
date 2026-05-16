import sys
import os
import csv
import sqlite3
import hashlib
import json
from pathlib import Path

workspace = sys.argv[1]

checks = []
score_total = 0.0
max_checks = 3  # one per task

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 1 — clean_transactions.csv
# Expect: header row + exactly 10 unique transaction_id rows, first-occurrence kept
# ══════════════════════════════════════════════════════════════════════════════
EXPECTED_TXNS = {
    "TXN001","TXN002","TXN003","TXN004","TXN005",
    "TXN006","TXN007","TXN008","TXN009","TXN010",
}
try:
    candidates = list(Path(workspace).rglob("clean_transactions.csv"))
    if not candidates:
        raise FileNotFoundError("clean_transactions.csv not found")
    txn_file = candidates[0]
    with open(txn_file, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    ids_found = [r["transaction_id"].strip() for r in rows]
    ids_set = set(ids_found)

    if ids_set != EXPECTED_TXNS:
        missing = EXPECTED_TXNS - ids_set
        extra   = ids_set - EXPECTED_TXNS
        detail  = f"Expected 10 unique TXN IDs. Missing={missing}, Extra={extra}"
        checks.append(make_check("clean_transactions_csv", False, detail))
    elif len(ids_found) != 10:
        checks.append(make_check("clean_transactions_csv", False,
            f"Duplicate rows still present; got {len(ids_found)} rows, expected 10"))
    else:
        checks.append(make_check("clean_transactions_csv", True,
            f"All 10 unique transaction IDs present, no duplicates. File: {txn_file}"))
        score_total += 1
except Exception as e:
    checks.append(make_check("clean_transactions_csv", False, f"Exception: {e}"))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 2 — dedup_manifest.txt
# Expect: exactly 8 unique files kept (12 files, 4 pairs of duplicates → 8 unique)
# Each line: <md5hash>  <filepath>
# The MD5 hashes must actually match the file contents in the archive.
# ══════════════════════════════════════════════════════════════════════════════
ARCHIVE_DIR = Path(workspace) / "data" / "raw" / "archive"

def md5_of_file(p):
    h = hashlib.md5()
    h.update(Path(p).read_bytes())
    return h.hexdigest()

# Build ground truth: unique content groups
try:
    archive_files = list(ARCHIVE_DIR.iterdir()) if ARCHIVE_DIR.exists() else []
    content_to_files = {}
    for f in archive_files:
        h = md5_of_file(f)
        content_to_files.setdefault(h, []).append(f)
    expected_unique_hashes = set(content_to_files.keys())  # should be 8

    candidates = list(Path(workspace).rglob("dedup_manifest.txt"))
    if not candidates:
        raise FileNotFoundError("dedup_manifest.txt not found")
    manifest_path = candidates[0]
    manifest_lines = [l.strip() for l in manifest_path.read_text().splitlines() if l.strip()]

    manifest_hashes = set()
    hash_errors = []
    for line in manifest_lines:
        parts = line.split()
        if len(parts) < 2:
            hash_errors.append(f"Malformed line: {line!r}")
            continue
        reported_hash = parts[0]
        manifest_hashes.add(reported_hash)
        # Verify hash matches a real file in the archive
        if reported_hash not in expected_unique_hashes:
            hash_errors.append(f"Hash {reported_hash} not found among archive unique hashes")

    if hash_errors:
        checks.append(make_check("dedup_manifest_txt", False,
            f"Hash errors: {hash_errors[:3]}"))
    elif manifest_hashes != expected_unique_hashes:
        missing = expected_unique_hashes - manifest_hashes
        extra   = manifest_hashes - expected_unique_hashes
        checks.append(make_check("dedup_manifest_txt", False,
            f"Wrong set of hashes. Missing={len(missing)}, Extra={len(extra)}. "
            f"Expected {len(expected_unique_hashes)} unique hashes, got {len(manifest_hashes)}"))
    elif len(manifest_lines) != len(expected_unique_hashes):
        checks.append(make_check("dedup_manifest_txt", False,
            f"Line count mismatch: {len(manifest_lines)} lines, expected {len(expected_unique_hashes)}"))
    else:
        checks.append(make_check("dedup_manifest_txt", True,
            f"Manifest lists all {len(expected_unique_hashes)} unique files with correct MD5 hashes."))
        score_total += 1
except Exception as e:
    checks.append(make_check("dedup_manifest_txt", False, f"Exception: {e}"))

# ══════════════════════════════════════════════════════════════════════════════
# CHECK 3 — clean_customers.db  (table: customers_clean)
# Expect: 10 unique customer_id rows, each with the LOWEST id value among duplicates
# ══════════════════════════════════════════════════════════════════════════════
SOURCE_DB = Path(workspace) / "data" / "raw" / "customers" / "customers.db"

try:
    # Compute ground truth from source DB
    src_conn = sqlite3.connect(str(SOURCE_DB))
    src_cur  = src_conn.cursor()
    src_cur.execute("""
        SELECT customer_id, MIN(id) as min_id
        FROM customers
        GROUP BY customer_id
        ORDER BY customer_id
    """)
    expected = {row[0]: row[1] for row in src_cur.fetchall()}
    src_conn.close()

    candidates = list(Path(workspace).rglob("clean_customers.db"))
    if not candidates:
        raise FileNotFoundError("clean_customers.db not found")
    clean_db = candidates[0]
    out_conn = sqlite3.connect(str(clean_db))
    out_cur  = out_conn.cursor()

    # Table must be named customers_clean
    out_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers_clean'")
    if not out_cur.fetchone():
        raise ValueError("Table 'customers_clean' not found in clean_customers.db")

    out_cur.execute("SELECT customer_id, id FROM customers_clean ORDER BY customer_id")
    result_rows = out_cur.fetchall()
    out_conn.close()

    result = {row[0]: row[1] for row in result_rows}

    if set(result.keys()) != set(expected.keys()):
        missing = set(expected.keys()) - set(result.keys())
        extra   = set(result.keys()) - set(expected.keys())
        checks.append(make_check("clean_customers_db", False,
            f"customer_id set mismatch. Missing={missing}, Extra={extra}"))
    else:
        wrong = {cid: (result[cid], expected[cid])
                 for cid in expected if result[cid] != expected[cid]}
        if wrong:
            checks.append(make_check("clean_customers_db", False,
                f"Wrong id kept for some customers (got_id, expected_min_id): {wrong}"))
        else:
            checks.append(make_check("clean_customers_db", True,
                f"All {len(expected)} customers present with correct (lowest) id kept."))
            score_total += 1
except Exception as e:
    checks.append(make_check("clean_customers_db", False, f"Exception: {e}"))

# ══════════════════════════════════════════════════════════════════════════════
# Final result
# ══════════════════════════════════════════════════════════════════════════════
final_score = round(score_total / max_checks, 4)
result = {
    "passed": score_total == max_checks,
    "score":  final_score,
    "checks": checks,
}
print(json.dumps(result, indent=2))