#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying contract draft exists..."
if [ -f "/workspace/hr_department/contracts/drafts/labor_contract_zhao_ming_draft.docx" ]; then
    echo "Contract draft found. Setup complete."
else
    echo "ERROR: Contract draft not found!"
    exit 1
fi

echo "Setup complete."