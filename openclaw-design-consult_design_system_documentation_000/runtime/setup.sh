#!/bin/bash
set -e

echo "RiskLens Pro sandbox initialized."
echo "Workspace contents:"
ls /workspace/
echo ""
echo "CLAUDE.md exists:"
cat /workspace/CLAUDE.md | head -5
echo ""
echo "DESIGN.md status:"
ls /workspace/DESIGN.md 2>/dev/null && echo "EXISTS (unexpected)" || echo "NOT FOUND (expected)"