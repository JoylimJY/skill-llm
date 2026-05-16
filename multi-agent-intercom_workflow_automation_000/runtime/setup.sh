#!/bin/bash
set -e

# Make the intercom script executable
chmod +x /workspace/skills/multi-agent-intercom/scripts/intercom.py

# Create a mock 'openclaw' binary so the script doesn't fail on Popen
cat > /usr/local/bin/openclaw << 'EOF'
#!/usr/bin/env python3
import sys
import json
import time
import os

# Mock openclaw CLI — records invocations for eval
args = sys.argv[1:]
log_path = "/workspace/data/queue/openclaw_invocations.jsonl"
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, "a") as f:
    f.write(json.dumps({"args": args, "timestamp": time.time()}) + "\n")
print(f"[mock openclaw] invoked with: {args}")
sys.exit(0)
EOF
chmod +x /usr/local/bin/openclaw

echo "[setup] Mock openclaw installed at /usr/local/bin/openclaw"
echo "[setup] intercom.py is executable"
echo "[setup] Workspace is ready for the agent task."