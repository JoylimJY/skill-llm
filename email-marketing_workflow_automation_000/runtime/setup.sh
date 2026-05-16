#!/bin/bash
set -e

# Make workspace readable
chmod -R 755 /workspace

echo "Workspace ready. Subscriber data and campaign brief are in place."
ls /workspace/codepulse/marketing/campaigns/
ls /workspace/codepulse/sales/crm_exports/