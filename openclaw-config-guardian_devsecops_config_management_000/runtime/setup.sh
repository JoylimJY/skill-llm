#!/bin/bash
set -euo pipefail

echo "[setup] Initializing sandbox environment..."

# Ensure workspace scripts are executable
chmod +x /workspace/scripts/install.sh
chmod +x /workspace/scripts/openclaw-config-guardian
chmod +x /workspace/scripts/rotate_keys.sh
chmod +x /workspace/scripts/healthcheck.sh
chmod +x /workspace/scripts/backup_config.sh

# Ensure the initial openclaw config exists and is valid
mkdir -p /root/.openclaw
if [[ ! -f /root/.openclaw/openclaw.json ]]; then
    cat > /root/.openclaw/openclaw.json <<'EOF'
{
  "gateway_id": "gw-prod-7a3f",
  "port": 8443,
  "environment": "production",
  "tls": true,
  "max_connections": 1000,
  "timeout_ms": 5000,
  "routes": [
    {"path": "/pay", "upstream": "payment-svc:9001"},
    {"path": "/refund", "upstream": "refund-svc:9002"}
  ]
}
EOF
    chmod 600 /root/.openclaw/openclaw.json
fi

# Stub out 'openclaw' CLI so guardian's alert call doesn't error fatally
if [[ ! -f /usr/local/bin/openclaw ]]; then
    cat > /usr/local/bin/openclaw <<'STUB'
#!/bin/bash
# Stub openclaw CLI for sandbox
exit 0
STUB
    chmod +x /usr/local/bin/openclaw
fi

echo "[setup] Environment ready."