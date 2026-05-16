#!/usr/bin/env bash
set -euo pipefail

echo "[setup] Ensuring scripts are executable..."
chmod +x /workspace/scripts/install_official_obsidian.sh
chmod +x /workspace/scripts/configure_official_cli.sh
chmod +x /workspace/scripts/verify_official_cli.sh

echo "[setup] Creating target vault directory owned by root (simulates real scenario)..."
mkdir -p /root/research-vault/daily
mkdir -p /root/research-vault/projects
touch /root/research-vault/daily/.keep
touch /root/research-vault/projects/.keep

echo "[setup] Ensuring /var/lib/obsidian-cli placeholder exists..."
mkdir -p /var/lib/obsidian-cli

echo "[setup] Verifying ACL tools available..."
which setfacl || echo "[setup] WARNING: setfacl not found, configure script will use fallback chmod"

echo "[setup] Ready. Agent should work from /workspace."