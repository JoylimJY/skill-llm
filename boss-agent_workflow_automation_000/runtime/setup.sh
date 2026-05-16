#!/bin/bash
set -e

# Make mock scripts executable
chmod +x /workspace/bin/sessions_list
chmod +x /workspace/bin/sessions_send
chmod +x /workspace/bin/systemctl_mock
chmod +x /workspace/scripts/utils/health_check.sh

# Add workspace/bin to PATH so agent can use sessions_list and sessions_send directly
echo 'export PATH="/workspace/bin:$PATH"' >> /etc/profile
echo 'export PATH="/workspace/bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/workspace/bin:$PATH"' >> /root/.profile

# Make systemctl available as a mock (override for --user flag testing)
# Create a wrapper that delegates to our mock when --user is used
cat > /usr/local/bin/systemctl << 'EOF'
#!/bin/bash
if [[ "$*" == *"--user"* ]]; then
    exec /workspace/bin/systemctl_mock "$@"
else
    /bin/systemctl "$@" 2>/dev/null || true
fi
EOF
chmod +x /usr/local/bin/systemctl

# Ensure PATH is immediately available
export PATH="/workspace/bin:$PATH"

# Verify mock tools work
echo "Verifying mock tools..."
/workspace/bin/sessions_list --agent ass > /dev/null && echo "sessions_list: OK"
/workspace/bin/sessions_send --session-key agent:ass:main --message "test" > /dev/null && echo "sessions_send: OK"

# Create the output directory for incident report
mkdir -p /workspace/reports/incidents

echo "Setup complete. Mock CLI tools are ready."
echo "PATH includes /workspace/bin: $PATH"