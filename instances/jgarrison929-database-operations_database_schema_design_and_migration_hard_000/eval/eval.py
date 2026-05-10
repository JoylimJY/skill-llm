#!/usr/bin/env python3
"""
Evaluation script for the ecommerce DB modernization task.
Checks both the SQL file AND the live database state.
"""

import sys
import json
import subprocess
import re
from pathlib import Path

def run_psql(query: str, dbname: str = "ecommerce_db") -> tuple[bool, str]:
    """Execute a psql command and return (success, output)."""
    try:
        result = subprocess.run(
            ["su", "-c", f"psql -U postgres -d {dbname} -c \"{query}\" -t --no-align", "postgres"],
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
    except Exception as e:
        return False, str(e)

def run_psql_file(filepath: str, dbname: str = "ecommerce_db") -> tuple[bool, str]:
    """Execute a SQL file and return (success, output)."""
    try:
        result = subprocess.run(
            ["su", "-c", f"psql -U postgres -d {dbname} -f {filepath}", "postgres"],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def main(workspace: str) -> dict:
    checks = []
    workspace_path = Path(workspace)

    # ===== CHECK 1: schema_migration.sql file exists =====
    sql_files = list(workspace_path.rglob("schema_migration.sql"))
    file_exists = len(sql_files) > 0
    sql_path = str(sql_files[0]) if file_exists else None
    checks.append({
        "name": "schema_migration.sql file exists",
        "passed": file_exists,
        "detail": f"Found at {sql_path}" if file_exists else "File schema_migration.sql not found anywhere in workspace"
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "remaining checks skipped", "passed": False, "detail": "No SQL file found"}]
        }

    # Read the SQL content for static analysis
    try:
        sql_content = Path(sql_path).read_text()
    except Exception as e:
        checks.append({"name": "SQL file readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ===== CHECK 2: Apply the migration to live DB =====
    apply_ok, apply_out = run_psql_file(sql_path)
    checks.append({
        "name": "schema_migration.sql applies without error",
        "passed": apply_ok,
        "detail": f"Output: {apply_out[:500]}" if not apply_ok else "Migration applied successfully"
    })

    # ===== CHECK 3: audit_operation ENUM exists with correct values =====
    ok, out = run_psql("SELECT unnest(enum_range(NULL::audit_operation))::text ORDER BY 1;")
    enum_values = set(out.strip().split('\n')) if ok and out.strip() else set()
    enum_correct = {'DELETE', 'INSERT', 'UPDATE'} == enum_values
    checks.append({
        "name": "audit_operation ENUM has correct values (INSERT, UPDATE, DELETE)",
        "passed": enum_correct,
        "detail": f"Found enum values: {enum_values}"
    })

    # ===== CHECK 4: audit_log table exists with required columns =====
    ok, out = run_psql("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'audit_log' AND table_schema = 'public'
        ORDER BY column_name;
    """)
    if ok and out.strip():
        audit_cols = set(out.strip().split('\n'))
        required_audit_cols = {'id', 'table_name', 'record_id', 'operation', 'old_values', 'new_values', 'created_at'}
        audit_table_ok = required_audit_cols.issubset(audit_cols)
        checks.append({
            "name": "audit_log table has required columns",
            "passed": audit_table_ok,
            "detail": f"Found columns: {audit_cols}, Required: {required_audit_cols}"
        })
    else:
        checks.append({"name": "audit_log table has required columns", "passed": False, "detail": f"Could not query audit_log columns: {out}"})

    # ===== CHECK 5: old_values and new_values columns are JSONB type =====
    ok, out = run_psql("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_name = 'audit_log' AND column_name IN ('old_values', 'new_values')
        ORDER BY column_name;
    """)
    jsonb_ok = 'jsonb' in out.lower() if ok else False
    checks.append({
        "name": "audit_log.old_values and new_values are JSONB type",
        "passed": jsonb_ok,
        "detail": f"Column types: {out}"
    })

    # ===== CHECK 6: audit_trigger_function uses correct pattern =====
    # Must use TG_TABLE_NAME, TG_OP, to_jsonb
    has_tg_table_name = 'TG_TABLE_NAME' in sql_content or 'tg_table_name' in sql_content.lower()
    has_to_jsonb = 'to_jsonb' in sql_content.lower()
    has_tg_op = 'TG_OP' in sql_content or 'tg_op' in sql_content.lower()
    trigger_fn_ok = has_tg_table_name and has_to_jsonb and has_tg_op
    checks.append({
        "name": "audit_trigger_function uses TG_TABLE_NAME, TG_OP, to_jsonb (not row_to_json)",
        "passed": trigger_fn_ok,
        "detail": f"TG_TABLE_NAME: {has_tg_table_name}, to_jsonb: {has_to_jsonb}, TG_OP: {has_tg_op}"
    })

    # ===== CHECK 7: orders table is partitioned by created_at =====
    ok, out = run_psql("""
        SELECT partstrat FROM pg_partitioned_table pt
        JOIN pg_class c ON c.oid = pt.partrelid
        WHERE c.relname = 'orders';
    """)
    is_partitioned = 'r' in out if ok else False  # 'r' = RANGE
    checks.append({
        "name": "orders table is range-partitioned",
        "passed": is_partitioned,
        "detail": f"Partition strategy (r=range): {out}"
    })

    # ===== CHECK 8: Three monthly partitions exist for orders =====
    ok, out = run_psql("""
        SELECT c.relname FROM pg_inherits i
        JOIN pg_class c ON c.oid = i.inhrelid
        JOIN pg_class p ON p.oid = i.inhparent
        WHERE p.relname = 'orders'
        ORDER BY c.relname;
    """)
    partition_names = out.strip().split('\n') if ok and out.strip() else []
    expected_partitions = {'orders_2024_01', 'orders_2024_02', 'orders_2024_03'}
    found_partitions = set(partition_names)
    partitions_ok = expected_partitions.issubset(found_partitions)
    checks.append({
        "name": "Monthly partitions orders_2024_01, orders_2024_02, orders_2024_03 exist",
        "passed": partitions_ok,
        "detail": f"Found partitions: {found_partitions}, Expected: {expected_partitions}"
    })

    # ===== CHECK 9: create_monthly_partition function exists with correct signature =====
    ok, out = run_psql("""
        SELECT proname FROM pg_proc
        WHERE proname = 'create_monthly_partition';
    """)
    fn_exists = 'create_monthly_partition' in out if ok else False
    checks.append({
        "name": "create_monthly_partition function exists",
        "passed": fn_exists,
        "detail": f"Query output: {out}"
    })

    # Verify the function uses the skill's pattern: p_table || '_' || to_char(p_date, 'YYYY_MM')
    has_to_char = 'to_char' in sql_content.lower()
    has_yyyy_mm = 'YYYY_MM' in sql_content or 'yyyy_mm' in sql_content.lower()
    has_interval = "INTERVAL '1 month'" in sql_content or "interval '1 month'" in sql_content.lower()
    partition_fn_pattern_ok = has_to_char and has_yyyy_mm and has_interval
    checks.append({
        "name": "create_monthly_partition uses to_char(date,'YYYY_MM') and INTERVAL '1 month' pattern",
        "passed": partition_fn_pattern_ok,
        "detail": f"to_char: {has_to_char}, YYYY_MM: {has_yyyy_mm}, INTERVAL '1 month': {has_interval}"
    })

    # ===== CHECK 10: Functional test - partition function creates new partition =====
    if fn_exists:
        ok2, out2 = run_psql("SELECT create_monthly_partition('orders', '2024-04-01'::DATE);")
        # Check if orders_2024_04 now exists
        ok3, out3 = run_psql("""
            SELECT c.relname FROM pg_inherits i
            JOIN pg_class c ON c.oid = i.inhrelid
            JOIN pg_class p ON p.oid = i.inhparent
            WHERE p.relname = 'orders' AND c.relname = 'orders_2024_04';
        """)
        fn_functional = 'orders_2024_04' in out3 if ok3 else False
        checks.append({
            "name": "create_monthly_partition function correctly creates new partition when invoked",
            "passed": fn_functional,
            "detail": f"Called for 2024-04-01, found orders_2024_04: {fn_functional}, output: {out3}"
        })
    else:
        checks.append({"name": "create_monthly_partition functional test", "passed": False, "detail": "Function not found, skipped"})

    # ===== CHECK 11: orders primary key includes both id AND created_at =====
    ok, out = run_psql("""
        SELECT a.attname FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(c.conkey)
        WHERE c.contype = 'p' AND t.relname = 'orders'
        ORDER BY a.attname;
    """)
    pk_cols = set(out.strip().split('\n')) if ok and out.strip() else set()
    pk_ok = {'id', 'created_at'}.issubset(pk_cols)
    checks.append({
        "name": "orders table has composite PK (id, created_at) required for partitioning",
        "passed": pk_ok,
        "detail": f"PK columns found: {pk_cols}"
    })

    # ===== CHECK 12: Covering index on orders (user_id, status) INCLUDE (total, created_at) =====
    ok, out = run_psql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename LIKE 'orders%' AND indexdef LIKE '%user_id%' AND indexdef LIKE '%status%';
    """)
    has_covering_index = ok and out.strip() != ''
    # Check it uses INCLUDE clause
    has_include = 'include' in out.lower() if ok else False
    has_total_in_include = 'total' in out.lower() if ok else False
    covering_idx_ok = has_covering_index and has_include and has_total_in_include
    checks.append({
        "name": "Covering index on orders(user_id, status) INCLUDE (total, created_at) exists",
        "passed": covering_idx_ok,
        "detail": f"Found: {out[:300] if ok else 'error: ' + out}"
    })

    # ===== CHECK 13: products table exists with correct columns =====
    ok, out = run_psql("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'products' ORDER BY column_name;
    """)
    product_cols = set(out.strip().split('\n')) if ok and out.strip() else set()
    required_product_cols = {'id', 'name', 'description', 'sku', 'inventory_quantity', 'inventory_tracking', 'attributes', 'price'}
    products_ok = required_product_cols.issubset(product_cols)
    checks.append({
        "name": "products table has all required columns",
        "passed": products_ok,
        "detail": f"Found: {product_cols}, Required: {required_product_cols}"
    })

    # ===== CHECK 14: products.price is DECIMAL (not FLOAT) =====
    ok, out = run_psql("""
        SELECT data_type FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'price';
    """)
    price_type_ok = 'numeric' in out.lower() if ok else False  # DECIMAL maps to 'numeric' in PostgreSQL
    checks.append({
        "name": "products.price is DECIMAL/NUMERIC (not FLOAT) — anti-pattern check",
        "passed": price_type_ok,
        "detail": f"price column type: {out}"
    })

    # ===== CHECK 15: Full-text search vector column on products =====
    ok, out = run_psql("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_name = 'products' AND data_type = 'tsvector';
    """)
    has_tsvector = ok and 'tsvector' in out.lower()
    checks.append({
        "name": "products table has tsvector column for full-text search",
        "passed": has_tsvector,
        "detail": f"tsvector column found: {out}"
    })

    # Verify it uses GENERATED ALWAYS AS ... STORED pattern (stored generated column)
    has_generated = 'GENERATED ALWAYS AS' in sql_content.upper()
    has_stored = 'STORED' in sql_content.upper()
    has_to_tsvector = 'to_tsvector' in sql_content.lower()
    fts_pattern_ok = has_generated and has_stored and has_to_tsvector
    checks.append({
        "name": "Full-text search uses GENERATED ALWAYS AS (tsvector) STORED pattern",
        "passed": fts_pattern_ok,
        "detail": f"GENERATED ALWAYS AS: {has_generated}, STORED: {has_stored}, to_tsvector: {has_to_tsvector}"
    })

    # ===== CHECK 16: GIN index on products.search_vector =====
    ok, out = run_psql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename = 'products' AND indexdef LIKE '%gin%';
    """)
    has_gin_index = ok and out.strip() != ''
    checks.append({
        "name": "GIN index on products for full-text search (search_vector or attributes)",
        "passed": has_gin_index,
        "detail": f"GIN indexes found: {out}"
    })

    # ===== CHECK 17: Partial index on products (low inventory) =====
    ok, out = run_psql("""
        SELECT indexname, indexdef FROM pg_indexes
        WHERE tablename = 'products' AND indexdef LIKE '%inventory_tracking%';
    """)
    has_partial_inventory_idx = ok and 'inventory_quantity' in out.lower() and 'where' in out.lower()
    checks.append({
        "name": "Partial index on products for low inventory (WHERE inventory_tracking=true AND inventory_quantity<=5)",
        "passed": has_partial_inventory_idx,
        "detail": f"Found: {out}"
    })

    # ===== CHECK 18: soft_delete function exists =====
    ok, out = run_psql("SELECT proname FROM pg_proc WHERE proname = 'soft_delete';")
    soft_delete_fn_ok = 'soft_delete' in out if ok else False
    checks.append({
        "name": "soft_delete utility function exists",
        "passed": soft_delete_fn_ok,
        "detail": f"Query output: {out}"
    })

    # soft_delete must use EXECUTE format with %I pattern
    has_execute_format = 'EXECUTE format' in sql_content or 'execute format' in sql_content.lower()
    has_percent_I = '%I' in sql_content
    soft_delete_pattern_ok = has_execute_format and has_percent_I
    checks.append({
        "name": "soft_delete function uses EXECUTE format('%I') dynamic SQL pattern from skill",
        "passed": soft_delete_pattern_ok,
        "detail": f"EXECUTE format: {has_execute_format}, %I identifier quoting: {has_percent_I}"
    })

    # ===== CHECK 19: Audit trigger functional test =====
    # Insert a row into orders, update it, verify audit_log has entries
    ok_ins, out_ins = run_psql("""
        INSERT INTO orders (user_id, status, total, created_at)
        VALUES (1, 'pending', 99.99, '2024-01-15 10:00:00+00');
    """)
    if ok_ins:
        # Check audit log has INSERT record
        ok_a, out_a = run_psql("""
            SELECT operation FROM audit_log
            WHERE table_name = 'orders' AND operation = 'INSERT'
            LIMIT 1;
        """)
        audit_insert_ok = 'INSERT' in out_a if ok_a else False

        # Do an UPDATE and check audit log
        run_psql("UPDATE orders SET status = 'shipped' WHERE user_id = 1 AND created_at = '2024-01-15 10:00:00+00';")
        ok_u, out_u = run_psql("""
            SELECT operation, old_values::text, new_values::text FROM audit_log
            WHERE table_name = 'orders' AND operation = 'UPDATE'
            LIMIT 1;
        """)
        # old_values should contain 'pending', new_values should contain 'shipped'
        audit_update_ok = ok_u and 'UPDATE' in out_u and 'pending' in out_u and 'shipped' in out_u
        checks.append({
            "name": "Audit trigger captures INSERT into orders table",
            "passed": audit_insert_ok,
            "detail": f"Audit INSERT found: {audit_insert_ok}, output: {out_a}"
        })
        checks.append({
            "name": "Audit trigger captures UPDATE with old_values (pending) and new_values (shipped)",
            "passed": audit_update_ok,
            "detail": f"UPDATE audit row: {out_u[:200]}"
        })
    else:
        checks.append({"name": "Audit trigger INSERT test", "passed": False, "detail": f"Could not insert into orders: {out_ins}"})
        checks.append({"name": "Audit trigger UPDATE test", "passed": False, "detail": "Insert failed, skipping UPDATE test"})

    # ===== CHECK 20: indexes use CONCURRENTLY (anti-pattern avoidance) =====
    # Count CREATE INDEX statements and CONCURRENTLY occurrences
    create_index_count = len(re.findall(r'CREATE\s+INDEX', sql_content, re.IGNORECASE))
    concurrently_count = len(re.findall(r'CREATE\s+INDEX\s+CONCURRENTLY', sql_content, re.IGNORECASE))
    # At least 3 regular indexes should use CONCURRENTLY
    concurrently_ok = concurrently_count >= 3
    checks.append({
        "name": "Indexes use CREATE INDEX CONCURRENTLY (at least 3) for production safety",
        "passed": concurrently_ok,
        "detail": f"Total CREATE INDEX: {create_index_count}, Using CONCURRENTLY: {concurrently_count}"
    })

    # ===== Compute score =====
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(passed_count / total_count, 3)
    overall_passed = score >= 0.80  # Must pass at least 80% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace_dir)
    print(json.dumps(result, indent=2))