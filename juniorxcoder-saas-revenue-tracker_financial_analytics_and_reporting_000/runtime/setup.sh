#!/bin/bash
set -e

chmod +x /workspace/scripts/utils/export_helper.sh 2>/dev/null || true

echo "Workspace initialized. Raw data files are in /workspace/data/raw_exports/"
echo "Agent task: Produce revenue_intelligence_report.json in the workspace."