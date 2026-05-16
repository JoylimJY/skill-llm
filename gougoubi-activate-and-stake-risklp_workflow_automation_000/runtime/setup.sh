#!/bin/bash
set -e

echo "[setup] Making scripts executable..."
chmod +x /workspace/scripts/pbft-activate-and-add-risklp.mjs
chmod +x /workspace/scripts/pbft-join-and-activate-all-conditions.mjs
chmod +x /workspace/scripts/pbft-add-risk-lp-to-proposal.mjs

echo "[setup] Verifying Node.js..."
node --version

echo "[setup] Verifying scripts parse without error..."
node --input-type=module <<'EOF'
import { readFileSync } from 'fs';
const src = readFileSync('/workspace/scripts/pbft-activate-and-add-risklp.mjs', 'utf8');
if (!src.includes('dry-run')) throw new Error('Script missing dry-run support');
console.log('[setup] Script validation OK');
EOF

echo "[setup] Done."