#!/bin/bash
set -e

# Ensure correct ownership
chown -R bioagent:bioagent /home/bioagent

# Ensure git is configured for bioagent
su - bioagent -c "git config --global user.email 'bio@lab.org' && git config --global user.name 'BioLab'"

# Ensure the openclaw workspace parent exists
mkdir -p /home/bioagent/.openclaw
chown -R bioagent:bioagent /home/bioagent/.openclaw

echo "Setup complete."