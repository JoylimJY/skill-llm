#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/workspace"

echo "[setup] Setting correct permissions on all scripts..."
find "$WORKSPACE/scripts" -name "*.sh" -exec chmod +x {} \;

echo "[setup] Verifying jq is available..."
jq --version

echo "[setup] Verifying workspace structure..."
ls -la "$WORKSPACE/scripts/"

echo "[setup] Confirming checklist.md does NOT exist (agent must create it)..."
if [ -f "$WORKSPACE/checklist.md" ]; then
    echo "[setup] WARNING: checklist.md already exists — removing it."
    rm "$WORKSPACE/checklist.md"
fi

echo "[setup] Confirming .claude-status.txt does NOT exist..."
if [ -f "$WORKSPACE/.claude-status.txt" ]; then
    echo "[setup] WARNING: .claude-status.txt already exists — removing it."
    rm "$WORKSPACE/.claude-status.txt"
fi

echo "[setup] Confirming .claude/fullrun does NOT exist..."
if [ -d "$WORKSPACE/.claude/fullrun" ]; then
    echo "[setup] WARNING: .claude/fullrun already exists — removing it."
    rm -rf "$WORKSPACE/.claude/fullrun"
fi

echo "[setup] Setup complete. Workspace is ready for agent."