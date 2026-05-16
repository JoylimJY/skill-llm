#!/bin/bash
set -e

# Make all scripts in /workspace/scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Ensure deploy/systemd directory exists and is writable
mkdir -p /workspace/deploy/systemd
mkdir -p /workspace/deploy/cron

# Create /var/log/cron-jobs dir as per the wrapper pattern in SKILL.md
mkdir -p /var/log/cron-jobs
chmod 777 /var/log/cron-jobs

# Create /tmp/locks dir for flock files
mkdir -p /tmp/locks
chmod 777 /tmp/locks

echo "Setup complete."