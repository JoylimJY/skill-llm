#!/bin/bash
set -e

# Ensure workspace permissions are sane
chmod -R 755 /workspace

echo "Workspace ready. Node version: $(node --version)"
echo "Scenario spec at: /workspace/scripts/bench/cache_scenarios.json"
echo "SmartCache module at: /workspace/lib/adapters/smart_cache.js"