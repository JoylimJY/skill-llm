#!/bin/bash
set -e

# Ensure the mock odps_helper.py is executable
chmod +x /workspace/mcp-odps/scripts/odps_helper.py

# Set mock environment variables so the agent doesn't get stuck on missing creds
export ALIYUN_ACCESS_ID="mock_access_id_test"
export ALIYUN_ACCESS_SECRET="mock_access_secret_test"
export ALIYUN_PROJECT_NAME="mock_project"
export ALIYUN_END_POINT="http://mock.maxcompute.aliyun.com/api"

# Persist env vars for the agent session
echo "export ALIYUN_ACCESS_ID=mock_access_id_test" >> /etc/environment
echo "export ALIYUN_ACCESS_SECRET=mock_access_secret_test" >> /etc/environment
echo "export ALIYUN_PROJECT_NAME=mock_project" >> /etc/environment
echo "export ALIYUN_END_POINT=http://mock.maxcompute.aliyun.com/api" >> /etc/environment

# Also write to a .env file in the expected location
cat > /workspace/mcp-odps/.env <<EOF
ALIYUN_ACCESS_ID=mock_access_id_test
ALIYUN_ACCESS_SECRET=mock_access_secret_test
ALIYUN_PROJECT_NAME=mock_project
ALIYUN_END_POINT=http://mock.maxcompute.aliyun.com/api
EOF

echo "Setup complete. Mock ODPS environment ready."