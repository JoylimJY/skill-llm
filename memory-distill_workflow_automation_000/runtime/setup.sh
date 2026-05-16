#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace
chmod 644 /workspace/raw_conversation.txt
chmod 644 /workspace/MEMORY.md

echo "Workspace ready."
echo "Current memory directory contents:"
ls -la /workspace/memory/
echo ""
echo "Today's date: $(date +%Y-%m-%d)"