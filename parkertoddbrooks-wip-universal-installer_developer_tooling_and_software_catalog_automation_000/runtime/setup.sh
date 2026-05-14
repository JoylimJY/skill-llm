#!/usr/bin/env bash
set -e

echo "=== Setting up wip-universal-installer environment ==="

# Initialize git in the candidate repo (wip-install may require it)
cd /workspace/candidate-tool
git init --quiet
git config user.email "platform@acme.internal"
git config user.name "Acme Platform CI"
git add -A
git commit -m "Initial commit" --quiet || true

# Initialize git in distractor repos too
for repo in legacy-auth-service data-pipeline-v2 frontend-dashboard infra-terraform-modules ml-feature-store; do
  cd /workspace/$repo
  git init --quiet
  git config user.email "platform@acme.internal"
  git config user.name "Acme Platform CI"
  git add -A
  git commit -m "Initial commit" --quiet || true
done

cd /workspace

# Verify wip-install is available; if npm global install failed, try installing it now
if ! command -v wip-install &>/dev/null; then
  echo "wip-install not found globally, attempting install..."
  npm install -g @wipcomputer/universal-installer --registry https://registry.npmjs.org 2>/dev/null || true
fi

# Find where universal-installer was installed for module access
WIP_MODULE_PATH=$(npm root -g)/@wipcomputer/universal-installer
echo "WIP module path: $WIP_MODULE_PATH"

# Make detect.mjs accessible at /workspace/detect.mjs if available
if [ -f "$WIP_MODULE_PATH/detect.mjs" ]; then
  ln -sf "$WIP_MODULE_PATH/detect.mjs" /workspace/detect.mjs
  echo "detect.mjs linked to /workspace/detect.mjs"
else
  echo "detect.mjs not found at expected path, agent must locate it"
fi

# Print installed version info
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"
echo "git version: $(git --version)"

if command -v wip-install &>/dev/null; then
  echo "wip-install version: $(wip-install --version 2>/dev/null || echo 'unknown')"
else
  echo "WARNING: wip-install not in PATH"
fi

echo "=== Setup complete ==="