#!/bin/bash
set -e

# Make placeholder scripts executable
chmod +x /workspace/openclaw/scripts/*.sh 2>/dev/null || true

# Ensure infra/systemd and infra/monitoring dirs exist
mkdir -p /workspace/infra/systemd
mkdir -p /workspace/infra/monitoring

# Create a minimal mock `openclaw` CLI so the agent can test commands
cat > /usr/local/bin/openclaw << 'EOF'
#!/bin/bash
if [ "$1" = "gateway" ] && [ "$2" = "status" ]; then
  echo "gateway: running on port 8080"
  exit 0
fi
echo "openclaw: unknown command"
exit 1
EOF
chmod +x /usr/local/bin/openclaw

echo "Setup complete."