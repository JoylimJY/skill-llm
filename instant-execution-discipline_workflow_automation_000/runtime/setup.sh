#!/usr/bin/env bash
set -e

# Print today and yesterday dates for agent context
echo "=== Environment Ready ==="
echo "Today: $(date +%Y-%m-%d)"
echo "Yesterday: $(date -d 'yesterday' +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null || python3 -c 'from datetime import date, timedelta; print((date.today()-timedelta(1)).isoformat())')"
echo "Workspace: /workspace"
echo "Incident report: /workspace/ops/logs/distribution_incident_raw.txt"
echo "========================="

chmod -R 755 /workspace