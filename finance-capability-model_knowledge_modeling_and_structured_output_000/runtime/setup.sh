#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying problem file exists..."
ls /workspace/hr/recruitment/2024/finance/finance_talent_initiative_memo.txt

echo "Setup complete."