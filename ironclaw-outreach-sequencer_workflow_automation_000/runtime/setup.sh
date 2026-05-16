#!/usr/bin/env bash
set -e

echo "=== Setting up outreach sequencer sandbox ==="

# Ensure workspace permissions
chmod -R 755 "${WORKSPACE:-/workspace}"

# Verify DuckDB is accessible
python3 -c "
import duckdb, os
db_path = os.path.join(os.environ.get('WORKSPACE', '/workspace'), 'crm/leads.db')
con = duckdb.connect(db_path)
count = con.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
print(f'DuckDB ready: {count} leads loaded')
con.close()
"

echo "=== Sandbox ready ==="