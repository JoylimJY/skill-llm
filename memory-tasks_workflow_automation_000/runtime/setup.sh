#!/usr/bin/env bash
set -e

WORKSPACE=/workspace

# ── Initialize Basic Memory project ──────────────────────────────────────────
cd "$WORKSPACE"

# Configure basic-memory to use the workspace as its project root
mkdir -p ~/.basic-memory

cat > ~/.basic-memory/config.json << 'EOF'
{
  "projects": {
    "default": {
      "path": "/workspace/memory",
      "name": "drug-discovery"
    }
  },
  "default_project": "default"
}
EOF

# Initialize the basic-memory database for the workspace
cd "$WORKSPACE"
memory init --path /workspace/memory --name drug-discovery 2>/dev/null || true

# Ensure memory CLI is accessible
which memory || echo "WARNING: memory CLI not found on PATH"

# Remove the WRONG_EXAMPLE to avoid it polluting search results during eval
# (keep it as a distractor for the agent, but make it clear via filename)
# Actually keep it — it's a deliberate trap

echo "Basic Memory environment initialized."
echo "Project root: /workspace/memory"
echo ""
echo "Work briefs available in /workspace/pipeline/stages/"
echo "Three research tasks require structured tracking setup."