#!/bin/bash
set -e

# Make workspace writable
chmod -R 755 /workspace

# Ensure openssl is available (needed for integrity signature)
which openssl || (echo "ERROR: openssl not found" && exit 1)
which jq || (echo "ERROR: jq not found" && exit 1)
which python3 || (echo "ERROR: python3 not found" && exit 1)

echo "AgentBench sandbox ready."
echo "Skill dir: /workspace/agentbench-skill"
echo "Tasks available:"
find /workspace/agentbench-skill/tasks -name "task.yaml" | sort | while read f; do
    suite=$(python3 -c "import yaml; d=yaml.safe_load(open('$f')); print(d['suite']+'/'+d['id']+' ['+d['difficulty']+']')")
    echo "  $suite"
done