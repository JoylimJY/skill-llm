#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace

echo "=== Setting up claw-esp-expert sandbox ==="

# Run the workspace generator
python3 /dev/stdin << 'PYEOF'
import subprocess, sys
result = subprocess.run([sys.executable, '/workspace/../gen_inputs.py'], capture_output=True, text=True)
print(result.stdout)
print(result.stderr)
PYEOF

# Make scripts executable
chmod +x "${WORKSPACE}/scripts/run-tool.mjs"
chmod +x "${WORKSPACE}/bin/idf.py"

# The run-tool.mjs uses require() style (CommonJS), ensure node can run it
# Patch the shebang and module style check
head -1 "${WORKSPACE}/scripts/run-tool.mjs"

# Set environment variables that the tool runner expects
export IDF_PATH="${WORKSPACE}/esp-idf"
export PATH="${WORKSPACE}/bin:${PATH}"

# Verify node can parse the tool runner
node --check "${WORKSPACE}/scripts/run-tool.mjs" 2>/dev/null || true

# Smoke test: manage_env check
echo "--- Smoke test: manage_env ---"
cd "${WORKSPACE}"
printf '%s' '{"action":"check"}' | IDF_PATH="${WORKSPACE}/esp-idf" node scripts/run-tool.mjs manage_env --stdin || true

echo "--- Smoke test: explore_demo gpio ---"
printf '%s' '{"query":"gpio"}' | IDF_PATH="${WORKSPACE}/esp-idf" node scripts/run-tool.mjs explore_demo --stdin || true

echo "=== Setup complete ==="
echo "Workspace: ${WORKSPACE}"
echo "IDF_PATH: ${WORKSPACE}/esp-idf"
echo "Project: ${WORKSPACE}/sensor_project"