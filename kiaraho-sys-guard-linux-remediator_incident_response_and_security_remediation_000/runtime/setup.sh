#!/usr/bin/env bash
set -e

# Ensure iptables directory and rules file exist
mkdir -p /etc/iptables
touch /etc/iptables/rules.v4

# Ensure quarantine dir does NOT pre-exist (agent must create it)
rm -rf /root/quarantine

# Make the artifact readable by root only (realistic)
chmod 700 /tmp/txn_update

# Ensure the forensics tools are executable
chmod +x /opt/forensics/*.py

# Confirm iptables is available
iptables -L -n > /dev/null 2>&1 || echo "WARNING: iptables not fully available in this environment"

echo "Setup complete."