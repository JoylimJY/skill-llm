import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create the minecraft-monitor skill script path
script_dir = os.path.expanduser("~/.openclaw/workspace/skills/public/minecraft-monitor/scripts")
os.makedirs(script_dir, exist_ok=True)

# Write the actual minecraft-status.py script
minecraft_script = r'''#!/usr/bin/env python3
"""
Minecraft Server List Ping (SLP) checker.
Usage: minecraft-status.py <host[:port]> [timeout]
Exit code: 0 if online, 1 if offline
"""

import sys
import socket
import struct
import json
import time


def read_varint(sock):
    result = 0
    shift = 0
    while True:
        byte = sock.recv(1)
        if not byte:
            raise ConnectionError("Socket closed")
        b = ord(byte)
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result


def write_varint(value):
    out = b""
    while True:
        part = value & 0x7F
        value >>= 7
        if value:
            part |= 0x80
        out += bytes([part])
        if not value:
            break
    return out


def create_handshake(host, port, protocol_version=760):
    host_bytes = host.encode("utf-8")
    host_len = write_varint(len(host_bytes))
    pv = write_varint(protocol_version)
    packet = (
        write_varint(0x00)  # packet id
        + pv
        + host_len
        + host_bytes
        + struct.pack(">H", port)
        + write_varint(1)  # next state: status
    )
    return write_varint(len(packet)) + packet


def create_status_request():
    packet = write_varint(0x00)
    return write_varint(len(packet)) + packet


def create_ping_packet(payload=1234567890):
    packet = write_varint(0x01) + struct.pack(">q", payload)
    return write_varint(len(packet)) + packet


def ping_server(host, port, timeout=5):
    start = time.time()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((host, port))

    sock.sendall(create_handshake(host, port))
    sock.sendall(create_status_request())

    # Read status response
    length = read_varint(sock)
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise ConnectionError("Connection closed")
        data += chunk

    packet_id = data[0]
    # parse varint for json length
    idx = 1
    json_len = 0
    shift = 0
    while True:
        b = data[idx]
        idx += 1
        json_len |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7

    json_data = data[idx:idx + json_len].decode("utf-8")
    status = json.loads(json_data)

    # Ping for latency
    ping_start = time.time()
    sock.sendall(create_ping_packet())
    try:
        pong = sock.recv(10)
    except Exception:
        pass
    latency_ms = int((time.time() - ping_start) * 1000)

    sock.close()
    return status, latency_ms


def strip_formatting(text):
    """Remove Minecraft color codes (§x)"""
    result = ""
    i = 0
    while i < len(text):
        if text[i] == "§" and i + 1 < len(text):
            i += 2
        else:
            result += text[i]
            i += 1
    return result


def latency_icon(ms):
    if ms < 100:
        return "🟢"
    elif ms < 200:
        return "🟡"
    else:
        return "🟠"


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <host[:port]> [timeout]")
        sys.exit(1)

    host_port = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 5

    # Parse host:port
    if ":" in host_port:
        host, port_str = host_port.rsplit(":", 1)
        port = int(port_str)
    else:
        host = host_port
        port = 25565

    try:
        status, latency = ping_server(host, port, timeout)

        version = status.get("version", {}).get("name", "Unknown")
        players_online = status.get("players", {}).get("online", 0)
        players_max = status.get("players", {}).get("max", 0)
        motd_raw = status.get("description", {})
        if isinstance(motd_raw, dict):
            motd = motd_raw.get("text", "")
        else:
            motd = str(motd_raw)
        motd = strip_formatting(motd)

        player_list = status.get("players", {}).get("sample", [])
        player_names = [p.get("name", "") for p in player_list[:5]]

        icon = latency_icon(latency)
        print(f"{icon} {host}:{port} - ONLINE ({latency}ms)")
        print(f"   Version: {version}")
        print(f"   Players: {players_online}/{players_max}")
        if player_names:
            print(f"   Online: {', '.join(player_names)}")
        print(f"   MOTD: {motd}")
        sys.exit(0)

    except (socket.timeout, TimeoutError):
        print(f"🔴 {host}:{port} - OFFLINE (timeout)")
        sys.exit(1)
    except ConnectionRefusedError:
        print(f"🔴 {host}:{port} - OFFLINE (connection refused)")
        sys.exit(1)
    except Exception as e:
        print(f"🔴 {host}:{port} - OFFLINE ({e})")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(script_dir, "minecraft-status.py"), "w") as f:
    f.write(minecraft_script)
os.chmod(os.path.join(script_dir, "minecraft-status.py"), 0o755)

# Create the main workspace with a server list config
servers_content = """# Game Server Fleet - Monitoring Targets
# Format: host:port  (one per line, lines starting with # are comments)
# Last updated: 2024-01-15
localhost:25565
localhost:25566
localhost:25999
"""

with open(os.path.join(workspace, "servers_to_monitor.txt"), "w") as f:
    f.write(servers_content)

# Create distractor files to simulate a real ops environment
ops_dir = os.path.join(workspace, "ops")
os.makedirs(ops_dir, exist_ok=True)

logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)

config_dir = os.path.join(workspace, "config")
os.makedirs(config_dir, exist_ok=True)

archive_dir = os.path.join(workspace, "archive", "2023")
os.makedirs(archive_dir, exist_ok=True)

scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

# Distractor 1: Old status report (wrong format, outdated)
old_report = """{
  "generated": "2023-11-01T00:00:00Z",
  "servers": [
    {"host": "old-server.example.com", "status": "unknown"}
  ]
}"""
with open(os.path.join(archive_dir, "old_health_report.json"), "w") as f:
    f.write(old_report)

# Distractor 2: Fake network config
net_config = """[network]
primary_dns = 8.8.8.8
secondary_dns = 8.8.4.4
vpc_cidr = 10.0.0.0/16
timeout_default = 30
"""
with open(os.path.join(config_dir, "network.conf"), "w") as f:
    f.write(net_config)

# Distractor 3: Server inventory (CSV, different format)
inventory = """server_id,hostname,region,type,status
srv-001,game-eu-1.example.com,eu-west-1,game,active
srv-002,game-us-1.example.com,us-east-1,game,active
srv-003,lobby.example.com,us-east-1,lobby,maintenance
srv-004,creative.example.com,ap-south-1,game,unknown
"""
with open(os.path.join(ops_dir, "server_inventory.csv"), "w") as f:
    f.write(inventory)

# Distractor 4: Old bash monitoring script (different tool, wrong approach)
old_bash = """#!/bin/bash
# DEPRECATED - DO NOT USE
# Old ping-based monitor - does not work for Minecraft SLP
for server in $@; do
    ping -c 1 $server > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "$server: reachable"
    else
        echo "$server: unreachable"
    fi
done
"""
with open(os.path.join(scripts_dir, "old_monitor.sh"), "w") as f:
    f.write(old_bash)
os.chmod(os.path.join(scripts_dir, "old_monitor.sh"), 0o755)

# Distractor 5: Python utility that does NOT do SLP
fake_checker = """#!/usr/bin/env python3
# Generic TCP port checker - NOT Minecraft-aware
import socket, sys
host, port = sys.argv[1], int(sys.argv[2])
try:
    s = socket.create_connection((host, port), timeout=3)
    s.close()
    print(f"TCP {host}:{port} OPEN")
except Exception as e:
    print(f"TCP {host}:{port} CLOSED: {e}")
"""
with open(os.path.join(scripts_dir, "tcp_check.py"), "w") as f:
    f.write(fake_checker)

# Distractor 6: Alerts config
alerts_cfg = """[alerts]
slack_webhook = https://hooks.slack.com/DISABLED
email_to = ops@example.com
threshold_players_min = 0
threshold_latency_max = 500
alert_on_offline = true
"""
with open(os.path.join(config_dir, "alerts.cfg"), "w") as f:
    f.write(alerts_cfg)

# Distractor 7: Log files
for i, level in enumerate(["INFO", "WARN", "ERROR"]):
    log_content = f"[2024-01-{10+i:02d}] [{level}] Server check script started\n"
    log_content += f"[2024-01-{10+i:02d}] [{level}] Connection attempt to game-server-{i+1}\n"
    log_content += f"[2024-01-{10+i:02d}] [{level}] Done\n"
    with open(os.path.join(logs_dir, f"monitor_{2024010 + i}.log"), "w") as f:
        f.write(log_content)

# Distractor 8: A requirements.txt suggesting wrong dependencies
reqs = """requests==2.31.0
mcstatus==11.1.0
# NOTE: mcstatus is NOT the tool used in this project
paramiko==3.4.0
boto3==1.34.0
"""
with open(os.path.join(workspace, "requirements_OLD.txt"), "w") as f:
    f.write(reqs)

# Distractor 9: Incomplete notes file
notes = """TODO list (OPS team):
- Update server fleet health check process
- Replace old ping-based monitor with proper Minecraft protocol checker
- Output results as JSON for the dashboard team
- Check servers: localhost:25565, localhost:25566, localhost:25999
- Use 3 second timeout for checks (fast fail for unreachable servers)
- Dashboard expects file named: server_health_report.json
- Fields needed: server address, online status (bool), latency_ms, version, players_online, players_max, motd, player_list
- player_list should be a list of strings
- offline servers should have null for version/players/motd/latency
"""
with open(os.path.join(ops_dir, "TODO_ops_notes.txt"), "w") as f:
    f.write(notes)

# Distractor 10: An old JSON report with wrong schema
wrong_schema = """{
  "timestamp": "2024-01-01",
  "checks": [
    {"address": "localhost:25565", "reachable": true, "rtt": 5}
  ]
}"""
with open(os.path.join(archive_dir, "wrong_schema_report.json"), "w") as f:
    f.write(wrong_schema)

print("Workspace and skill script created successfully.")
print(f"Script path: {script_dir}/minecraft-status.py")
print(f"Server list: {workspace}/servers_to_monitor.txt")