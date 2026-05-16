#!/usr/bin/env bash
set -e

# Make all run.py scripts executable
find /workspace/skills -name "run.py" -exec chmod +x {} \;
chmod +x /workspace/config/mock_server.py

# Start the mock Flask server in the background
export FT_BASE_URL="http://localhost:18080"
python /workspace/config/mock_server.py &
MOCK_PID=$!
echo "Mock server PID: $MOCK_PID"

# Wait for the mock server to be ready
for i in {1..20}; do
    if curl -sf http://localhost:18080/api/fund/support-symbols?page=1 > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    sleep 0.5
done

# Export the env var so all subsequent processes inherit it
echo "export FT_BASE_URL=http://localhost:18080" >> /etc/environment
echo "export FT_BASE_URL=http://localhost:18080" >> /root/.bashrc

# Patch all sub-skill run.py scripts to default to localhost if FT_BASE_URL not set
# (they already read from env var, so just ensure it's exported globally)
export FT_BASE_URL=http://localhost:18080
printenv FT_BASE_URL