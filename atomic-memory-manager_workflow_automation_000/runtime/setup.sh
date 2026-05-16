#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/run_nextflow.sh 2>/dev/null || true

# Create a simple memory_search stub that agents can call
cat > /usr/local/bin/memory_search << 'EOF'
#!/bin/bash
# memory_search: search workspace memory files for a query
# Usage: memory_search "tight specific query"
QUERY="$*"
WORKSPACE="${MEMORY_WORKSPACE:-/workspace}"
echo "=== memory_search: '$QUERY' ==="
grep -rn --include="*.md" -i "$QUERY" "$WORKSPACE/MEMORY.md" "$WORKSPACE/memory/" 2>/dev/null || echo "(no results)"
EOF
chmod +x /usr/local/bin/memory_search

# Create a memory_get stub that reads specific line ranges
cat > /usr/local/bin/memory_get << 'EOF'
#!/bin/bash
# memory_get: read exact lines from a memory file
# Usage: memory_get <filepath> [start_line] [end_line]
FILE="$1"
START="${2:-1}"
END="${3:-999999}"
if [ -z "$FILE" ]; then
  echo "Usage: memory_get <filepath> [start_line] [end_line]"
  exit 1
fi
echo "=== memory_get: $FILE lines $START-$END ==="
sed -n "${START},${END}p" "$FILE" 2>/dev/null || echo "(file not found or empty range)"
EOF
chmod +x /usr/local/bin/memory_get

echo "Setup complete. memory_search and memory_get are available."