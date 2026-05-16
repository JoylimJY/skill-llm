#!/usr/bin/env python3
"""
Build the initial sandbox workspace with realistic distractor files
and a scripts/ directory containing the stub script.sh.
"""

import os
import random
import stat

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "logs/app",
    "logs/nginx",
    "config/network",
    "config/deploy",
    "audits/old",
    "audits/archive",
    "deploy/k8s",
    "deploy/compose",
    "monitoring/alerts",
    "monitoring/dashboards",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "logs/app/app.log": (
        "2024-01-10 08:00:01 INFO  Service started on port 8080\n"
        "2024-01-10 08:00:05 WARN  High memory usage detected\n"
        "2024-01-10 08:01:22 ERROR Connection refused on 5432\n"
    ),
    "logs/nginx/access.log": (
        "192.168.1.10 - - [10/Jan/2024:08:00:01 +0000] GET /api/v1/health 200\n"
        "192.168.1.11 - - [10/Jan/2024:08:00:02 +0000] POST /api/v1/data 201\n"
    ),
    "config/network/firewall.rules": (
        "ALLOW TCP 80\nALLOW TCP 443\nALLOW TCP 22\nDENY ALL\n"
    ),
    "config/network/interfaces.cfg": (
        "eth0: 10.0.0.1/24\nlo: 127.0.0.1/8\n"
    ),
    "config/deploy/env.prod": (
        "DB_HOST=postgres-primary\nDB_PORT=5432\nREDIS_PORT=6379\nAPP_PORT=8080\n"
    ),
    "audits/old/network_snapshot_2023.txt": (
        "# OLD AUDIT - DO NOT USE\n"
        "Listening: 80, 443, 22, 5432\n"
        "Connections: 142 ESTABLISHED\n"
        "Dropped packets: 0\n"
    ),
    "audits/archive/audit_2022.json": (
        '{"listening_ports": [22, 80], "established": 55, "stats": {}}\n'
    ),
    "deploy/k8s/deployment.yaml": (
        "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web-app\n"
        "spec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: web\n"
    ),
    "deploy/compose/docker-compose.yml": (
        "version: '3'\nservices:\n  web:\n    image: nginx\n    ports:\n      - '80:80'\n"
        "  db:\n    image: postgres\n    ports:\n      - '5432:5432'\n"
    ),
    "monitoring/alerts/cpu_alert.yaml": (
        "alert: HighCPU\ncondition: cpu_usage > 85\nseverity: warning\n"
    ),
    "monitoring/dashboards/network.json": (
        '{"panels": [{"title": "Bandwidth", "type": "graph"}]}\n'
    ),
    "config/deploy/rollout.sh": (
        "#!/bin/bash\nkubectl rollout restart deployment/web-app\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── scripts/script.sh ───────────────────────────────────────────────────────
# This is the REAL mock implementation of the netstat wrapper.
# It writes deterministic data to ~/.local/share/netstat/ AND prints to stdout.
script_content = r"""#!/usr/bin/env bash
# BytesAgain netstat wrapper v3.0.0

DATADIR="$HOME/.local/share/netstat"
mkdir -p "$DATADIR"

CMD="${1}"
ARG="${2}"

case "$CMD" in
  listen)
    OUTPUT="$DATADIR/listen.txt"
    cat > "$OUTPUT" << 'ENDOFDATA'
Proto  LocalAddress          State
tcp    0.0.0.0:22            LISTEN
tcp    0.0.0.0:80            LISTEN
tcp    0.0.0.0:443           LISTEN
tcp    127.0.0.1:5432        LISTEN
tcp    0.0.0.0:8080          LISTEN
tcp6   :::9090               LISTEN
ENDOFDATA
    cat "$OUTPUT"
    ;;
  connections)
    STATE="${ARG}"
    OUTPUT="$DATADIR/connections_${STATE}.txt"
    if [ "$STATE" = "ESTABLISHED" ]; then
      cat > "$OUTPUT" << 'ENDOFDATA'
Proto  LocalAddress           ForeignAddress         State
tcp    10.0.0.5:8080          10.0.0.20:54321        ESTABLISHED
tcp    10.0.0.5:8080          10.0.0.21:54322        ESTABLISHED
tcp    10.0.0.5:443           10.0.0.22:60001        ESTABLISHED
tcp    10.0.0.5:5432          10.0.0.23:45001        ESTABLISHED
ENDOFDATA
    elif [ "$STATE" = "TIME_WAIT" ]; then
      cat > "$OUTPUT" << 'ENDOFDATA'
Proto  LocalAddress           ForeignAddress         State
tcp    10.0.0.5:80            10.0.0.30:55000        TIME_WAIT
tcp    10.0.0.5:80            10.0.0.31:55001        TIME_WAIT
ENDOFDATA
    else
      cat > "$OUTPUT" << 'ENDOFDATA'
Proto  LocalAddress           ForeignAddress         State
ENDOFDATA
    fi
    cat "$OUTPUT"
    ;;
  stats)
    OUTPUT="$DATADIR/stats.txt"
    cat > "$OUTPUT" << 'ENDOFDATA'
Ip:
    1024 total packets received
    0 forwarded
    0 incoming packets discarded
    1024 incoming packets delivered
    987 requests sent out
Tcp:
    512 active connection openings
    128 passive connection openings
    3 failed connection attempts
    7 connection resets received
    4 connections established
    1019 segments received
    982 segments sent out
    2 segments retransmitted
    0 bad segments received
    12 resets sent
Udp:
    5 packets received
    0 packets to unknown port received
    0 packet receive errors
    5 packets sent
ENDOFDATA
    cat "$OUTPUT"
    ;;
  interfaces)
    OUTPUT="$DATADIR/interfaces.txt"
    cat > "$OUTPUT" << 'ENDOFDATA'
Iface   MTU  RX-OK  TX-OK  RX-ERR  TX-ERR
eth0   1500  10234  9876   0       0
lo    65536   512    512   0       0
ENDOFDATA
    cat "$OUTPUT"
    ;;
  route)
    OUTPUT="$DATADIR/route.txt"
    cat > "$OUTPUT" << 'ENDOFDATA'
Destination  Gateway     Genmask        Flags Iface
0.0.0.0      10.0.0.1    0.0.0.0        UG    eth0
10.0.0.0     0.0.0.0     255.255.255.0  U     eth0
127.0.0.0    0.0.0.0     255.0.0.0      U     lo
ENDOFDATA
    cat "$OUTPUT"
    ;;
  dns)
    OUTPUT="$DATADIR/dns.txt"
    cat > "$OUTPUT" << 'ENDOFDATA'
nameserver 8.8.8.8
nameserver 8.8.4.4
search internal.company.com
ENDOFDATA
    cat "$OUTPUT"
    ;;
  ports)
    PORT="${ARG}"
    OUTPUT="$DATADIR/ports_${PORT}.txt"
    cat > "$OUTPUT" << ENDOFDATA
Port ${PORT} info:
tcp  0.0.0.0:${PORT}  LISTEN
ENDOFDATA
    cat "$OUTPUT"
    ;;
  *)
    echo "Unknown command: $CMD" >&2
    exit 1
    ;;
esac
"""

script_path = os.path.join(WORKSPACE, "scripts", "script.sh")
with open(script_path, "w") as f:
    f.write(script_content)

# Make executable
os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print(f"Workspace built at {WORKSPACE}")
print("Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for file in files:
        rel = os.path.relpath(os.path.join(root, file), WORKSPACE)
        print(f"  {rel}")