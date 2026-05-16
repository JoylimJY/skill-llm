#!/usr/bin/env bash
set -e

# Ensure data directory permissions
chmod -R 755 /workspace/data
chmod -R 755 /workspace/tmp

# Confirm the key files are in place
echo "=== Setup Check ==="
ls -la /workspace/data/fitness.json
ls -la /workspace/tmp/raw_session_notes.txt
echo "=== fitness.json initial state ==="
cat /workspace/data/fitness.json
echo "=== raw_session_notes.txt ==="
cat /workspace/tmp/raw_session_notes.txt
echo "=== Setup complete ==="