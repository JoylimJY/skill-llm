#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure md2pdf.sh is executable
chmod +x "$WORKSPACE/skills/md-to-pdf/scripts/md2pdf.sh"

# Patch md2pdf.sh to use xvfb-run for headless wkhtmltopdf
sed -i 's|wkhtmltopdf \\|xvfb-run -a --server-args="-screen 0 1024x768x24" wkhtmltopdf \\|g' \
    "$WORKSPACE/skills/md-to-pdf/scripts/md2pdf.sh"

echo "Setup complete."
echo "Skill script: $WORKSPACE/skills/md-to-pdf/scripts/md2pdf.sh"
echo "Reports dir:  $WORKSPACE/institute/reports/q3_2024/"