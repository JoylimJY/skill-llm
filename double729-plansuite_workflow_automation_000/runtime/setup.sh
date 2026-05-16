#!/bin/bash
set -e

# Make ETL and validation scripts executable
chmod +x /workspace/scripts/etl/extract_legacy.py
chmod +x /workspace/scripts/validation/row_count_check.sh

# Verify template files exist (sanity check)
for f in task_plan.md progress.md findings.md; do
    if [ ! -f "/workspace/templates/$f" ]; then
        echo "ERROR: Missing template file: templates/$f"
        exit 1
    fi
done

echo "Setup complete. Workspace ready."
echo "Template files verified."
tree /workspace --dirsfirst 2>/dev/null || find /workspace -type f | sort