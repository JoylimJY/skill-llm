#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

echo "Verifying campaign brief exists..."
if [ ! -f /workspace/campaigns/q3_launch/briefs/campaign_brief_raw.json ]; then
    echo "ERROR: Campaign brief not found!"
    exit 1
fi

echo "Setup complete. Agent task: review /workspace/campaigns/q3_launch/briefs/campaign_brief_raw.json and produce compliance_review_report.json"