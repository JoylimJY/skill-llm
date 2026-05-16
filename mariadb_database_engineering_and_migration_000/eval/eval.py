import sys
import json
import subprocess
import os
from pathlib import Path

try:
    import pymysql
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "pymysql",
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"], check=True)
    import pymysql

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def get_conn():
    return pymysql.connect(
        host="127.0.0.1", port=3306,
        user="pharma_agent", password="agent_pass_2024",
        database="pharmacy",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

# ──────────────────────────────────────────────
# CHECK 1: Sequence exists (not AUTO_INCREMENT)
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SHOW CREATE SEQUENCE batch_id_seq;")
    row = cur.fetchone()
    conn.close()
    if row:
        add_check("sequence_exists", True,
                  "Sequence 'batch_id_seq' exists in the database.")
    else:
        add_check("sequence_exists", False,
                  "Sequence 'batch_id_seq' not found.")
except Exception as e:
    add_check("sequence_exists", False, f"Could not verify sequence: {e}")

# ──────────────────────────────────────────────
# CHECK 2: drug_batches table uses utf8mb4 + unicode_ci collation
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TABLE_COLLATION
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'pharmacy'
          AND TABLE_NAME = 'drug_batches';
    """)
    row = cur.fetchone()
    conn.close()
    if row:
        collation = row["TABLE_COLLATION"] or ""
        passed = "utf8mb4" in collation and "unicode" in collation.lower()
        add_check("table_charset_utf8mb4_unicode",
                  passed,
                  f"drug_batches collation is '{collation}' (need utf8mb4_unicode_ci)")
    else:
        add_check("table_charset_utf8mb4_unicode", False,
                  "Table 'drug_batches' not found in information_schema.")
except Exception as e:
    add_check("table_charset_utf8mb4_unicode", False, f"Error: {e}")

# ──────────────────────────────────────────────
# CHECK 3: drug_batches has SYSTEM VERSIONING enabled
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT CREATE_OPTIONS
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = 'pharmacy'
          AND TABLE_NAME = 'drug_batches';
    """)
    row = cur.fetchone()
    conn.close()
    if row:
        opts = (row.get("CREATE_OPTIONS") or "").lower()
        passed = "with system versioning" in opts or "system_versioning" in opts
        # Also try SHOW CREATE TABLE as fallback
        if not passed:
            conn2 = get_conn()
            cur2 = conn2.cursor()
            cur2.execute("SHOW CREATE TABLE drug_batches;")
            create_row = cur2.fetchone()
            conn2.close()
            ddl = str(create_row).lower() if create_row else ""
            passed = "system versioning" in ddl or "with system versioning" in ddl
        add_check("system_versioning_enabled", passed,
                  f"CREATE_OPTIONS='{opts}'; System versioning {'detected' if passed else 'NOT detected'}")
    else:
        add_check("system_versioning_enabled", False,
                  "Table 'drug_batches' not found.")
except Exception as e:
    add_check("system_versioning_enabled", False, f"Error: {e}")

# ──────────────────────────────────────────────
# CHECK 4: drug_batches IDs come from sequence (no AUTO_INCREMENT in table DDL)
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SHOW CREATE TABLE drug_batches;")
    row = cur.fetchone()
    conn.close()
    ddl_str = str(row).lower() if row else ""
    # Should NOT have auto_increment as column default
    has_auto_inc = "auto_increment" in ddl_str
    # Check that there IS data with valid integer IDs
    conn2 = get_conn()
    cur2 = conn2.cursor()
    cur2.execute("SELECT COUNT(*) as cnt FROM drug_batches;")
    cnt_row = cur2.fetchone()
    conn2.close()
    row_count = cnt_row["cnt"] if cnt_row else 0
    # We want rows loaded AND no auto_increment (sequence used instead)
    passed = (not has_auto_inc) and (row_count >= 20)
    add_check("sequence_used_for_ids",
              passed,
              f"auto_increment in DDL: {has_auto_inc}, row_count: {row_count} (need >=20, no auto_increment)")
except Exception as e:
    add_check("sequence_used_for_ids", False, f"Error: {e}")

# ──────────────────────────────────────────────
# CHECK 5: Price updates were applied (two distinct prices exist or existed)
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    # Check current prices match revised values
    cur.execute("""
        SELECT drug_name, unit_price
        FROM drug_batches
        WHERE drug_name = 'Aspirin 100mg'
        LIMIT 1;
    """)
    row = cur.fetchone()
    conn.close()
    if row:
        price = float(row["unit_price"])
        # After revision, Aspirin should be 12.00
        passed = abs(price - 12.00) < 0.01
        add_check("price_revision_applied", passed,
                  f"Aspirin current price={price}, expected 12.00 after revision")
    else:
        add_check("price_revision_applied", False,
                  "No 'Aspirin 100mg' rows found in drug_batches.")
except Exception as e:
    add_check("price_revision_applied", False, f"Error: {e}")

# ──────────────────────────────────────────────
# CHECK 6: historical_prices.tsv exists and contains old prices via temporal query
# ──────────────────────────────────────────────
try:
    tsv_files = list(Path(workspace).rglob("historical_prices.tsv"))
    if not tsv_files:
        add_check("historical_prices_file", False,
                  "historical_prices.tsv not found anywhere in workspace.")
    else:
        tsv_path = tsv_files[0]
        with open(tsv_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        lines = [l for l in content.split("\n") if l.strip()]
        # Should have header + at least 20 data rows
        data_lines = [l for l in lines if not l.lower().startswith("batch_ref")]
        # Check that old Aspirin price (10.50) appears somewhere
        aspirin_old = any("10.5" in l or "10.50" in l for l in lines)
        has_enough = len(data_lines) >= 20
        passed = aspirin_old and has_enough
        add_check("historical_prices_file", passed,
                  f"Rows={len(data_lines)}, old_aspirin_price_present={aspirin_old}")
except Exception as e:
    add_check("historical_prices_file", False, f"Error reading file: {e}")

# ──────────────────────────────────────────────
# CHECK 7: running_totals.tsv exists and has correct window function output
# ──────────────────────────────────────────────
try:
    tsv_files = list(Path(workspace).rglob("running_totals.tsv"))
    if not tsv_files:
        add_check("running_totals_file", False,
                  "running_totals.tsv not found anywhere in workspace.")
    else:
        tsv_path = tsv_files[0]
        with open(tsv_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        lines = [l for l in content.split("\n") if l.strip()]
        data_lines = [l for l in lines if not l.lower().startswith("branch_id")]

        # Must have at least 20 rows (4 branches × 5 drugs)
        has_enough = len(data_lines) >= 20

        # Verify running total logic: for each branch, the running_total column
        # must be non-decreasing (it's a cumulative sum)
        from collections import defaultdict
        branch_totals = defaultdict(list)
        col_error = False
        for line in data_lines:
            parts = line.split("\t")
            if len(parts) < 5:
                col_error = True
                break
            try:
                b_id = parts[0]
                running_total = float(parts[4])
                branch_totals[b_id].append(running_total)
            except (ValueError, IndexError):
                col_error = True

        non_decreasing = True
        for b_id, totals in branch_totals.items():
            for i in range(1, len(totals)):
                if totals[i] < totals[i-1] - 0.01:
                    non_decreasing = False
                    break

        passed = has_enough and not col_error and non_decreasing
        add_check("running_totals_file", passed,
                  f"Rows={len(data_lines)}, col_error={col_error}, non_decreasing={non_decreasing}")
except Exception as e:
    add_check("running_totals_file", False, f"Error reading file: {e}")

# ──────────────────────────────────────────────
# CHECK 8: dosage_report.tsv exists and uses JSON_VALUE extraction
# ──────────────────────────────────────────────
try:
    tsv_files = list(Path(workspace).rglob("dosage_report.tsv"))
    if not tsv_files:
        add_check("dosage_report_file", False,
                  "dosage_report.tsv not found anywhere in workspace.")
    else:
        tsv_path = tsv_files[0]
        with open(tsv_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        lines = [l for l in content.split("\n") if l.strip()]
        data_lines = [l for l in lines if not (
            l.lower().startswith("batch_ref") or
            l.lower().startswith("id") or
            l.lower().startswith("drug_name")
        )]

        has_enough = len(data_lines) >= 20

        # Check known dosage values: Aspirin=100, Ibuprofen=400, Amoxicillin=500
        has_100 = any("100" in l for l in data_lines)
        has_400 = any("400" in l for l in data_lines)
        has_500 = any("500" in l for l in data_lines)

        passed = has_enough and has_100 and has_400 and has_500
        add_check("dosage_report_file", passed,
                  f"Rows={len(data_lines)}, has_100mg={has_100}, has_400mg={has_400}, has_500mg={has_500}")
except Exception as e:
    add_check("dosage_report_file", False, f"Error reading file: {e}")

# ──────────────────────────────────────────────
# CHECK 9: Composite covering index exists on branch_sales or related table
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX, COLUMN_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = 'pharmacy'
        ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;
    """)
    rows = cur.fetchall()
    conn.close()

    # Find any composite index (SEQ_IN_INDEX > 1 exists for same index)
    from collections import defaultdict
    index_cols = defaultdict(list)
    for r in rows:
        key = (r["TABLE_NAME"], r["INDEX_NAME"])
        index_cols[key].append(r["COLUMN_NAME"])

    composite_indexes = {k: v for k, v in index_cols.items() if len(v) >= 2}
    has_composite = len(composite_indexes) > 0

    # Also check that at least one index covers branch_id + sale_date or similar
    relevant = any(
        any(c in ["branch_id", "sale_date", "drug_slug"] for c in cols)
        for cols in composite_indexes.values()
    )

    passed = has_composite and relevant
    add_check("composite_covering_index", passed,
              f"Composite indexes found: {dict(composite_indexes)}, relevant={relevant}")
except Exception as e:
    add_check("composite_covering_index", False, f"Error: {e}")

# ──────────────────────────────────────────────
# CHECK 10: Unicode data integrity — accented branch names stored correctly
# ──────────────────────────────────────────────
try:
    conn = get_conn()
    cur = conn.cursor()
    # Look for accented chars in any table
    cur.execute("SHOW TABLES;")
    tables = [list(r.values())[0] for r in cur.fetchall()]
    conn.close()

    found_unicode = False
    for tbl in tables:
        try:
            conn2 = get_conn()
            cur2 = conn2.cursor()
            cur2.execute(f"SELECT * FROM `{tbl}` LIMIT 100;")
            rows2 = cur2.fetchall()
            conn2.close()
            for row2 in rows2:
                for val in row2.values():
                    if val and isinstance(val, str):
                        # Check for accented chars
                        if any(ord(c) > 127 for c in val):
                            found_unicode = True
                            break
        except Exception:
            pass
        if found_unicode:
            break

    add_check("unicode_data_integrity", found_unicode,
              f"Accented/unicode characters {'found' if found_unicode else 'NOT found'} in database tables")
except Exception as e:
    add_check("unicode_data_integrity", False, f"Error: {e}")

# ──────────────────────────────────────────────
# Final scoring
# ──────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

result = {
    "passed": passed_count >= 8,  # Must pass at least 8/10
    "score": score,
    "checks": checks
}

print("\n=== EVALUATION RESULT ===")
print(json.dumps(result, indent=2))