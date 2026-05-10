#!/usr/bin/env python3
import sys
import json
import subprocess
import os

WORKSPACE = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

DB_NAME = "healthdb"
DB_USER = "healthadmin"
DB_PASS = "health_secret_2024"
DB_HOST = "localhost"

checks = []

def run_sql(query, db=DB_NAME):
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    result = subprocess.run(
        ["psql", "-U", DB_USER, "-d", db, "-h", DB_HOST, "-tAc", query],
        capture_output=True, text=True, env=env, timeout=30
    )
    return result.stdout.strip(), result.stderr.strip()

def check(name, fn):
    try:
        passed, detail = fn()
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed
    except Exception as e:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})
        return False

# -----------------------------------------------------------------------
# 1. providers table exists with correct ENUM status type
# -----------------------------------------------------------------------
def check_providers_table():
    out, err = run_sql("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'providers';
    """)
    if out.strip() != "1":
        return False, f"providers table does not exist. stdout={out}, stderr={err}"
    return True, "providers table exists"

check("providers_table_exists", check_providers_table)

# -----------------------------------------------------------------------
# 2. providers status column uses ENUM type (not VARCHAR)
# -----------------------------------------------------------------------
def check_providers_status_enum():
    out, err = run_sql("""
        SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='providers' AND column_name='status';
    """)
    # PostgreSQL reports user-defined enums as 'USER-DEFINED'
    if "user-defined" not in out.lower() and "enum" not in out.lower():
        return False, f"providers.status is not an ENUM type, got: '{out}'"
    # Also verify the enum values
    out2, _ = run_sql("""
        SELECT enumlabel FROM pg_enum
        JOIN pg_type ON pg_enum.enumtypid = pg_type.oid
        WHERE pg_type.typname LIKE '%status%'
        ORDER BY enumlabel;
    """)
    required_vals = {"active", "inactive", "suspended", "pending"}
    found_vals = set(out2.strip().split("\n")) if out2.strip() else set()
    if not required_vals.issubset(found_vals):
        return False, f"ENUM missing required values. Found: {found_vals}"
    return True, f"providers.status is USER-DEFINED ENUM with values: {found_vals}"

check("providers_status_is_enum", check_providers_status_enum)

# -----------------------------------------------------------------------
# 3. providers table has deleted_at column (soft delete pattern)
# -----------------------------------------------------------------------
def check_soft_delete_column():
    out, err = run_sql("""
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema='public' AND table_name='providers' AND column_name='deleted_at';
    """)
    if out.strip() != "1":
        return False, "providers.deleted_at column missing"
    # Check it's TIMESTAMPTZ
    out2, _ = run_sql("""
        SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='providers' AND column_name='deleted_at';
    """)
    if "timestamp" not in out2.lower():
        return False, f"deleted_at is not a timestamp type: {out2}"
    return True, "providers.deleted_at exists as timestamp type"

check("providers_soft_delete_column", check_soft_delete_column)

# -----------------------------------------------------------------------
# 4. consultation_fee uses DECIMAL/NUMERIC, NOT float
# -----------------------------------------------------------------------
def check_fee_not_float():
    out, err = run_sql("""
        SELECT data_type FROM information_schema.columns
        WHERE table_schema='public' AND table_name='appointments'
        AND column_name='consultation_fee';
    """)
    if not out.strip():
        return False, "appointments.consultation_fee column not found"
    if "float" in out.lower() or "double" in out.lower() or "real" in out.lower():
        return False, f"consultation_fee uses float type (anti-pattern): {out}"
    if "numeric" not in out.lower() and "decimal" not in out.lower():
        return False, f"consultation_fee should be DECIMAL/NUMERIC, got: {out}"
    return True, f"consultation_fee uses correct type: {out}"

check("consultation_fee_not_float", check_fee_not_float)

# -----------------------------------------------------------------------
# 5. audit_log table exists with correct structure
# -----------------------------------------------------------------------
def check_audit_log_table():
    out, err = run_sql("""
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema='public' AND table_name='audit_log';
    """)
    if out.strip() != "1":
        return False, "audit_log table does not exist"
    # Check key columns
    out2, _ = run_sql("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name='audit_log'
        ORDER BY column_name;
    """)
    found_cols = set(out2.strip().split("\n")) if out2.strip() else set()
    required = {"table_name", "record_id", "operation", "old_values", "new_values"}
    missing = required - found_cols
    if missing:
        return False, f"audit_log missing columns: {missing}. Found: {found_cols}"
    return True, f"audit_log has required columns: {found_cols}"

check("audit_log_table_exists", check_audit_log_table)

# -----------------------------------------------------------------------
# 6. Audit trigger is installed on providers table
# -----------------------------------------------------------------------
def check_audit_trigger():
    out, err = run_sql("""
        SELECT COUNT(*) FROM information_schema.triggers
        WHERE trigger_schema='public' AND event_object_table='providers'
        AND event_manipulation IN ('INSERT','UPDATE','DELETE');
    """)
    count = int(out.strip()) if out.strip().isdigit() else 0
    if count < 1:
        return False, f"No audit triggers found on providers table (count={count})"
    return True, f"Found {count} trigger event(s) on providers table"

check("audit_trigger_on_providers", check_audit_trigger)

# -----------------------------------------------------------------------
# 7. Audit trigger actually works: INSERT into providers logs to audit_log
# -----------------------------------------------------------------------
def check_audit_trigger_works():
    # Insert a test provider
    insert_sql = """
        INSERT INTO providers (email, username, password_hash, first_name, last_name, specialty, status)
        VALUES ('eval_test_doc@medibook.com', 'eval_testdoc', 'hash123', 'Eval', 'Doctor', 'General', 'active')
        ON CONFLICT DO NOTHING;
    """
    run_sql(insert_sql)
    # Check audit_log has entry for providers INSERT
    out, err = run_sql("""
        SELECT COUNT(*) FROM audit_log
        WHERE table_name='providers' AND operation='INSERT';
    """)
    count = int(out.strip()) if out.strip().isdigit() else 0
    if count < 1:
        return False, f"Audit trigger did not log INSERT to providers. audit_log count={count}, err={err}"
    
    # Test UPDATE logs both old and new values
    run_sql("""
        UPDATE providers SET specialty='Cardiology' WHERE email='eval_test_doc@medibook.com';
    """)
    out2, _ = run_sql("""
        SELECT COUNT(*) FROM audit_log
        WHERE table_name='providers' AND operation='UPDATE'
        AND old_values IS NOT NULL AND new_values IS NOT NULL;
    """)
    upd_count = int(out2.strip()) if out2.strip().isdigit() else 0
    if upd_count < 1:
        return False, "Audit trigger UPDATE did not record old_values and new_values"
    return True, f"Audit trigger works: {count} INSERT(s) and {upd_count} UPDATE(s) logged"

check("audit_trigger_functional", check_audit_trigger_works)

# -----------------------------------------------------------------------
# 8. Expression index on lower(email) exists for providers
# -----------------------------------------------------------------------
def check_expression_index_lower_email():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename='providers' AND schemaname='public'
        AND indexdef ILIKE '%lower%email%';
    """)
    if not out.strip():
        return False, "No expression index on lower(email) found for providers table"
    return True, f"Expression index on lower(email) found: {out.strip()[:120]}"

check("expression_index_lower_email", check_expression_index_lower_email)

# -----------------------------------------------------------------------
# 9. Partial index on providers.status WHERE status != 'active'
# -----------------------------------------------------------------------
def check_partial_index_status():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename='providers' AND schemaname='public'
        AND indexdef ILIKE '%status%'
        AND indexdef ILIKE '%where%';
    """)
    if not out.strip():
        return False, "No partial index on providers.status found"
    # Must exclude 'active' (the partial condition)
    if "active" not in out.lower():
        return False, f"Partial index on status found but doesn't filter on 'active': {out}"
    return True, f"Partial index on status (excluding active) found: {out.strip()[:120]}"

check("partial_index_status_not_active", check_partial_index_status)

# -----------------------------------------------------------------------
# 10. Partial index on deleted_at WHERE deleted_at IS NULL
# -----------------------------------------------------------------------
def check_partial_index_deleted_at():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename='providers' AND schemaname='public'
        AND indexdef ILIKE '%deleted_at%'
        AND indexdef ILIKE '%null%';
    """)
    if not out.strip():
        return False, "No partial index on providers.deleted_at IS NULL found"
    return True, f"Partial index on deleted_at found: {out.strip()[:120]}"

check("partial_index_deleted_at_null", check_partial_index_deleted_at)

# -----------------------------------------------------------------------
# 11. appointments table is partitioned (RANGE on created_at)
# -----------------------------------------------------------------------
def check_appointments_partitioned():
    out, err = run_sql("""
        SELECT partstrat FROM pg_partitioned_table pt
        JOIN pg_class c ON pt.partrelid = c.oid
        WHERE c.relname = 'appointments';
    """)
    if out.strip() != "r":
        return False, f"appointments table is not RANGE partitioned. Got: '{out}', err={err}"
    return True, "appointments table is RANGE partitioned"

check("appointments_table_partitioned", check_appointments_partitioned)

# -----------------------------------------------------------------------
# 12. Monthly partitions for 2024-01, 2024-02, 2024-03 exist
# -----------------------------------------------------------------------
def check_monthly_partitions():
    out, err = run_sql("""
        SELECT c.relname FROM pg_class c
        JOIN pg_inherits i ON c.oid = i.inhrelid
        JOIN pg_class p ON i.inhparent = p.oid
        WHERE p.relname = 'appointments'
        ORDER BY c.relname;
    """)
    if not out.strip():
        return False, "No child partitions found for appointments"
    partitions = set(out.strip().split("\n"))
    required_months = ["2024_01", "2024_02", "2024_03"]
    found_months = [m for m in required_months if any(m in p for p in partitions)]
    if len(found_months) < 3:
        return False, f"Missing monthly partitions. Found: {partitions}. Need: {required_months}"
    return True, f"All required monthly partitions found: {partitions}"

check("monthly_partitions_exist", check_monthly_partitions)

# -----------------------------------------------------------------------
# 13. Covering index on appointments (provider_id, status) INCLUDE (consultation_fee, appointment_date)
# -----------------------------------------------------------------------
def check_covering_index():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE (tablename LIKE 'appointments%') AND schemaname='public'
        AND indexdef ILIKE '%provider_id%status%'
        AND indexdef ILIKE '%include%';
    """)
    if not out.strip():
        return False, "No covering index with INCLUDE on appointments found"
    if "consultation_fee" not in out.lower() and "appointment_date" not in out.lower():
        return False, f"Covering index found but missing expected INCLUDE columns: {out}"
    return True, f"Covering index found: {out.strip()[:160]}"

check("covering_index_appointments", check_covering_index)

# -----------------------------------------------------------------------
# 14. Partial index on appointments.consultation_fee WHERE status='completed'
# -----------------------------------------------------------------------
def check_partial_index_completed_fee():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE (tablename LIKE 'appointments%') AND schemaname='public'
        AND indexdef ILIKE '%consultation_fee%'
        AND indexdef ILIKE '%completed%';
    """)
    if not out.strip():
        return False, "No partial index on consultation_fee WHERE status='completed' found"
    return True, f"Partial index on fee for completed appointments found: {out.strip()[:120]}"

check("partial_index_completed_fee", check_partial_index_completed_fee)

# -----------------------------------------------------------------------
# 15. monthly_revenue_summary materialized view exists
# -----------------------------------------------------------------------
def check_materialized_view():
    out, err = run_sql("""
        SELECT COUNT(*) FROM pg_matviews
        WHERE schemaname='public' AND matviewname='monthly_revenue_summary';
    """)
    if out.strip() != "1":
        return False, "monthly_revenue_summary materialized view not found"
    return True, "monthly_revenue_summary materialized view exists"

check("materialized_view_exists", check_materialized_view)

# -----------------------------------------------------------------------
# 16. Materialized view has UNIQUE index (required for CONCURRENT refresh)
# -----------------------------------------------------------------------
def check_matview_unique_index():
    out, err = run_sql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename='monthly_revenue_summary' AND schemaname='public'
        AND indexdef ILIKE '%unique%';
    """)
    if not out.strip():
        return False, "No UNIQUE index on monthly_revenue_summary (required for CONCURRENT refresh)"
    return True, f"UNIQUE index on materialized view found: {out.strip()[:120]}"

check("matview_unique_index_for_concurrent", check_matview_unique_index)

# -----------------------------------------------------------------------
# 17. Materialized view has correct columns (month, provider_id, revenue aggregates)
# -----------------------------------------------------------------------
def check_matview_columns():
    # Refresh the view first (in case it's empty) -- ignore error
    run_sql("REFRESH MATERIALIZED VIEW monthly_revenue_summary;")
    out, err = run_sql("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema='public' AND table_name='monthly_revenue_summary'
        ORDER BY column_name;
    """)
    if not out.strip():
        return False, "Cannot inspect monthly_revenue_summary columns"
    cols = set(out.strip().split("\n"))
    required = {"provider_id"}
    # Must have revenue-related columns
    has_revenue = any("revenue" in c.lower() or "total" in c.lower() or "fee" in c.lower() for c in cols)
    has_count = any("count" in c.lower() for c in cols)
    has_month = any("month" in c.lower() for c in cols)
    
    issues = []
    if not required.issubset(cols):
        issues.append(f"Missing columns: {required - cols}")
    if not has_revenue:
        issues.append("No revenue/total/fee aggregate column found")
    if not has_count:
        issues.append("No appointment count column found")
    if not has_month:
        issues.append("No month column found")
    
    if issues:
        return False, f"Materialized view column issues: {issues}. Found: {cols}"
    return True, f"Materialized view has correct structure. Columns: {cols}"

check("matview_correct_columns", check_matview_columns)

# -----------------------------------------------------------------------
# 18. active_providers view exists (soft delete view pattern)
# -----------------------------------------------------------------------
def check_active_providers_view():
    out, err = run_sql("""
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema='public' AND table_name='active_providers';
    """)
    if out.strip() != "1":
        return False, "active_providers view (soft delete filter) not found"
    # Verify it filters deleted_at IS NULL
    out2, _ = run_sql("""
        SELECT view_definition FROM information_schema.views
        WHERE table_schema='public' AND table_name='active_providers';
    """)
    if "deleted_at" not in out2.lower() or "null" not in out2.lower():
        return False, f"active_providers view does not filter on deleted_at IS NULL: {out2[:100]}"
    return True, "active_providers view exists and filters soft-deleted records"

check("active_providers_view", check_active_providers_view)

# -----------------------------------------------------------------------
# 19. Email constraint check (format validation on providers)
# -----------------------------------------------------------------------
def check_email_constraint():
    # Try inserting an invalid email - should fail
    bad_insert = """
        INSERT INTO providers (email, username, password_hash, first_name, last_name, status)
        VALUES ('not-an-email', 'testuserbad', 'hash', 'Test', 'User', 'active');
    """
    out, err = run_sql(bad_insert)
    if "violates check constraint" in err.lower() or "check" in err.lower() or "constraint" in err.lower():
        return True, "Email format constraint correctly rejects invalid email"
    # Also check constraint exists
    out2, err2 = run_sql("""
        SELECT COUNT(*) FROM information_schema.table_constraints
        WHERE table_schema='public' AND table_name='providers'
        AND constraint_type='CHECK';
    """)
    count = int(out2.strip()) if out2.strip().isdigit() else 0
    if count < 1:
        return False, "No CHECK constraints on providers table (email format validation missing)"
    return True, f"providers has {count} CHECK constraint(s)"

check("email_format_constraint", check_email_constraint)

# -----------------------------------------------------------------------
# 20. Solution SQL file exists in workspace
# -----------------------------------------------------------------------
def check_solution_file_exists():
    from pathlib import Path
    sql_files = list(Path(WORKSPACE).rglob("medibook_schema.sql"))
    if not sql_files:
        return False, "medibook_schema.sql not found anywhere in workspace"
    if len(sql_files) > 1:
        return True, f"Found {len(sql_files)} medibook_schema.sql files: {[str(f) for f in sql_files]}"
    return True, f"medibook_schema.sql found at: {sql_files[0]}"

check("solution_sql_file_exists", check_solution_file_exists)

# -----------------------------------------------------------------------
# Final scoring
# -----------------------------------------------------------------------
passed_checks = sum(1 for c in checks if c["passed"])
total_checks = len(checks)
score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
all_passed = passed_checks == total_checks

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))