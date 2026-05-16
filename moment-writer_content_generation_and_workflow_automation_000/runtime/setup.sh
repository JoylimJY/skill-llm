#!/bin/bash
set -e

cd /workspace
chmod -R 755 /workspace

echo "Workspace ready. Directory structure:"
find /workspace -type f | sort

echo ""
echo "Task brief location: /workspace/workspace/content/campaign_brief.json"
echo "Skill documentation: /workspace/workspace/SKILL.md"