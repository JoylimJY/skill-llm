#!/bin/bash
set -e

# Make deploy script executable (distractor)
chmod +x /workspace/scripts/deploy.sh

echo "Sandbox ready. Input data available at /workspace/data/raw_tickets/escalation_TK9021.json"
echo "The relay bot must format the summary for the Signal channel."