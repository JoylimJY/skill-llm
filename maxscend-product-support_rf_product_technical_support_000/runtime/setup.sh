#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying key input files exist..."
test -f /workspace/project/system/specs/rx_chain_requirements.csv && echo "  [OK] requirements CSV"
test -f /workspace/project/rf_design/test_data/proto_v2_test_log.txt && echo "  [OK] test log"
test -f /workspace/project/vendor_docs/internal/maxscend_intro.txt && echo "  [OK] vendor notes"

echo "Setup complete."