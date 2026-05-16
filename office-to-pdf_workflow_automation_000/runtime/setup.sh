#!/bin/bash
set -e

# Ensure the output directory exists and is writable
mkdir -p /workspace/output/pdf_archive
chmod 755 /workspace/output/pdf_archive

# Pre-warm LibreOffice user profile to avoid first-run delays
libreoffice --headless --norestore --convert-to pdf /dev/null --outdir /tmp/ 2>/dev/null || true

echo "Setup complete. Workspace ready."
ls -la /workspace/