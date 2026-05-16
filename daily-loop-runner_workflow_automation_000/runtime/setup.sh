#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Verify input files exist
echo "=== Verifying input files ==="
for f in \
    /workspace/task.json \
    /workspace/inputs/project_card_alpha.json \
    /workspace/inputs/weekly_review_alpha.json \
    /workspace/inputs/daily_logs_alpha.json \
    /workspace/inputs/open_questions_alpha.json \
    /workspace/inputs/forced_bottleneck_alpha.txt \
    /workspace/inputs/project_card_beta.json \
    /workspace/inputs/weekly_review_beta.json \
    /workspace/inputs/daily_logs_beta.json \
    /workspace/inputs/open_questions_beta.json; do
    if [ -f "$f" ]; then
        echo "  OK: $f"
    else
        echo "  MISSING: $f"
        exit 1
    fi
done

# Create outputs directory if not present
mkdir -p /workspace/outputs

echo "=== Setup complete ==="