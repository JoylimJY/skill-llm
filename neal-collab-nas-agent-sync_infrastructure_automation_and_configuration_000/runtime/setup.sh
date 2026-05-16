#!/usr/bin/env bash
set -e

echo "[setup] Configuring mock SSH server for NAS simulation..."

# Create nas-user with home at /nas_home
useradd -m -d /nas_home -s /bin/bash nas-user 2>/dev/null || true
chown -R nas-user:nas-user /nas_home

# Generate SSH keys for root (the agent) to authenticate to nas-user@localhost
mkdir -p /root/.ssh
if [ ! -f /root/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 2048 -f /root/.ssh/id_rsa -N "" -q
fi

# Authorize root's public key for nas-user
mkdir -p /nas_home/.ssh
cat /root/.ssh/id_rsa.pub >> /nas_home/.ssh/authorized_keys
chmod 700 /nas_home/.ssh
chmod 600 /nas_home/.ssh/authorized_keys
chown -R nas-user:nas-user /nas_home/.ssh

# Start SSH server
mkdir -p /run/sshd
/usr/sbin/sshd -o "StrictModes no" -o "PermitRootLogin yes"
sleep 1

# Pre-accept localhost host key
ssh-keyscan -H localhost >> /root/.ssh/known_hosts 2>/dev/null || true

echo "[setup] SSH mock NAS ready. Test: ssh nas-user@localhost 'echo OK'"
ssh nas-user@localhost "echo '[setup] SSH connection verified OK'"

echo "[setup] Setup complete."