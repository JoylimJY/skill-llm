#!/bin/bash
set -e

WORKSPACE=/workspace

# Ensure scripts are executable
chmod +x "$WORKSPACE/openclaw/scripts/check_update.sh"
chmod +x "$WORKSPACE/mock_npm.sh"

# Inject mock npm at front of PATH by creating a wrapper in /usr/local/bin
cat > /usr/local/bin/npm_real_path.sh << 'EOF'
#!/bin/bash
echo "/usr/bin/npm"
EOF
chmod +x /usr/local/bin/npm_real_path.sh

# Create a shim npm that delegates to mock for openclaw operations
cat > /usr/local/bin/npm << 'NPMSHIM'
#!/bin/bash
/workspace/mock_npm.sh "$@"
NPMSHIM
chmod +x /usr/local/bin/npm

# Verify shim is in place
which npm

# Clear any prior npm call log
rm -f /workspace/.npm_calls.log

# Create the baseDir symlink so scripts/{check_update.sh} resolves cleanly
ln -sfn "$WORKSPACE/openclaw" "$WORKSPACE/openclaw_base_link" 2>/dev/null || true

echo "Setup complete. npm shim active."
echo "check_update.sh test:"
bash /workspace/openclaw/scripts/check_update.sh