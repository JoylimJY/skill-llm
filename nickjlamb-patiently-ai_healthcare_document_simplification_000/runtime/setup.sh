#!/usr/bin/env bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
test -f /workspace/patient_portal/incoming/letter_P247_20241114.txt \
    && echo "  ✓ Clinical letter found" \
    || echo "  ✗ Clinical letter MISSING"

test -f /workspace/patient_portal/config/patient_P247_preferences.cfg \
    && echo "  ✓ Preferences config found" \
    || echo "  ✗ Preferences config MISSING"

echo "Setup complete."