#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_DIR="${WORKSPACE_DIR:-/workspace}"

echo "=== Setting up context-cleanup sandbox ==="

# Ensure cleanup.sh is executable
chmod +x "${WORKSPACE_DIR}/skills/context-cleanup/cleanup.sh"

# Create .openclaw dir with correct permissions
mkdir -p "${WORKSPACE_DIR}/.openclaw"
chmod 755 "${WORKSPACE_DIR}/.openclaw"

# Ensure archive directory is ready
mkdir -p "${WORKSPACE_DIR}/memory/archive"
mkdir -p "${WORKSPACE_DIR}/memory/sessions"

echo "=== Sandbox ready ==="
echo "Workspace: ${WORKSPACE_DIR}"
echo "Memory sessions:"
ls -la "${WORKSPACE_DIR}/memory/sessions/" 2>/dev/null || echo "(empty)"
echo "SKILL.md location: ${WORKSPACE_DIR}/skills/context-cleanup/SKILL.md"