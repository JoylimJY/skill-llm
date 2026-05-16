#!/usr/bin/env bash
set -e

chmod +x /workspace/scripts/run.py

# Ensure the expected directory skeleton is present (gen_inputs_script already created it,
# but just in case the container reorders operations)
mkdir -p /workspace/ref/agent-surveys/pdfs
mkdir -p /workspace/ref/agent-surveys/text

echo "[setup] Workspace ready. scripts/run.py is executable."
echo "[setup] ref/agent-surveys/arxiv_ids.txt is intentionally absent — agent must create it."