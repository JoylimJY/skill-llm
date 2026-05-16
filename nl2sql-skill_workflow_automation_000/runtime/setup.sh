#!/usr/bin/env bash
set -e

echo "=== Setting up NL2SQL task environment ==="

# Verify the database is intact
sqlite3 /workspace/data/ecommerce.db "SELECT COUNT(*) FROM orders;" > /dev/null
echo "Database check: OK ($(sqlite3 /workspace/data/ecommerce.db 'SELECT COUNT(*) FROM orders;') orders)"

# Make all scripts in scripts/ executable
find /workspace/scripts -name "*.py" -exec chmod +x {} \;
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Create a small helper that agents can call to execute SQL against the DB
# This simulates the execute_sql / get_table_schema tools described in the skill
cat > /workspace/scripts/execute_sql.py << 'PYEOF'
#!/usr/bin/env python3
"""
Utility: execute a SQL query against data/ecommerce.db and print results as JSON.
Usage: python scripts/execute_sql.py "<SQL query>"
"""
import sys, sqlite3, json
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "ecommerce.db"

if len(sys.argv) < 2:
    print(json.dumps({"error": "No SQL provided"}))
    sys.exit(1)

sql = sys.argv[1]
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    print(json.dumps({"rows": rows, "count": len(rows)}, ensure_ascii=False, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
PYEOF
chmod +x /workspace/scripts/execute_sql.py

cat > /workspace/scripts/get_table_schema.py << 'PYEOF'
#!/usr/bin/env python3
"""
Utility: show schema + first 5 rows of a table.
Usage: python scripts/get_table_schema.py <table_name>
"""
import sys, sqlite3, json
from pathlib import Path

db_path = Path(__file__).parent.parent / "data" / "ecommerce.db"

if len(sys.argv) < 2:
    print(json.dumps({"error": "No table name provided"}))
    sys.exit(1)

table = sys.argv[1]
try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [dict(r) for r in cur.fetchall()]
    cur.execute(f"SELECT * FROM {table} LIMIT 5")
    sample = [dict(r) for r in cur.fetchall()]
    conn.close()
    print(json.dumps({"table": table, "columns": cols, "sample_rows": sample}, ensure_ascii=False, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}))
    sys.exit(1)
PYEOF
chmod +x /workspace/scripts/get_table_schema.py

echo "=== Setup complete ==="
echo "Available tools:"
echo "  python scripts/execute_sql.py '<SQL>'"
echo "  python scripts/get_table_schema.py <table_name>"