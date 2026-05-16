#!/bin/bash
set -e

# Ensure reference files are readable
chmod -R 644 /home/ubuntu/skills/clawhub-recommender/references/
chmod +x /home/ubuntu/scripts/deploy/deploy.sh
chmod +x /home/ubuntu/scripts/backup/backup.sh

echo "Setup complete. Workspace ready."
ls /home/ubuntu/skills/clawhub-recommender/references/