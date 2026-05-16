#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"

echo "[setup] Making OpenClaw scripts executable..."
chmod +x "$WORKSPACE/openclaw-backup/scripts/backup.sh"
chmod +x "$WORKSPACE/openclaw-backup/scripts/verify.sh"
chmod +x "$WORKSPACE/openclaw-backup/scripts/restore.sh"
chmod +x "$WORKSPACE/openclaw-backup/scripts/push-to-github.sh"

chmod +x "$WORKSPACE/order-routing-agent/scripts/rebalance.sh"
chmod +x "$WORKSPACE/order-routing-agent/scripts/risk-check.sh"
chmod +x "$WORKSPACE/order-routing-agent/scripts/startup.sh"

echo "[setup] Generating fresh age keypair for this sandbox..."
AGE_IDENTITY_FILE="$WORKSPACE/age-identity.txt"
AGE_PUBKEY_FILE="$WORKSPACE/age-pubkey.txt"

# Remove placeholder files created by gen_inputs.py before generating
rm -f "$AGE_IDENTITY_FILE" "$AGE_PUBKEY_FILE"

# Generate keypair
age-keygen -o "$AGE_IDENTITY_FILE"
# Extract public key from the generated identity file
PUBKEY="$(grep '^# public key:' "$AGE_IDENTITY_FILE" | awk '{print $NF}')"
echo "$PUBKEY" > "$AGE_PUBKEY_FILE"

echo "[setup] Age public key: $PUBKEY"
echo "[setup] Age identity:   $AGE_IDENTITY_FILE"
echo "[setup] Age pubkey:     $AGE_PUBKEY_FILE"

# Create a backups output directory
mkdir -p "$WORKSPACE/backups"

echo "[setup] Setup complete."
echo ""
echo "=== TASK CONTEXT FOR AGENT ==="
echo "OpenClaw skill base:       $WORKSPACE/openclaw-backup"
echo "Agent workspace to backup: $WORKSPACE/order-routing-agent"
echo "Age public key file:       $WORKSPACE/age-pubkey.txt"
echo "Output backups directory:  $WORKSPACE/backups"
echo "==========================="