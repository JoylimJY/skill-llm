#!/bin/bash
set -e

# Ensure workspace permissions
chmod -R 755 /workspace

# Ensure ~/.solo-factory does NOT pre-exist (clean state for the org-level config)
rm -rf ~/.solo-factory

# Ensure the stacks templates are executable-friendly
chmod -R 644 /workspace/solo-factory/templates/stacks/*.yaml 2>/dev/null || true

echo "Setup complete. Workspace is ready."
echo "Founder answers: /workspace/founder_answers.md"
echo "SKILL.md: /workspace/SKILL.md"
echo "Generation rules: /workspace/solo-factory/references/generation-rules.md"