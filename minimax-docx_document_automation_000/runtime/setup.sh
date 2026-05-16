#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${1:-/workspace}"
SKILL_PATH="$WORKSPACE/skill/minimax-docx"

echo "=== Setting up minimax-docx sandbox ==="

# Permissions
chmod +x "$SKILL_PATH/docx_engine.py"

# Verify Python
python3 --version

# Verify .NET
dotnet --version || echo "WARNING: .NET not yet available"

# Pre-restore NuGet packages for DocForge so the agent doesn't need internet during dotnet run
echo "=== Pre-restoring DocForge NuGet packages ==="
cd "$SKILL_PATH/src"
dotnet restore DocForge.csproj \
    --source https://api.nuget.org/v3/index.json \
    || echo "WARNING: NuGet restore failed — agent will need to restore at runtime"

echo "=== Setup complete ==="
echo "Skill path: $SKILL_PATH"
echo "Template: $WORKSPACE/project/quarterly_reports/Q4_2024/compliance_template.docx"