#!/bin/bash
set -e

echo "Setting up sandbox environment..."

# Ensure workspace permissions are correct
chmod -R 755 /workspace/.openclaw

# Verify the keyword-templates.json was created
if [ -f "/workspace/.openclaw/workspace/skills/news-source-manager/references/keyword-templates.json" ]; then
    echo "✅ keyword-templates.json found"
else
    echo "❌ keyword-templates.json missing - gen_inputs_script may have failed"
    exit 1
fi

# Confirm news-sources.json does NOT exist (agent must create it)
if [ -f "/workspace/.openclaw/workspace/memory/news-sources.json" ]; then
    echo "❌ news-sources.json already exists - this is a problem"
    exit 1
else
    echo "✅ news-sources.json does not exist (correct starting state)"
fi

echo "Sandbox setup complete."