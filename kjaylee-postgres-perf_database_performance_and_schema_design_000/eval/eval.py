import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_migration_file(workspace):
    """Find schema_migration.sql anywhere in workspace."""
    results = list(Path(workspace).rglob("schema_migration.sql"))
    return results[0] if results else None

def load_sql(path):
    try:
        return path.read_text(encoding="utf-8").lower()
    except Exception as e:
        return ""

def run_check(name, cond, detail):
    checks.append({"name": name, "passed": bool(cond), "detail": detail})
    return bool(cond)

# ─── Locate file ─────────────────────────────────────────────────────────────
migration_file = find_migration_file(workspace)

if migration_file is None:
    checks.append({"name": "file_exists", "passed": False,
                   "detail": "schema_migration.sql not found anywhere in workspace"})
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

run_check("file_exists", True, f"Found at {migration_file}")
sql = load_sql(migration_file)

# ─── CHECK 1: No SELECT * ────────────────────────────────────────────────────
# The file should not contain SELECT * patterns in query definitions
select_star = re.search(r'select\s+\*', sql)
run_check(
    "no_select_star",
    not select_star,
    "No 'SELECT *' found — correct" if not select_star
    else "Found 'SELECT *' which violates the CRITICAL rule"
)

# ─── CHECK 2: DROP or replace bad composite index ────────────────────────────
drop_composite = re.search(r'drop\s+index.*idx_everything_orders', sql)
run_check(
    "drop_bad_composite_index",
    bool(drop_composite),
    "idx_everything_orders composite index is dropped — correct" if drop_composite
    else "Bloated composite index idx_everything_orders was not dropped"
)

# ─── CHECK 3: Partial index on orders WHERE status = 'active' ────────────────
# Must use WHERE clause — this is the key proprietary trap
partial_index_pattern = re.search(
    r'create\s+index\s+\w+\s+on\s+orders\s*\(.*created_at.*\)\s*where\s+status\s*=\s*[\'"]active[\'"]',
    sql,
    re.IGNORECASE
)
run_check(
    "partial_index_active_orders",
    bool(partial_index_pattern),
    "Partial index on orders(created_at) WHERE status='active' found — correct" if partial_index_pattern
    else "Missing partial index on orders for active status — must use WHERE status='active' clause"
)

# ─── CHECK 4: Index on customers(email) ──────────────────────────────────────
email_index = re.search(r'create\s+index\s+\w+\s+on\s+customers\s*\(\s*email\s*\)', sql, re.IGNORECASE)
run_check(
    "index_customers_email",
    bool(email_index),
    "Index on customers(email) found — correct" if email_index
    else "Missing index on customers(email) — reported as 4-6s slow by support team"
)

# ─── CHECK 5: Index on orders(customer_id) ───────────────────────────────────
customer_id_index = re.search(
    r'create\s+index\s+\w+\s+on\s+orders\s*\(\s*customer_id\s*\)',
    sql, re.IGNORECASE
)
run_check(
    "index_orders_customer_id",
    bool(customer_id_index),
    "Index on orders(customer_id) found — correct" if customer_id_index
    else "Missing index on orders(customer_id) — critical for customer order lookups"
)

# ─── CHECK 6: JSONB metadata columns extracted to real columns ───────────────
# metadata->>'region' and metadata->>'priority' are queried — must become columns
# Agent should add region and priority as proper columns (ALTER TABLE or in schema)
region_col = re.search(r'(add\s+column\s+region|region\s+varchar|region\s+text)', sql, re.IGNORECASE)
priority_col = re.search(r'(add\s+column\s+priority|priority\s+varchar|priority\s+text|priority\s+integer|priority\s+int)', sql, re.IGNORECASE)
run_check(
    "jsonb_region_extracted_to_column",
    bool(region_col),
    "region extracted from JSONB to proper column — correct" if region_col
    else "metadata->>'region' is queried heavily but not extracted to a proper column"
)
run_check(
    "jsonb_priority_extracted_to_column",
    bool(priority_col),
    "priority extracted from JSONB to proper column — correct" if priority_col
    else "metadata->>'priority' is queried heavily but not extracted to a proper column"
)

# ─── CHECK 7: Index on extracted region column ───────────────────────────────
region_index = re.search(r'create\s+index\s+\w+\s+on\s+orders\s*\(\s*region\s*\)', sql, re.IGNORECASE)
run_check(
    "index_on_region_column",
    bool(region_index),
    "Index on orders(region) found — correct" if region_index
    else "No index on region column — APAC filter queries will still be slow"
)

# ─── CHECK 8: RLS enabled on orders ──────────────────────────────────────────
rls_enabled = re.search(r'alter\s+table\s+orders\s+enable\s+row\s+level\s+security', sql, re.IGNORECASE)
run_check(
    "rls_enabled_orders",
    bool(rls_enabled),
    "RLS enabled on orders table — correct" if rls_enabled
    else "RLS not enabled on orders table — compliance requirement"
)

# ─── CHECK 9: RLS policy uses customer_id = auth.uid() ───────────────────────
rls_policy = re.search(
    r'create\s+policy\s+\w+\s+on\s+orders.*using\s*\(\s*customer_id\s*=\s*auth\.uid\(\)',
    sql, re.IGNORECASE | re.DOTALL
)
run_check(
    "rls_policy_correct",
    bool(rls_policy),
    "RLS policy with customer_id = auth.uid() found — correct" if rls_policy
    else "RLS policy missing or incorrect — must use customer_id = auth.uid()"
)

# ─── CHECK 10: RLS paired with index on customer_id (index exists from check 5) ─
# This check verifies the agent understands RLS needs index support
# We verify customer_id index exists alongside RLS policy
rls_with_index = (
    bool(rls_policy) and bool(customer_id_index)
)
run_check(
    "rls_paired_with_index",
    rls_with_index,
    "RLS policy is paired with an index on customer_id — performance-safe" if rls_with_index
    else "RLS policy exists but customer_id index is missing — RLS will cause full scan"
)

# ─── Score calculation ───────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)

# Must pass critical checks to be considered overall passing
critical_passed = all(
    c["passed"] for c in checks
    if c["name"] in {
        "file_exists",
        "no_select_star",
        "partial_index_active_orders",
        "rls_enabled_orders",
        "rls_policy_correct",
        "drop_bad_composite_index",
    }
)

result = {
    "passed": critical_passed and score >= 0.75,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, indent=2))