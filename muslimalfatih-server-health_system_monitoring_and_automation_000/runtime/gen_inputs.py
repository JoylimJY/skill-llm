import os
import stat
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
distractor_dirs = [
    "logs/nginx/access",
    "logs/nginx/error",
    "logs/app/2024-01",
    "logs/app/2024-02",
    "config/services/postgres",
    "config/services/docker",
    "config/gateway/tls",
    "scripts/maintenance",
    "scripts/backup",
    "monitoring/grafana/dashboards",
    "monitoring/prometheus/rules",
    "deploy/k8s/manifests",
    "deploy/ansible/roles",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files with realistic-looking content
distractors = {
    "logs/nginx/access/2024-02-01.log": "192.168.1.1 - - [01/Feb/2024:10:00:01 +0000] \"GET /api/v1/health HTTP/1.1\" 200 234\n" * 50,
    "logs/nginx/error/error.log": "[error] 2024/02/01 10:00:01 upstream timed out (110: Connection timed out)\n" * 10,
    "logs/app/2024-01/app.log": "2024-01-15 12:34:56 INFO Transaction processed: txn_abc123 amount=1500.00\n" * 30,
    "logs/app/2024-02/app.log": "2024-02-01 09:15:22 WARN Slow query detected: 2340ms\n2024-02-01 09:15:23 INFO Retry succeeded\n" * 20,
    "config/services/postgres/postgresql.conf": "max_connections = 200\nshared_buffers = 256MB\neffective_cache_size = 1GB\nlog_min_duration_statement = 1000\n",
    "config/services/docker/daemon.json": '{"log-driver": "json-file", "log-opts": {"max-size": "100m", "max-file": "3"}, "storage-driver": "overlay2"}\n',
    "config/gateway/tls/cert.pem.info": "Certificate expires: 2025-08-15\nIssuer: Let's Encrypt\nSubject: gateway.fintech-internal.io\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\n# Cleanup old logs older than 30 days\nfind /var/log -name '*.log' -mtime +30 -delete\n",
    "scripts/backup/db_backup.sh": "#!/bin/bash\n# Database backup script\npg_dump -U postgres fintech_db | gzip > /backups/db_$(date +%Y%m%d).sql.gz\n",
    "monitoring/grafana/dashboards/system_overview.json": '{"title": "System Overview", "panels": [], "version": 7}\n',
    "monitoring/prometheus/rules/alerts.yml": "groups:\n  - name: system\n    rules:\n      - alert: HighCPU\n        expr: cpu_usage > 90\n",
    "deploy/k8s/manifests/gateway-deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: openclaw-gateway\nspec:\n  replicas: 1\n",
    "deploy/ansible/roles/README": "Ansible roles for provisioning fintech gateway servers.\n",
    "config/gateway/gateway.env": "GATEWAY_PORT=18789\nGATEWAY_VERSION=2026.2.6-3\nPRIMARY_MODEL=claude-sonnet-4-5\nFALLBACK_MODELS=glm-4.7,copilot-sonnet,opus-4-5\n",
}

for filepath, content in distractors.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the mock server-health.sh script ---
# This script simulates a server with DISK at 92% (triggering an alert)
# RAM at 68% (below 80% threshold, no alert)
# CPU at 45% (below 90% threshold, no alert)

server_health_script = r"""#!/bin/bash

# Mock server-health.sh for fintech gateway server
# Simulates real server-health skill behavior

VERBOSE=0
JSON=0
ALERTS=0

for arg in "$@"; do
    case $arg in
        --verbose) VERBOSE=1 ;;
        --json) JSON=1 ;;
        --alerts) ALERTS=1 ;;
    esac
done

# Simulated values
CPU_PCT=45
CPU_LOAD1=1.82
CPU_LOAD5=1.54
CPU_LOAD15=1.21
RAM_USED_GB=5.44
RAM_TOTAL_GB=8
RAM_PCT=68
DISK_USED_GB=92
DISK_TOTAL_GB=100
DISK_PCT=92
UPTIME_STR="12d 7h"
OC_PID=1639125
OC_PORT=18789
OC_VERSION="v2026.2.6-3"
OC_UPTIME="2d 5h"
MODEL_PRIMARY="claude-sonnet-4-5"
MODEL_CTX_USED=43000
MODEL_CTX_TOTAL=128000
MODEL_CTX_PCT=33
TOKENS_DOWN=574
TOKENS_UP=182
FALLBACK1="glm-4.7"
FALLBACK2="copilot-sonnet"
FALLBACK3="opus-4-5"
SESSIONS_ACTIVE=3
HEARTBEAT_MIN=30
LAST_SEEN_MIN=1
DOCKER_CONTAINERS=3
PG_STATUS="Running"
SWAP_USED_GB=0
NET_RX="12.4 MB/s"
NET_TX="3.2 MB/s"
DISK_IO_READ="45.2 MB/s"
DISK_IO_WRITE="18.7 MB/s"
TEMP_CPU="58°C"

if [ $JSON -eq 1 ]; then
    cat <<EOF
{
  "system": {
    "cpu_percent": $CPU_PCT,
    "cpu_load": [$CPU_LOAD1, $CPU_LOAD5, $CPU_LOAD15],
    "ram_used_gb": $RAM_USED_GB,
    "ram_total_gb": $RAM_TOTAL_GB,
    "ram_percent": $RAM_PCT,
    "disk_used_gb": $DISK_USED_GB,
    "disk_total_gb": $DISK_TOTAL_GB,
    "disk_percent": $DISK_PCT,
    "uptime": "$UPTIME_STR"
  },
  "processes": [
    {"name": "node", "cpu_percent": 35, "ram_mb": 450},
    {"name": "postgres", "cpu_percent": 12, "ram_mb": 280},
    {"name": "openclaw", "cpu_percent": 8, "ram_mb": 180}
  ],
  "openclaw": {
    "status": "running",
    "pid": $OC_PID,
    "uptime": "$OC_UPTIME",
    "port": $OC_PORT,
    "version": "$OC_VERSION"
  },
  "model": {
    "primary": "$MODEL_PRIMARY",
    "context_used": $MODEL_CTX_USED,
    "context_total": $MODEL_CTX_TOTAL,
    "context_percent": $MODEL_CTX_PCT,
    "tokens_down": $TOKENS_DOWN,
    "tokens_up": $TOKENS_UP,
    "fallbacks": ["$FALLBACK1", "$FALLBACK2", "$FALLBACK3"]
  },
  "sessions": {
    "active": $SESSIONS_ACTIVE,
    "heartbeat_minutes": $HEARTBEAT_MIN,
    "last_seen_minutes": $LAST_SEEN_MIN
  },
  "services": {
    "docker_containers": $DOCKER_CONTAINERS,
    "postgresql": "$PG_STATUS"
  }
}
EOF
    exit 0
fi

if [ $ALERTS -eq 1 ]; then
    ALERT_COUNT=0
    if [ $DISK_PCT -gt 90 ]; then
        echo "⚠️  DISK ALERT: ${DISK_PCT}% used (${DISK_USED_GB}GB/${DISK_TOTAL_GB}GB) - threshold: 90%"
        ALERT_COUNT=$((ALERT_COUNT+1))
    fi
    if [ $RAM_PCT -gt 80 ]; then
        echo "⚠️  RAM ALERT: ${RAM_PCT}% used (${RAM_USED_GB}GB/${RAM_TOTAL_GB}GB) - threshold: 80%"
        ALERT_COUNT=$((ALERT_COUNT+1))
    fi
    if [ $CPU_PCT -gt 90 ]; then
        echo "⚠️  CPU ALERT: ${CPU_PCT}% used - threshold: 90%"
        ALERT_COUNT=$((ALERT_COUNT+1))
    fi
    if [ $ALERT_COUNT -eq 0 ]; then
        echo "✅ All systems nominal"
    fi
    exit 0
fi

if [ $VERBOSE -eq 1 ]; then
    cat <<VERBEOF
🖥️ SERVER HEALTH
━━━━━━━━━━━━━━━━━━━━

💻 SYSTEM
CPU: ████░░░░░░ ${CPU_PCT}% (Load: ${CPU_LOAD1}, ${CPU_LOAD5}, ${CPU_LOAD15})
RAM: ██████░░░░ ${RAM_USED_GB}GB/${RAM_TOTAL_GB}GB (${RAM_PCT}%)
DISK: █████████░ ${DISK_USED_GB}GB/${DISK_TOTAL_GB}GB (${DISK_PCT}%)
UP: ⏱️ ${UPTIME_STR}

🌡️ TEMPERATURE
CPU Temp: ${TEMP_CPU}

🌐 NETWORK
RX: ${NET_RX} | TX: ${NET_TX}

💾 DISK I/O
Read: ${DISK_IO_READ} | Write: ${DISK_IO_WRITE}

🔄 TOP PROCESSES
node         35%    450MB
postgres     12%    280MB
openclaw      8%    180MB

⚡ OPENCLAW GATEWAY
Status: ✅ Running (PID: ${OC_PID})
Uptime: ${OC_UPTIME} | Port: ${OC_PORT} | ${OC_VERSION}

🤖 MODEL CONFIG
Primary: ${MODEL_PRIMARY}
Context: ${MODEL_CTX_USED}k/${MODEL_CTX_TOTAL}k (${MODEL_CTX_PCT}%) | ${TOKENS_DOWN}↓ ${TOKENS_UP}↑ tokens
Fallbacks: ${FALLBACK1} → ${FALLBACK2} → ${FALLBACK3}

📊 SESSIONS
Active: ${SESSIONS_ACTIVE} | Heartbeat: ${HEARTBEAT_MIN}m | Last: ${LAST_SEEN_MIN}m ago

🐳 SERVICES
Docker: ✅ ${DOCKER_CONTAINERS} containers
PostgreSQL: ✅ ${PG_STATUS}
VERBEOF
    exit 0
fi

# Standard output
cat <<STDEOF
🖥️ SERVER HEALTH
━━━━━━━━━━━━━━━━━━━━

💻 SYSTEM
CPU: ████░░░░░░ ${CPU_PCT}% (Load: ${CPU_LOAD1}, ${CPU_LOAD5}, ${CPU_LOAD15})
RAM: ██████░░░░ ${RAM_USED_GB}GB/${RAM_TOTAL_GB}GB (${RAM_PCT}%)
DISK: █████████░ ${DISK_USED_GB}GB/${DISK_TOTAL_GB}GB (${DISK_PCT}%)
UP: ⏱️ ${UPTIME_STR}

🔄 TOP PROCESSES
node         35%    450MB
postgres     12%    280MB
openclaw      8%    180MB

⚡ OPENCLAW GATEWAY
Status: ✅ Running (PID: ${OC_PID})
Uptime: ${OC_UPTIME} | Port: ${OC_PORT} | ${OC_VERSION}

🤖 MODEL CONFIG
Primary: ${MODEL_PRIMARY}
Context: ${MODEL_CTX_USED}k/${MODEL_CTX_TOTAL}k (${MODEL_CTX_PCT}%) | ${TOKENS_DOWN}↓ ${TOKENS_UP}↑ tokens
Fallbacks: ${FALLBACK1} → ${FALLBACK2} → ${FALLBACK3}

📊 SESSIONS
Active: ${SESSIONS_ACTIVE} | Heartbeat: ${HEARTBEAT_MIN}m | Last: ${LAST_SEEN_MIN}m ago

🐳 SERVICES
Docker: ✅ ${DOCKER_CONTAINERS} containers
PostgreSQL: ✅ ${PG_STATUS}
STDEOF
exit 0
"""

server_health_path = os.path.join(workspace, "server-health.sh")
with open(server_health_path, "w") as f:
    f.write(server_health_script)

# Make it executable
os.chmod(server_health_path, 
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# Add a plausible but misleading "old" health snapshot to distract the agent
old_snapshot = {
    "timestamp": "2024-01-15T08:30:00Z",
    "cpu": 23,
    "ram": 45,
    "disk": 78,
    "status": "ok",
    "note": "Legacy format - do not use for pipeline"
}
import json
with open(os.path.join(workspace, "monitoring/grafana/dashboards/last_health_snapshot.json"), "w") as f:
    json.dump(old_snapshot, f, indent=2)

# Add a fake partial config that looks like output but is wrong
with open(os.path.join(workspace, "config/gateway/health_cache.txt"), "w") as f:
    f.write("CACHED HEALTH - STALE\n")
    f.write("disk=78% ram=55% cpu=30%\n")
    f.write("Generated: 2024-01-10 (outdated - regenerate from script)\n")

print("Workspace setup complete.")
print(f"Files created in {workspace}")