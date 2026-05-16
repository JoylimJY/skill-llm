#!/bin/bash
set -euo pipefail

chmod +x /workspace/memlog.sh
chmod +x /workspace/memory-gc.sh

# Create required memory subdirectories per SKILL.md architecture
mkdir -p /workspace/memory/short-term
mkdir -p /workspace/memory/semantic
mkdir -p /workspace/memory/confidence
mkdir -p /workspace/reflections
mkdir -p /workspace/tasks
mkdir -p /workspace/emotions
mkdir -p /workspace/knowledge
mkdir -p /workspace/privacy
mkdir -p /workspace/explainability
mkdir -p /workspace/elastic
mkdir -p /workspace/evolution
mkdir -p /workspace/collaboration

echo "[setup] Workspace ready."
ls /workspace/