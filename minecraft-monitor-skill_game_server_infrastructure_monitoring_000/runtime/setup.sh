#!/bin/bash
set -e

# Make the skill script executable
chmod +x ~/.openclaw/workspace/skills/public/minecraft-monitor/scripts/minecraft-status.py

# Write and start mock Minecraft SLP servers

# Mock server on port 25565 (ONLINE - with players)
cat > /tmp/mock_slp_25565.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock Minecraft SLP server on port 25565.
Responds with: version=1.20.4, players=3/20, MOTD=Fleet Server Alpha, sample players
"""
import socket
import json
import struct
import threading

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

def read_varint(data, idx):
    result = 0
    shift = 0
    while True:
        b = data[idx]
        idx += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, idx

def handle_client(conn, addr):
    try:
        conn.settimeout(5)
        data = b""
        # Read enough data for handshake + status request
        while len(data) < 3:
            chunk = conn.recv(1024)
            if not chunk:
                return
            data += chunk
        
        # Consume any additional data
        try:
            while True:
                conn.settimeout(0.1)
                more = conn.recv(1024)
                if not more:
                    break
                data += more
        except:
            pass
        conn.settimeout(5)
        
        # Build status response
        status = {
            "version": {"name": "1.20.4", "protocol": 765},
            "players": {
                "max": 20,
                "online": 3,
                "sample": [
                    {"name": "SteveBuilder", "id": "00000000-0000-0000-0000-000000000001"},
                    {"name": "AlexCrafter", "id": "00000000-0000-0000-0000-000000000002"},
                    {"name": "DiamondMiner", "id": "00000000-0000-0000-0000-000000000003"}
                ]
            },
            "description": {"text": "Fleet Server Alpha"},
            "favicon": ""
        }
        json_bytes = json.dumps(status).encode("utf-8")
        json_len = write_varint(len(json_bytes))
        packet_id = write_varint(0x00)
        packet_body = packet_id + json_len + json_bytes
        packet = write_varint(len(packet_body)) + packet_body
        conn.sendall(packet)
        
        # Handle ping
        try:
            ping_data = conn.recv(10)
            if ping_data and len(ping_data) >= 9:
                # Send pong with same payload
                conn.sendall(ping_data)
        except:
            pass
    except Exception as e:
        pass
    finally:
        try:
            conn.close()
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 25565))
    server.listen(10)
    while True:
        try:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except Exception:
            pass

if __name__ == "__main__":
    main()
MOCK_EOF

# Mock server on port 25566 (ONLINE - empty server)
cat > /tmp/mock_slp_25566.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock Minecraft SLP server on port 25566.
Responds with: version=1.19.4, players=0/50, MOTD=Fleet Server Beta
"""
import socket
import json
import struct
import threading

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

def handle_client(conn, addr):
    try:
        conn.settimeout(5)
        data = b""
        while len(data) < 3:
            chunk = conn.recv(1024)
            if not chunk:
                return
            data += chunk
        try:
            while True:
                conn.settimeout(0.1)
                more = conn.recv(1024)
                if not more:
                    break
                data += more
        except:
            pass
        conn.settimeout(5)
        
        status = {
            "version": {"name": "1.19.4", "protocol": 762},
            "players": {
                "max": 50,
                "online": 0,
                "sample": []
            },
            "description": {"text": "Fleet Server Beta"},
            "favicon": ""
        }
        json_bytes = json.dumps(status).encode("utf-8")
        json_len = write_varint(len(json_bytes))
        packet_id = write_varint(0x00)
        packet_body = packet_id + json_len + json_bytes
        packet = write_varint(len(packet_body)) + packet_body
        conn.sendall(packet)
        
        try:
            ping_data = conn.recv(10)
            if ping_data:
                conn.sendall(ping_data)
        except:
            pass
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 25566))
    server.listen(10)
    while True:
        try:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
        except Exception:
            pass

if __name__ == "__main__":
    main()
MOCK_EOF

# Start both mock servers in background
python3 /tmp/mock_slp_25565.py &
echo $! > /tmp/mock_25565.pid
python3 /tmp/mock_slp_25566.py &
echo $! > /tmp/mock_25566.pid

# Port 25999 intentionally has no server (will be connection refused / timeout)

# Wait for servers to be ready
sleep 2

echo "Mock Minecraft SLP servers started on ports 25565 and 25566"
echo "Port 25999 is intentionally not listening (offline simulation)"