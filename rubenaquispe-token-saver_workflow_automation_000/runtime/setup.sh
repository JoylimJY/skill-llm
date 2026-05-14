#!/usr/bin/env bash
set -e

echo "=== Token Saver v3 Sandbox Setup ==="

# Make the optimize script executable
chmod +x /workspace/scripts/optimize.py

# Create a convenience wrapper so the agent can call `optimize` directly
cat > /usr/local/bin/optimize << 'EOF'
#!/usr/bin/env bash
exec python3 /workspace/scripts/optimize.py optimize "$@"
EOF
chmod +x /usr/local/bin/optimize

# Ensure the ~/.openclaw directory exists (but NOT the openclaw.json config)
mkdir -p ~/.openclaw

# Ensure workspace .openclaw dir exists
mkdir -p /workspace/.openclaw

# Verify the model registry is accessible
if [ -f /workspace/scripts/models.json ]; then
    echo "✓ Model registry found: $(python3 -c "import json; d=json.load(open('/workspace/scripts/models.json')); print(len(d['models']), 'models registered')")"
else
    echo "✗ ERROR: Model registry missing!"
    exit 1
fi

# Verify workspace files exist
for f in SOUL.md AGENTS.md USER.md MEMORY.md PROJECTS.md; do
    if [ -f "/workspace/$f" ]; then
        echo "✓ $f present"
    else
        echo "✗ MISSING: $f"
    fi
done

# Confirm no openclaw.json exists yet (agent must set this up)
if [ -f ~/.openclaw/openclaw.json ]; then
    echo "WARNING: openclaw.json already exists - removing for clean test"
    rm ~/.openclaw/openclaw.json
fi

echo ""
echo "=== Setup Complete ==="
echo "Agent task: Configure Gemini 2.5 Pro as the active model, apply conservative"
echo "compaction preset, run workspace compression, and save report to optimization_report.json"
echo ""
echo "SKILL.md is available at: /workspace/SKILL.md"
echo "Optimize tool: 'optimize <subcommand>' or 'python3 /workspace/scripts/optimize.py optimize <subcommand>'"