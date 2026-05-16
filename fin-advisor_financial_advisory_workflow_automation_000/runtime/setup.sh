#!/usr/bin/env bash
set -e

# Install the mock mcporter as a system-wide CLI tool
cp /workspace/scripts/mcporter_mock.py /usr/local/bin/mcporter
chmod +x /usr/local/bin/mcporter

# Add a shebang-compatible wrapper so it runs as a Python script
cat > /usr/local/bin/mcporter << 'WRAPPER'
#!/usr/bin/env python3
import subprocess, sys, os
os.execv(sys.executable, [sys.executable, '/workspace/scripts/mcporter_mock.py'] + sys.argv[1:])
WRAPPER
chmod +x /usr/local/bin/mcporter

# Make the underlying script executable too
chmod +x /workspace/scripts/mcporter_mock.py

# Create empty log file for call tracking
mkdir -p /workspace/logs
touch /workspace/logs/mcporter_calls.jsonl

# Verify mcporter is accessible
echo "mcporter mock installed at $(which mcporter)"
mcporter call fund-diagnosis.fundIntro fundObject:"005827" --output json | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['success'], 'mock failed'" && echo "Mock server verification: OK"