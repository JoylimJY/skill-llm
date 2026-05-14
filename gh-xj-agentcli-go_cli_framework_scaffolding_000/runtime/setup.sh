#!/bin/bash
set -e

echo "=== Setting up sandbox environment ==="

# Ensure Go is on PATH
export GOPATH=/root/go
export PATH=$PATH:/root/go/bin

# Ensure agentcli binary is available
if ! command -v agentcli &> /dev/null; then
    echo "agentcli not found in PATH, attempting install..."
    cd /opt/agentcli-go 2>/dev/null && go install ./cmd/agentcli/... 2>/dev/null || true
fi

# Set up Go proxy to use direct (allows fetching agentcli-go)
go env -w GONOSUMCHECK="*"
go env -w GONOSUMDB="*"
go env -w GONOPROXY=""
go env -w GOPROXY="https://goproxy.cn,direct"

# Make workspace writable
chmod -R 777 /workspace

# Verify the broken project is there
echo "=== Verifying workspace structure ==="
ls /workspace/
ls /workspace/infra-deployer/

echo "=== Setup complete ==="