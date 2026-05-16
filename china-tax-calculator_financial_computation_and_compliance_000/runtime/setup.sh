#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying input file exists..."
ls -la /workspace/hr_system/payroll/2025/employees_yearend_2025.csv

echo "Setup complete."