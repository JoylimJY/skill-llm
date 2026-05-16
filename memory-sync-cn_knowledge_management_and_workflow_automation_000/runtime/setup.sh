#!/bin/bash
set -e

echo "=== Setting up CortexGraph environment ==="

# Create config directory
mkdir -p ~/.config/cortexgraph/jsonl

# Write the cortexgraph config
cat > ~/.config/cortexgraph/.env << 'EOF'
CORTEXGRAPH_STORAGE_PATH=~/.config/cortexgraph/jsonl
CORTEXGRAPH_DECAY_MODEL=power_law
CORTEXGRAPH_PL_HALFLIFE_DAYS=3.0
CORTEXGRAPH_FORGET_THRESHOLD=0.05
CORTEXGRAPH_PROMOTE_THRESHOLD=0.65
EOF

# Configure mcporter to know about cortexgraph
mkdir -p ~/.openclaw/workspace/config

CORTEXGRAPH_BIN=$(which cortexgraph)
cat > ~/.openclaw/workspace/config/mcporter.json << EOF
{
  "cortexgraph": {
    "command": "${CORTEXGRAPH_BIN}",
    "description": "Temporal memory system for AI with Ebbinghaus forgetting curve"
  }
}
EOF

echo "mcporter.json written with cortexgraph path: ${CORTEXGRAPH_BIN}"

# Verify tools are available
echo "=== Verifying tool availability ==="
cortexgraph --help > /dev/null 2>&1 && echo "✓ cortexgraph OK" || echo "✗ cortexgraph FAILED"
mcporter --help > /dev/null 2>&1 && echo "✓ mcporter OK" || echo "✗ mcporter FAILED"

# Test that mcporter can call cortexgraph
echo "=== Testing mcporter <-> cortexgraph link ==="
mcporter call cortexgraph.read_graph limit=1 2>&1 | head -5 || true

echo "=== Setup complete ==="