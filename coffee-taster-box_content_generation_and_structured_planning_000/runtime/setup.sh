#!/usr/bin/env bash
set -e

echo "[setup] Setting permissions on workspace..."
chmod -R 755 /workspace

echo "[setup] Verifying key files exist..."
test -f /workspace/SKILL.md && echo "  ✓ SKILL.md present"
test -f /workspace/references/taster_gifts_guide.md && echo "  ✓ references/taster_gifts_guide.md present"
test -f /workspace/data/subscribers/export_2024_q1.csv && echo "  ✓ subscriber data present"
test -f /workspace/config/shopify_settings_stub.yaml && echo "  ✓ shopify config present"

echo "[setup] Environment ready."