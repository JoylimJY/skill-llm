#!/usr/bin/env bash
set -euo pipefail

# Create a stub 'ralph' CLI that appends emitted events to a log file
cat > /usr/local/bin/ralph << 'EOF'
#!/usr/bin/env bash
# Minimal ralph stub: records "ralph emit" calls to /workspace/.ralph_events.log
if [[ "${1:-}" == "emit" ]]; then
    EVENT_NAME="${2:-}"
    EVENT_BODY="${3:-}"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${TIMESTAMP} | ${EVENT_NAME} | ${EVENT_BODY}" >> /workspace/.ralph_events.log
    echo "Event emitted: ${EVENT_NAME}"
else
    echo "ralph: unknown command '${1:-}'" >&2
    exit 1
fi
EOF
chmod +x /usr/local/bin/ralph

# Ensure the workspace Rust project can resolve dependencies offline-ish
cd /workspace
cargo fetch 2>/dev/null || true

echo "Setup complete."