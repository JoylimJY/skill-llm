#!/bin/bash
set -e

# Ensure memory-indexer directory exists
if [ ! -d /opt/memory-indexer ]; then
    echo "Warning: /opt/memory-indexer not found, creating empty directory."
    mkdir -p /opt/memory-indexer
fi

# Initialize the data directory
cd /opt/memory-indexer
python3 memory-indexer.py status 2>/dev/null || true

# Make sure jieba dictionary is pre-downloaded (avoids network calls during test)
python3 -c "import jieba; jieba.initialize()" 2>/dev/null || true

# Create a convenience symlink so agent can call it from workspace
ln -sf /opt/memory-indexer/memory-indexer.py /usr/local/bin/memory-indexer.py 2>/dev/null || true

# Ensure workspace permissions
chmod -R 755 /workspace

echo "Setup complete. memory-indexer is ready at /opt/memory-indexer/"
echo "Usage: python3 /opt/memory-indexer/memory-indexer.py <command>"