#!/bin/bash
set -e

chmod +x /workspace/scripts/migration/stripe_v3_migrate.sh
chmod +x /workspace/scripts/rollback/rollback_payment.sh

echo "Workspace ready. Key input file: /workspace/docs/refactor_raw_notes.txt"
echo "Distractor files and legacy artifacts are in place."
tree /workspace --dirsfirst -L 4 2>/dev/null || find /workspace -type f | sort