import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested directory structure with distractor files
dirs = [
    "logs/boss",
    "logs/ass",
    "logs/ops",
    "config/agents",
    "config/network",
    "sessions/cache",
    "sessions/archive",
    "reports/daily",
    "reports/incidents",
    "scripts/utils",
    "scripts/deprecated",
    "data/metrics",
    "data/inventory",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but not what the agent needs to produce
distractor_files = {
    "logs/boss/boss_startup.log": "[2024-01-15 08:00:01] Boss Agent started\n[2024-01-15 08:00:02] Connected to gateway\n[2024-01-15 08:00:03] All agents reachable\n",
    "logs/ass/ass_activity.log": "[2024-01-15 08:01:00] Ass Agent idle\n[2024-01-15 08:05:00] Task received\n[2024-01-15 08:05:30] Task completed\n",
    "logs/ops/ops_activity.log": "[2024-01-15 07:58:00] Ops Agent started monitoring\n[2024-01-15 08:10:00] Anomaly detected in gateway\n[2024-01-15 08:12:00] Alert raised\n",
    "config/agents/boss_config.json": json.dumps({"agent": "boss", "role": "coordinator", "version": "1.2.0", "gateway_port": 8080}, indent=2),
    "config/agents/ass_config.json": json.dumps({"agent": "ass", "role": "assistant", "version": "1.1.0", "gateway_port": 8081}, indent=2),
    "config/agents/ops_config.json": json.dumps({"agent": "ops", "role": "operations", "version": "1.1.0", "gateway_port": 8082}, indent=2),
    "config/network/routing.json": json.dumps({"routes": [{"from": "boss", "to": "ass", "key": "agent:ass:main"}, {"from": "boss", "to": "ops", "key": "agent:ops:main"}]}, indent=2),
    "sessions/cache/session_meta.json": json.dumps({"last_updated": "2024-01-15T08:15:00Z", "active_sessions": ["agent:boss:main", "agent:ass:main", "agent:ops:main"]}, indent=2),
    "sessions/archive/old_session_2024_01_14.json": json.dumps({"date": "2024-01-14", "tasks_completed": 12, "agents": ["ass", "ops"]}, indent=2),
    "reports/daily/report_2024_01_14.json": json.dumps({"date": "2024-01-14", "status": "all_clear", "services": {"doc_service": "ok", "user_service": "ok", "sys_service": "ok", "gateway": "ok"}}, indent=2),
    "scripts/utils/health_check.sh": "#!/bin/bash\necho 'Running health check...'\necho 'All systems nominal'\n",
    "scripts/deprecated/old_send_task.sh": "#!/bin/bash\n# DEPRECATED: Use sessions_send instead\necho 'This script is deprecated'\n",
    "data/metrics/service_metrics.csv": "timestamp,service,latency_ms,errors\n2024-01-15T08:00:00Z,doc_service,45,0\n2024-01-15T08:00:00Z,user_service,120,3\n2024-01-15T08:00:00Z,sys_service,200,12\n2024-01-15T08:00:00Z,gateway,89,1\n",
    "data/inventory/services.json": json.dumps({
        "services": [
            {"name": "doc_service", "owner": "ass", "criticality": "medium"},
            {"name": "user_service", "owner": "ass", "criticality": "high"},
            {"name": "sys_service", "owner": "ops", "criticality": "high"},
            {"name": "gateway", "owner": "ops", "criticality": "critical"}
        ]
    }, indent=2),
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Create mock CLI scripts that the SKILL.md references
# These simulate what sessions_list and sessions_send would return

# sessions_list mock: returns different output based on --agent flag
sessions_list_script = r"""#!/bin/bash
# Mock sessions_list CLI tool
# Usage: sessions_list --agent <agent_name>

AGENT=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --agent)
            AGENT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$AGENT" ]; then
    echo "Error: --agent flag required"
    exit 1
fi

case "$AGENT" in
    ass)
        cat /workspace/mock_data/ass_sessions.json
        ;;
    ops)
        cat /workspace/mock_data/ops_sessions.json
        ;;
    boss)
        cat /workspace/mock_data/boss_sessions.json
        ;;
    *)
        echo '{"error": "Unknown agent"}'
        exit 1
        ;;
esac
"""

# sessions_send mock: appends sent messages to a log file
sessions_send_script = r"""#!/bin/bash
# Mock sessions_send CLI tool
# Usage: sessions_send --session-key <key> --message <message>

SESSION_KEY=""
MESSAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --session-key)
            SESSION_KEY="$2"
            shift 2
            ;;
        --message)
            MESSAGE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ -z "$SESSION_KEY" ] || [ -z "$MESSAGE" ]; then
    echo "Error: --session-key and --message flags required"
    exit 1
fi

# Validate session key format: must be agent:<name>:main
if ! echo "$SESSION_KEY" | grep -qE '^agent:[a-z]+:main$'; then
    echo "Error: Invalid session key format. Expected agent:<name>:main"
    exit 1
fi

AGENT_NAME=$(echo "$SESSION_KEY" | cut -d: -f2)
LOGFILE="/workspace/sessions/sent_messages.log"

# Append the sent message to log
echo "{\"session_key\": \"$SESSION_KEY\", \"agent\": \"$AGENT_NAME\", \"message\": \"$MESSAGE\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}" >> "$LOGFILE"

# Return simulated agent response based on target agent
case "$AGENT_NAME" in
    ass)
        echo '{"status": "received", "agent": "ass", "response": "Task acknowledged. Checking doc_service and user_service. doc_service: degraded (high latency 450ms). user_service: 3 errors in last 5 minutes, investigating."}'
        ;;
    ops)
        echo '{"status": "received", "agent": "ops", "response": "Task acknowledged. Checking sys_service and gateway. sys_service: 12 errors detected, restarting. gateway: critical - packet loss 15%, escalating."}'
        ;;
    *)
        echo '{"status": "received", "agent": "'$AGENT_NAME'", "response": "Task acknowledged."}'
        ;;
esac
"""

# systemctl mock for --user flag
systemctl_mock = r"""#!/bin/bash
# Mock systemctl for agent status checks
# Usage: systemctl --user status <service>

MODE=""
ACTION=""
SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            MODE="user"
            shift
            ;;
        status)
            ACTION="status"
            shift
            ;;
        *)
            SERVICE="$1"
            shift
            ;;
    esac
done

case "$SERVICE" in
    openclaw-gateway-boss.service)
        echo "● openclaw-gateway-boss.service - OpenClaw Gateway Boss Agent"
        echo "   Loaded: loaded (/home/user/.config/systemd/user/openclaw-gateway-boss.service; enabled)"
        echo "   Active: active (running) since Mon 2024-01-15 08:00:01 UTC; 2h ago"
        echo "   PID: 1234"
        ;;
    openclaw-gateway-ass.service)
        echo "● openclaw-gateway-ass.service - OpenClaw Gateway Ass Agent"
        echo "   Loaded: loaded (/home/user/.config/systemd/user/openclaw-gateway-ass.service; enabled)"
        echo "   Active: active (running) since Mon 2024-01-15 08:00:02 UTC; 2h ago"
        echo "   PID: 1235"
        ;;
    openclaw-gateway-ops.service)
        echo "● openclaw-gateway-ops.service - OpenClaw Gateway Ops Agent"
        echo "   Loaded: loaded (/home/user/.config/systemd/user/openclaw-gateway-ops.service; enabled)"
        echo "   Active: active (running) since Mon 2024-01-15 08:00:03 UTC; 2h ago"
        echo "   PID: 1236"
        ;;
    *)
        echo "Unit $SERVICE could not be found."
        exit 1
        ;;
esac
"""

# Mock data for sessions_list
mock_data_dir = workspace / "mock_data"
mock_data_dir.mkdir(exist_ok=True)

ass_sessions = {
    "agent": "ass",
    "sessions": [
        {
            "session_id": "sess_ass_001",
            "key": "agent:ass:main",
            "messages": [
                {"role": "user", "content": "Check documentation service health", "timestamp": "2024-01-15T07:50:00Z"},
                {"role": "assistant", "content": "doc_service responding slowly, latency 450ms above threshold", "timestamp": "2024-01-15T07:50:30Z"},
                {"role": "user", "content": "Check user service", "timestamp": "2024-01-15T08:00:00Z"},
                {"role": "assistant", "content": "user_service showing intermittent 500 errors, approximately 3 per minute", "timestamp": "2024-01-15T08:00:45Z"}
            ],
            "status": "active",
            "last_activity": "2024-01-15T08:00:45Z"
        }
    ]
}

ops_sessions = {
    "agent": "ops",
    "sessions": [
        {
            "session_id": "sess_ops_001",
            "key": "agent:ops:main",
            "messages": [
                {"role": "user", "content": "Monitor system services", "timestamp": "2024-01-15T07:58:00Z"},
                {"role": "assistant", "content": "sys_service: error rate spiking, 12 errors detected. gateway: packet loss at 15%", "timestamp": "2024-01-15T08:10:00Z"},
                {"role": "assistant", "content": "Alert raised for gateway service degradation", "timestamp": "2024-01-15T08:12:00Z"}
            ],
            "status": "active",
            "last_activity": "2024-01-15T08:12:00Z"
        }
    ]
}

boss_sessions = {
    "agent": "boss",
    "sessions": [
        {
            "session_id": "sess_boss_001",
            "key": "agent:boss:main",
            "messages": [
                {"role": "user", "content": "Coordinate incident investigation", "timestamp": "2024-01-15T08:15:00Z"}
            ],
            "status": "active",
            "last_activity": "2024-01-15T08:15:00Z"
        }
    ]
}

(mock_data_dir / "ass_sessions.json").write_text(json.dumps(ass_sessions, indent=2))
(mock_data_dir / "ops_sessions.json").write_text(json.dumps(ops_sessions, indent=2))
(mock_data_dir / "boss_sessions.json").write_text(json.dumps(boss_sessions, indent=2))

# Write mock scripts to /usr/local/bin style paths (will be chmod'd in setup)
scripts_dir = workspace / "bin"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "sessions_list").write_text(sessions_list_script)
(scripts_dir / "sessions_send").write_text(sessions_send_script)
(scripts_dir / "systemctl_mock").write_text(systemctl_mock)

# Create the sent_messages log (initially empty)
(workspace / "sessions" / "sent_messages.log").write_text("")

print("Workspace initialized successfully.")
print(f"Created {len(distractor_files)} distractor files")
print("Mock CLI tools created in /workspace/bin/")