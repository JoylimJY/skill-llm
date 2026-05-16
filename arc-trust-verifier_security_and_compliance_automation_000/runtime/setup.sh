#!/bin/bash
set -e

# Make trust_verifier.py executable
chmod +x /workspace/openclaw/scripts/trust_verifier.py

# Make CI scripts executable (distractors)
chmod +x /workspace/ci/lint.sh /workspace/scripts/deploy.sh 2>/dev/null || true

echo "Setup complete. Workspace ready."
echo "Skill to audit: /workspace/skills/payment-processor-skill/"
echo "Trust verifier: /workspace/openclaw/scripts/trust_verifier.py"