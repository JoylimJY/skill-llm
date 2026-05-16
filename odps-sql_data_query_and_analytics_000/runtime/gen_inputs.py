import os
import stat
import textwrap

# Fixed seed for determinism
import random
random.seed(42)

workspace = "/workspace"

# --- Create directory structure ---
dirs = [
    "mcp-odps/scripts",
    "mcp-odps/references",
    "mcp-odps/logs",
    "mcp-odps/config",
    "reports/archive",
    "reports/draft",
    "data/raw",
    "data/processed",
    "notebooks",
    "etl/jobs",
    "etl/transforms",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "mcp-odps/config/config.example.env": textwrap.dedent("""\
        ALIYUN_ACCESS_ID=your_access_id_here
        ALIYUN_ACCESS_SECRET=your_access_secret_here
        ALIYUN_PROJECT_NAME=your_project_name
        ALIYUN_END_POINT=http://service.cn-hangzhou.maxcompute.aliyun.com/api
    """),
    "mcp-odps/logs/run_2024-10-31.log": textwrap.dedent("""\
        2024-10-31 08:00:01 INFO  Query executed: SELECT count(*) FROM orders_summary WHERE dt='2024-10-31'
        2024-10-31 08:00:03 INFO  Rows returned: 1
        2024-10-31 09:15:22 WARN  Slow query detected on table customer_profiles
    """),
    "mcp-odps/references/odps_sql_guide.md": textwrap.dedent("""\
        # ODPS SQL Reference Guide
        
        ## String Functions
        - CONCAT(str1, str2, ...) — concatenates strings
        - SUBSTR(str, start, len)
        - RLIKE — regex match operator (use instead of REGEXP)
        
        ## Null Handling
        - NVL(expr, default_value) — returns default if expr is null
        
        ## Date Functions
        - GETDATE() — current datetime
        - TO_DATE('2024-01-01','yyyy-mm-dd')
        
        ## Partitioned Tables
        - Always specify dt partition filter in WHERE clause
        - Full table scans on partitioned tables are prohibited
        
        ## Aggregate Functions
        - COUNT(*), SUM(), AVG(), MAX(), MIN()
        - GROUP BY supported
    """),
    "data/raw/orders_sample.csv": textwrap.dedent("""\
        order_id,customer_name,region,amount,dt
        10001,Alice Zhang,East,299.00,2024-11-01
        10002,Bob Li,West,155.50,2024-11-01
        10003,,North,88.00,2024-11-01
        10004,Carol Wang,East,430.00,2024-11-01
        10005,David Chen,South,210.00,2024-11-01
    """),
    "data/processed/summary_oct.json": '{"month": "2024-10", "total_orders": 18423, "regions": ["East","West","North","South"]}',
    "reports/archive/q3_report.json": '{"quarter": "Q3-2024", "revenue": 5820341.5, "top_region": "East"}',
    "reports/draft/nov_template.txt": "November 2024 Orders Report\n[DRAFT - DO NOT DISTRIBUTE]\n",
    "notebooks/exploration.py": textwrap.dedent("""\
        # Quick exploration notebook
        # WARNING: Old syntax used here — do NOT use as reference
        # result = conn.execute("SELECT * FROM orders_detail WHERE region REGEXP 'East|West'")
        # null_fill = "IFNULL(customer_name, 'Unknown')"
    """),
    "etl/jobs/daily_ingest.py": textwrap.dedent("""\
        import subprocess
        def run_daily():
            subprocess.run(['python', 'mcp-odps/scripts/odps_helper.py',
                            '--query', \"SELECT count(*) FROM orders_detail WHERE dt='2024-11-01'\"])
    """),
    "etl/transforms/region_map.json": '{"E":"East","W":"West","N":"North","S":"South"}',
    "mcp-odps/config/retry_policy.yaml": textwrap.dedent("""\
        max_retries: 3
        backoff_seconds: 2
        timeout_seconds: 30
    """),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- The critical mock odps_helper.py ---
# This script simulates real ODPS behavior:
# - --list-tables [--pattern X]: returns table list
# - --describe <table>: returns schema
# - --query "<SQL>" [--limit N]: validates ODPS-specific syntax and returns results
#
# The mock enforces ODPS SQL rules:
# - Rejects REGEXP (must use RLIKE)
# - Rejects IFNULL (must use NVL)
# - Rejects || for concat (must use CONCAT)
# - Rejects queries on orders_detail without a dt partition filter
# - Returns realistic JSON-serializable tabular output

odps_helper_script = textwrap.dedent(r'''
#!/usr/bin/env python3
"""
Mock ODPS helper script simulating Alibaba Cloud MaxCompute/ODPS CLI.
Responds to: --list-tables [--pattern], --describe <table>, --query "<SQL>" [--limit <n>]
"""
import argparse
import json
import re
import sys

ALL_TABLES = [
    "customer_profiles",
    "orders_detail",
    "orders_summary",
    "product_catalog",
    "region_dimension",
    "payment_transactions",
    "orders_returns",
    "marketing_campaigns",
    "logistics_tracking",
    "inventory_snapshot",
]

SCHEMAS = {
    "orders_detail": {
        "table": "orders_detail",
        "columns": [
            {"name": "order_id",       "type": "BIGINT",   "comment": "Unique order identifier"},
            {"name": "customer_name",  "type": "STRING",   "comment": "Customer full name, may be null"},
            {"name": "region",         "type": "STRING",   "comment": "Delivery region"},
            {"name": "amount",         "type": "DOUBLE",   "comment": "Order amount in CNY"},
            {"name": "status",         "type": "STRING",   "comment": "Order status: active/cancelled/returned"},
        ],
        "partition_columns": [
            {"name": "dt", "type": "STRING", "comment": "Date partition, format yyyy-mm-dd"}
        ],
        "is_partitioned": True,
    },
    "orders_summary": {
        "table": "orders_summary",
        "columns": [
            {"name": "dt",             "type": "STRING",   "comment": "Date"},
            {"name": "region",         "type": "STRING",   "comment": "Region"},
            {"name": "order_count",    "type": "BIGINT",   "comment": "Total orders"},
            {"name": "revenue",        "type": "DOUBLE",   "comment": "Total revenue"},
        ],
        "partition_columns": [],
        "is_partitioned": False,
    },
    "customer_profiles": {
        "table": "customer_profiles",
        "columns": [
            {"name": "customer_id",    "type": "BIGINT",   "comment": ""},
            {"name": "customer_name",  "type": "STRING",   "comment": ""},
            {"name": "segment",        "type": "STRING",   "comment": ""},
            {"name": "signup_date",    "type": "STRING",   "comment": ""},
        ],
        "partition_columns": [
            {"name": "dt", "type": "STRING", "comment": "snapshot date"}
        ],
        "is_partitioned": True,
    },
}

# Mock data for orders_detail on dt='2024-11-01'
ORDERS_DETAIL_DATA = [
    {"order_id": 10001, "customer_name": "Alice Zhang",  "region": "East",  "amount": 299.00,  "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10002, "customer_name": "Bob Li",        "region": "West",  "amount": 155.50,  "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10003, "customer_name": None,            "region": "North", "amount": 88.00,   "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10004, "customer_name": "Carol Wang",    "region": "East",  "amount": 430.00,  "status": "cancelled", "dt": "2024-11-01"},
    {"order_id": 10005, "customer_name": "David Chen",    "region": "South", "amount": 210.00,  "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10006, "customer_name": "Eve Wu",        "region": "East",  "amount": 510.00,  "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10007, "customer_name": None,            "region": "West",  "amount": 75.00,   "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10008, "customer_name": "Frank Sun",     "region": "North", "amount": 320.00,  "status": "returned",  "dt": "2024-11-01"},
    {"order_id": 10009, "customer_name": "Grace Zhao",    "region": "South", "amount": 185.00,  "status": "active",    "dt": "2024-11-01"},
    {"order_id": 10010, "customer_name": "Henry Liu",     "region": "East",  "amount": 640.00,  "status": "active",    "dt": "2024-11-01"},
]

def odps_sql_error(msg):
    print(f"ODPS SQL Error: {msg}", file=sys.stderr)
    sys.exit(2)

def validate_sql_odps(sql):
    """Enforce ODPS SQL dialect rules."""
    sql_upper = sql.upper()
    
    # Check for forbidden standard-SQL patterns
    if re.search(r'\bREGEXP\b', sql_upper):
        odps_sql_error("Unsupported operator REGEXP. Use RLIKE for regex matching in ODPS SQL.")
    
    if re.search(r'\bIFNULL\s*\(', sql_upper):
        odps_sql_error("Function IFNULL is not supported. Use NVL(expr, default) in ODPS SQL.")
    
    if re.search(r'\bCOALESCE\s*\(', sql_upper):
        odps_sql_error("Function COALESCE is not supported in ODPS SQL. Use NVL(expr, default).")
    
    if re.search(r"'[^']*'\s*\|\|\s*'[^']*'", sql) or re.search(r'\w+\s*\|\|\s*\w+', sql):
        odps_sql_error("String concatenation with || is not supported. Use CONCAT(a, b) in ODPS SQL.")
    
    # Check partition filter for orders_detail
    if re.search(r'\borders_detail\b', sql, re.IGNORECASE):
        if not re.search(r'\bdt\s*=\s*[\'"]', sql, re.IGNORECASE):
            odps_sql_error(
                "Table 'orders_detail' is partitioned. A partition filter (WHERE dt = '...') is REQUIRED. "
                "Full table scans are not allowed on partitioned tables."
            )

def execute_query(sql, limit):
    """Execute mock query against in-memory data."""
    validate_sql_odps(sql)
    
    sql_stripped = sql.strip().rstrip(';')
    sql_upper = sql_stripped.upper()
    
    # Only handle queries against orders_detail for this mock
    if not re.search(r'\borders_detail\b', sql_stripped, re.IGNORECASE):
        print(json.dumps({"rows": [], "row_count": 0, "note": "Mock: no data for this table"}))
        return
    
    # Extract dt partition value
    dt_match = re.search(r"dt\s*=\s*['\"](\d{4}-\d{2}-\d{2})['\"]", sql, re.IGNORECASE)
    if not dt_match:
        odps_sql_error("Could not parse partition filter dt='yyyy-mm-dd'.")
    dt_val = dt_match.group(1)
    
    rows = [r for r in ORDERS_DETAIL_DATA if r["dt"] == dt_val]
    
    # Apply status filter if present (active)
    if re.search(r"status\s*=\s*'active'", sql, re.IGNORECASE):
        rows = [r for r in rows if r["status"] == "active"]
    
    # Detect NVL usage on customer_name → replace None with 'Unknown'
    nvl_match = re.search(r'NVL\s*\(\s*customer_name\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)', sql, re.IGNORECASE)
    nvl_default = nvl_match.group(1) if nvl_match else None
    
    # Detect RLIKE pattern on customer_name or region
    rlike_match = re.search(r'(\w+)\s+RLIKE\s+[\'"]([^\'"]+)[\'"]', sql, re.IGNORECASE)
    if rlike_match:
        col = rlike_match.group(1).lower()
        pattern = rlike_match.group(2)
        filtered = []
        for r in rows:
            val = r.get(col, "")
            if val is None:
                val = ""
            if re.search(pattern, val, re.IGNORECASE):
                filtered.append(r)
        rows = filtered
    
    # Detect GROUP BY region → aggregate
    if re.search(r'\bGROUP\s+BY\s+region\b', sql_upper):
        # Count orders per region
        region_counts = {}
        for r in rows:
            region = r["region"]
            cname = r["customer_name"]
            if nvl_default is not None and cname is None:
                cname = nvl_default
            region_counts[region] = region_counts.get(region, 0) + 1
        
        result_rows = [{"region": reg, "order_count": cnt} for reg, cnt in sorted(region_counts.items())]
        result_rows = result_rows[:limit]
        print(json.dumps({"rows": result_rows, "row_count": len(result_rows)}))
        return
    
    # Default: return all columns with NVL applied
    result = []
    for r in rows[:limit]:
        row = dict(r)
        if nvl_default is not None and row["customer_name"] is None:
            row["customer_name"] = nvl_default
        result.append(row)
    
    print(json.dumps({"rows": result, "row_count": len(result)}))


def main():
    parser = argparse.ArgumentParser(description="ODPS Helper CLI (Mock)")
    parser.add_argument("--list-tables", action="store_true")
    parser.add_argument("--pattern", type=str, default=None)
    parser.add_argument("--describe", type=str, default=None, metavar="TABLE_NAME")
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--limit", type=int, default=100)
    
    args = parser.parse_args()
    
    if args.list_tables:
        tables = ALL_TABLES
        if args.pattern:
            tables = [t for t in tables if args.pattern.lower() in t.lower()]
        print(json.dumps({"tables": tables, "count": len(tables)}))
    
    elif args.describe:
        tname = args.describe.lower()
        if tname in SCHEMAS:
            print(json.dumps(SCHEMAS[tname], indent=2))
        else:
            print(json.dumps({"error": f"Table '{args.describe}' not found. Use --list-tables to discover tables."}))
            sys.exit(1)
    
    elif args.query:
        execute_query(args.query, args.limit)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
''')

with open(os.path.join(workspace, "mcp-odps/scripts/odps_helper.py"), "w") as f:
    f.write(odps_helper_script)

os.chmod(os.path.join(workspace, "mcp-odps/scripts/odps_helper.py"), 
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")