#!/bin/bash
set -e

# Make scripts executable
chmod +x /workspace/scripts/deploy.sh 2>/dev/null || true

# Simulate a developer "accidentally" modifying a migration file AFTER
# the agent should have taken the initial snapshot.
# We do this via a marker file — the agent must compute hashes BEFORE this runs,
# but we can't control agent timing. Instead, we'll modify the file AFTER
# the setup phase. We plant a "tamper script" the agent should NOT run.
# The actual tamper is applied by the eval script reading .eval_hashes.json.
#
# For the agent's task: the agent will hash files, then we tamper one file,
# and the agent must detect the mismatch via /cv verify.
#
# We create a clearly named tamper script the task prompt tells the agent to run
# after taking the initial snapshot, simulating a developer's accidental edit.

cat > /workspace/scripts/simulate_drift.sh << 'TAMPEREOF'
#!/bin/bash
# Simulates a developer accidentally modifying a migration file
# Run this AFTER taking your pre-refactor snapshot
cat >> /workspace/db/migrations/002_create_transactions.sql << 'SQL'

-- HOTFIX: Added missing index (unapproved change)
CREATE INDEX idx_transactions_account ON transactions(account_id);
SQL
echo "Drift simulated: db/migrations/002_create_transactions.sql has been modified."
TAMPEREOF

chmod +x /workspace/scripts/simulate_drift.sh

echo "Setup complete. Workspace ready."
ls -la /workspace/