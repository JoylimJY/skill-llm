#!/bin/bash
set -e

chmod -R 755 /workspace
echo "Workspace permissions set."

# Verify key input files exist
for f in \
  "/workspace/hr_cases/li_wei/employee_profile.json" \
  "/workspace/hr_cases/li_wei/attendance_march_2026.json" \
  "/workspace/hr_cases/li_wei/expense_claims_march_2026.json"; do
  if [ ! -f "$f" ]; then
    echo "ERROR: Missing file: $f"
    exit 1
  fi
done
echo "All required input files present. Sandbox ready."