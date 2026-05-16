#!/usr/bin/env bash
set -e

echo "🔧 Setting up sandbox environment..."

chmod +x /workspace/scripts/init-artifact.sh
chmod +x /workspace/scripts/bundle-artifact.sh

# Fix syntax error in gen_inputs_script (the f-string issue is only in gen_inputs; actual files are already written)
# Verify scripts exist
ls -la /workspace/scripts/

echo "✅ Setup complete."