#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying input files exist..."
test -f /workspace/accounting/2025/Q1/transactions_q1_2025.csv && echo "OK: transactions CSV found"
test -f /workspace/accounting/2025/Q1/company_details.json && echo "OK: company_details found"
test -f /workspace/accounting/2025/Q1/tax_settings.json && echo "OK: tax_settings found"
test -f /workspace/accounting/2025/Q1/skr04_reference.json && echo "OK: skr04_reference found"

echo "Setup complete."