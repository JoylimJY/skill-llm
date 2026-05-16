#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/projects/investment-post-management-report-updater/scripts/parse_financial_data.py
chmod +x /workspace/projects/investment-post-management-report-updater/scripts/parse_docx.py
chmod +x /workspace/projects/investment-post-management-report-updater/scripts/generate_report.py

echo "Setup complete. Scripts are executable."
echo "Workspace contents:"
find /workspace -type f | sort