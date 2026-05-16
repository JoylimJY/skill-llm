#!/usr/bin/env python3
import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
checks = []
passed_all = True

def fail(name, detail):
    checks.append({"name": name, "passed": False, "detail": detail})
    return False

def ok(name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})
    return True

# Load reference data
ref_path = os.path.join(workspace, "config/.eval_reference.json")
try:
    with open(ref_path) as f:
        ref = json.load(f)
    high_value_expected = ref.pop("__high_value_count__")
except Exception as e:
    fail("load_reference", f"Could not load eval reference: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ─────────────────────────────────────────────
# CHECK 1: regional_summary.md exists
# ─────────────────────────────────────────────
md_files = list(Path(workspace).rglob("regional_summary.md"))
if not md_files:
    fail("regional_summary_exists", "File 'regional_summary.md' not found anywhere in workspace.")
    passed_all = False
    md_content = None
else:
    md_path = md_files[0]
    ok("regional_summary_exists", f"Found at {md_path}")
    try:
        md_content = md_path.read_text()
    except Exception as e:
        fail("regional_summary_readable", f"Could not read file: {e}")
        passed_all = False
        md_content = None

# ─────────────────────────────────────────────
# CHECK 2: regional_summary.md is a Markdown table (contains pipe-delimited rows)
# ─────────────────────────────────────────────
if md_content is not None:
    lines = [l.strip() for l in md_content.strip().splitlines() if l.strip()]
    pipe_lines = [l for l in lines if l.startswith("|") and l.endswith("|")]
    if len(pipe_lines) < 3:
        fail("markdown_table_format", f"Expected Markdown table with pipe-delimited rows, got {len(pipe_lines)} pipe lines. Content snippet: {md_content[:300]}")
        passed_all = False
    else:
        ok("markdown_table_format", f"Markdown table detected with {len(pipe_lines)} pipe-delimited rows.")
else:
    fail("markdown_table_format", "Skipped: file not readable.")
    passed_all = False

# ─────────────────────────────────────────────
# CHECK 3: NULL values shown as "N/A" in the markdown report
# ─────────────────────────────────────────────
if md_content is not None:
    # The NULL region rows should appear as N/A (not empty, not "null", not "NULL")
    if "N/A" in md_content:
        ok("null_as_na", "Found 'N/A' representation for NULL values in markdown report.")
    else:
        fail("null_as_na", f"Expected NULL region to be shown as 'N/A' in markdown. Did not find 'N/A'. Content snippet: {md_content[:500]}")
        passed_all = False
else:
    fail("null_as_na", "Skipped: file not readable.")
    passed_all = False

# ─────────────────────────────────────────────
# CHECK 4: Markdown table has correct columns (region, order_count/orders, total_revenue/revenue)
# ─────────────────────────────────────────────
if md_content is not None:
    header_line = ""
    for line in md_content.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|") and "---" not in stripped:
            header_line = stripped.lower()
            break
    
    has_region = "region" in header_line
    has_count = any(x in header_line for x in ["order_count", "orders", "count"])
    has_revenue = any(x in header_line for x in ["total_revenue", "revenue", "total"])
    
    if has_region and has_count and has_revenue:
        ok("markdown_columns", f"Header line contains expected column concepts: '{header_line}'")
    else:
        fail("markdown_columns", f"Header line missing expected columns (region, count, revenue). Got: '{header_line}'")
        passed_all = False
else:
    fail("markdown_columns", "Skipped: file not readable.")
    passed_all = False

# ─────────────────────────────────────────────
# CHECK 5: Markdown table aggregated values are correct
# ─────────────────────────────────────────────
if md_content is not None:
    # Parse markdown table rows: skip header and separator
    data_rows = []
    for line in md_content.strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|") and "---" not in stripped:
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            data_rows.append(cells)
    
    # first row is header, rest are data
    if len(data_rows) < 2:
        fail("markdown_values_correct", "Not enough rows to validate data.")
        passed_all = False
    else:
        header_cells = [c.lower() for c in data_rows[0]]
        
        # Find column indices
        region_idx = next((i for i, h in enumerate(header_cells) if "region" in h), None)
        count_idx = next((i for i, h in enumerate(header_cells) if any(x in h for x in ["order_count","orders","count"])), None)
        revenue_idx = next((i for i, h in enumerate(header_cells) if any(x in h for x in ["total_revenue","revenue","total"])), None)
        
        if region_idx is None or count_idx is None or revenue_idx is None:
            fail("markdown_values_correct", f"Cannot locate required columns. Headers: {header_cells}")
            passed_all = False
        else:
            errors = []
            for row in data_rows[1:]:
                if len(row) <= max(region_idx, count_idx, revenue_idx):
                    continue
                region_val = row[region_idx].strip()
                # Map N/A back to NULL key
                ref_key = "NULL" if region_val == "N/A" else region_val
                if ref_key not in ref:
                    errors.append(f"Unexpected region '{region_val}' not in reference.")
                    continue
                try:
                    got_count = int(row[count_idx].replace(",","").strip())
                    got_revenue = float(row[revenue_idx].replace(",","").strip())
                except ValueError:
                    errors.append(f"Cannot parse count/revenue for region '{region_val}': count='{row[count_idx]}', revenue='{row[revenue_idx]}'")
                    continue
                
                exp_count = ref[ref_key]["order_count"]
                exp_revenue = ref[ref_key]["total_revenue"]
                
                if got_count != exp_count:
                    errors.append(f"Region '{region_val}': order_count {got_count} != expected {exp_count}")
                if abs(got_revenue - exp_revenue) > 1.0:  # allow $1 rounding tolerance
                    errors.append(f"Region '{region_val}': total_revenue {got_revenue} != expected {exp_revenue} (diff={abs(got_revenue-exp_revenue):.2f})")
            
            if errors:
                fail("markdown_values_correct", "Aggregation errors: " + "; ".join(errors[:5]))
                passed_all = False
            else:
                ok("markdown_values_correct", "All region aggregations match expected values.")

# ─────────────────────────────────────────────
# CHECK 6: high_value_orders.parquet exists
# ─────────────────────────────────────────────
parquet_files = list(Path(workspace).rglob("high_value_orders.parquet"))
if not parquet_files:
    fail("high_value_parquet_exists", "File 'high_value_orders.parquet' not found anywhere in workspace.")
    passed_all = False
    parquet_path = None
else:
    parquet_path = parquet_files[0]
    ok("high_value_parquet_exists", f"Found at {parquet_path}")

# ─────────────────────────────────────────────
# CHECK 7: high_value_orders.parquet is readable as Parquet and has correct row count
# ─────────────────────────────────────────────
if parquet_path is not None:
    try:
        import duckdb
        con = duckdb.connect()
        result = con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquet_path}')").fetchone()
        row_count = result[0]
        con.close()
        if row_count == high_value_expected:
            ok("high_value_parquet_row_count", f"Parquet has {row_count} rows, matches expected {high_value_expected}.")
        else:
            fail("high_value_parquet_row_count", f"Parquet has {row_count} rows, expected {high_value_expected} (orders with total_amount > 500).")
            passed_all = False
    except Exception as e:
        fail("high_value_parquet_row_count", f"Could not query parquet file: {e}")
        passed_all = False
else:
    fail("high_value_parquet_row_count", "Skipped: file not found.")
    passed_all = False

# ─────────────────────────────────────────────
# CHECK 8: high_value_orders.parquet contains product_name column (join was performed)
# ─────────────────────────────────────────────
if parquet_path is not None:
    try:
        import duckdb
        con = duckdb.connect()
        cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')").fetchall()
        col_names = [c[0].lower() for c in cols]
        con.close()
        if "product_name" in col_names or "category" in col_names:
            ok("high_value_parquet_join", f"Parquet contains product catalog columns: {col_names}")
        else:
            fail("high_value_parquet_join", f"Parquet missing product_name/category columns from JOIN. Got: {col_names}")
            passed_all = False
    except Exception as e:
        fail("high_value_parquet_join", f"Could not inspect parquet schema: {e}")
        passed_all = False
else:
    fail("high_value_parquet_join", "Skipped: file not found.")
    passed_all = False

# ─────────────────────────────────────────────
# Final score
# ─────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
final_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_passed,
    "score": score,
    "checks": checks
}, indent=2))