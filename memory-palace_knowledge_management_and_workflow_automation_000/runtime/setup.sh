#!/bin/bash
set -e

echo "=== Setting up Memory Palace environment ==="

# Ensure npm global packages are in PATH
export PATH="$(npm root -g)/.bin:$PATH"

# Try to install memory-palace if not already available
if ! npx memory-palace:memory_palace_stats 2>/dev/null | grep -q "total" 2>/dev/null; then
    echo "Installing memory-palace..."
    npm install -g memory-palace@1.6.5 2>/dev/null || true
fi

# Create a wrapper script that makes memory-palace commands easily callable
cat > /usr/local/bin/mp << 'WRAPPER'
#!/bin/bash
npx memory-palace:"$@"
WRAPPER
chmod +x /usr/local/bin/mp

# Set the memory palace data directory to workspace
export MEMORY_PALACE_DATA_DIR="/data/agent-memory-palace"
mkdir -p "$MEMORY_PALACE_DATA_DIR"

# Persist environment variable for agent sessions
echo "export MEMORY_PALACE_DATA_DIR=/data/agent-memory-palace" >> /etc/environment
echo "export MEMORY_PALACE_DATA_DIR=/data/agent-memory-palace" >> /root/.bashrc
echo "export PATH=$(npm root -g)/.bin:$PATH" >> /root/.bashrc

# Test that memory-palace is functional
echo "Testing memory-palace installation..."
TEST_RESULT=$(npx memory-palace:memory_palace_stats 2>&1 || true)
echo "memory-palace test result: $TEST_RESULT"

echo "=== Setup complete ==="