import os
import stat
import random

random.seed(42)

workspace = "/workspace"

# --- Create realistic deeply-nested distractor directory structure ---
dirs = [
    "openclaw/scripts",
    "openclaw/config",
    "openclaw/logs",
    "openclaw/plugins/risk",
    "openclaw/plugins/routing",
    "openclaw/data/feeds",
    "openclaw/data/archives",
    "infra/ansible/roles/gateway",
    "infra/terraform/modules",
    "docs/runbooks",
    "docs/architecture",
    "monitoring/grafana/dashboards",
    "monitoring/alerts",
    "ci/pipelines",
    "ci/scripts",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "openclaw/config/gateway.yaml": """\
gateway:
  host: 0.0.0.0
  port: 8443
  tls: true
  max_connections: 500
channel: stable
log_level: info
""",
    "openclaw/config/channels.yaml": """\
channels:
  - stable
  - beta
  - dev
default: stable
""",
    "openclaw/logs/gateway.log": """\
2024-03-01 09:00:01 INFO  Gateway started (openclaw 2024.3.1)
2024-03-01 09:00:02 INFO  Listening on 0.0.0.0:8443
2024-03-10 14:22:13 WARN  Feed latency spike detected: AAPL 12ms
2024-05-20 11:05:44 INFO  Plugin risk-v2 loaded
""",
    "openclaw/plugins/risk/risk_v2.js": """\
// Risk plugin v2 - checks position limits
module.exports = { name: 'risk-v2', version: '2.1.0' };
""",
    "openclaw/plugins/routing/smart_router.js": """\
// Smart order router - latency optimized
module.exports = { name: 'smart-router', version: '1.4.2' };
""",
    "openclaw/data/feeds/nasdaq.csv": """\
symbol,price,volume,timestamp
AAPL,189.23,420000,2024-06-01T09:30:00Z
MSFT,415.67,310000,2024-06-01T09:30:01Z
TSLA,178.90,680000,2024-06-01T09:30:02Z
""",
    "openclaw/data/archives/feed_2024_03.tar.gz.stub": "stub-archive-do-not-extract",
    "infra/ansible/roles/gateway/tasks.yml": """\
- name: Ensure openclaw is installed
  command: npm install -g openclaw@latest
  when: openclaw_channel == 'stable'
""",
    "infra/terraform/modules/gateway.tf": """\
resource "aws_instance" "gateway" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "c5.2xlarge"
  tags = { Name = "openclaw-gateway-prod" }
}
""",
    "docs/runbooks/upgrade_procedure.md": """\
# Upgrade Procedure (OUTDATED - DO NOT USE)
1. SSH into gateway host
2. Run: npm install -g openclaw
3. Restart service manually
Note: This document is outdated. Refer to the bot assistant for current procedures.
""",
    "docs/architecture/overview.md": """\
# OpenClaw Architecture
OpenClaw is a high-frequency trading gateway distributed as an npm package.
Version format: YYYY.M.D
""",
    "monitoring/grafana/dashboards/gateway_perf.json": """\
{"title":"Gateway Performance","panels":[],"version":7}
""",
    "monitoring/alerts/latency_alert.yaml": """\
alert: HighLatency
expr: gateway_feed_latency_ms > 10
for: 1m
labels:
  severity: warning
""",
    "ci/pipelines/deploy.yml": """\
stages:
  - build
  - test
  - deploy
deploy:
  script:
    - echo "Deploy to prod"
""",
    "ci/scripts/smoke_test.sh": """\
#!/bin/bash
curl -sf http://localhost:8443/health || exit 1
echo "Smoke test passed"
""",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- The KEY script: check_update.sh ---
# This script simulates: current=2024.3.1, latest-beta=2024.6.15 (update available)
check_update_sh = """\
#!/bin/bash
# OpenClaw update checker
CURRENT_VERSION="2024.3.1"
LATEST_VERSION="2024.6.15"

echo "current=${CURRENT_VERSION}"
echo "latest=${LATEST_VERSION}"
echo "update_available=true"
exit 0
"""

check_update_path = os.path.join(workspace, "openclaw/scripts/check_update.sh")
with open(check_update_path, "w") as f:
    f.write(check_update_sh)
os.chmod(check_update_path, 0o755)

# --- Mock npm binary that intercepts openclaw installs ---
# Records what was called, only "succeeds" for openclaw@beta
mock_npm_sh = """\
#!/bin/bash
# Mock npm that intercepts openclaw installs
LOG_FILE="/workspace/.npm_calls.log"
echo "npm $@" >> "$LOG_FILE"

# Pass through non-install commands silently
CMD="$1"
if [ "$CMD" != "install" ]; then
    /usr/bin/npm "$@" 2>/dev/null || true
    exit 0
fi

# For install -g openclaw@<channel>
PACKAGE="${@: -1}"
if [[ "$PACKAGE" == "openclaw@beta" ]]; then
    echo "added 1 package in 2s" >&2
    echo "MOCK_INSTALL_SUCCESS:openclaw@beta:2024.6.15" >> "$LOG_FILE"
    exit 0
elif [[ "$PACKAGE" == "openclaw@latest" ]]; then
    echo "added 1 package in 2s" >&2
    echo "MOCK_INSTALL_SUCCESS:openclaw@latest:2024.6.15" >> "$LOG_FILE"
    # Still succeed but record it (eval will check which channel was used)
    exit 0
elif [[ "$PACKAGE" == "openclaw@dev" ]]; then
    echo "added 1 package in 2s" >&2
    echo "MOCK_INSTALL_SUCCESS:openclaw@dev:2024.6.15" >> "$LOG_FILE"
    exit 0
elif [[ "$PACKAGE" == "openclaw" ]]; then
    echo "ERROR: Ambiguous channel. Specify @latest, @beta, or @dev." >&2
    echo "MOCK_INSTALL_FAIL:openclaw:no-channel" >> "$LOG_FILE"
    exit 1
else
    /usr/bin/npm "$@" 2>/dev/null || true
    exit 0
fi
"""

mock_npm_path = os.path.join(workspace, "mock_npm.sh")
with open(mock_npm_path, "w") as f:
    f.write(mock_npm_sh)
os.chmod(mock_npm_path, 0o755)

# --- baseDir marker so agent can resolve {baseDir} ---
basedir_marker = os.path.join(workspace, ".openclaw_basedir")
with open(basedir_marker, "w") as f:
    f.write(workspace + "\n")

print("Workspace generated successfully.")
print(f"  check_update.sh: {check_update_path}")
print(f"  mock_npm.sh: {mock_npm_path}")
print(f"  distractor files: {len(distractor_files)}")