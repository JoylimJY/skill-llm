#!/bin/bash
set -e

# --- Start a mock mesh bridge socket server on localhost:7331 ---
# This server handles: send, status, nodes commands
# It logs sent messages to /tmp/mesh_sent.log
# It responds to status and nodes queries

cat > /tmp/mock_bridge_server.py << 'PYEOF'
import socket
import json
import threading
import time
import os

HOST = '127.0.0.1'
PORT = 7331
SENT_LOG = '/tmp/mesh_sent.log'
NODES_FILE = '/tmp/mesh_nodes.json'

def handle_client(conn, addr):
    try:
        data = b''
        conn.settimeout(3.0)
        while True:
            try:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                break
        
        if not data:
            conn.close()
            return
        
        raw = data.decode('utf-8', errors='ignore').strip()
        
        try:
            cmd_obj = json.loads(raw)
        except json.JSONDecodeError:
            conn.sendall(b'{"error":"invalid json"}\n')
            conn.close()
            return
        
        cmd = cmd_obj.get('cmd', '')
        
        if cmd == 'send':
            text = cmd_obj.get('text', '')
            to = cmd_obj.get('to', 'broadcast')
            entry = json.dumps({"cmd": "send", "text": text, "to": to, "ts": time.time()})
            with open(SENT_LOG, 'a') as f:
                f.write(entry + '\n')
            response = {"ok": True, "queued": text, "to": to}
            conn.sendall((json.dumps(response) + '\n').encode())
        
        elif cmd == 'status':
            response = {
                "ok": True,
                "node_id": "!local0001",
                "firmware": "2.3.14",
                "channel": "LongFast",
                "battery": 87,
                "snr": -7.2,
                "bridge_uptime": 3600
            }
            conn.sendall((json.dumps(response) + '\n').encode())
        
        elif cmd == 'nodes':
            try:
                with open(NODES_FILE) as nf:
                    nodes_data = json.load(nf)
                response = {"ok": True, "nodes": nodes_data["nodes"]}
            except Exception as e:
                response = {"ok": False, "error": str(e)}
            conn.sendall((json.dumps(response) + '\n').encode())
        
        elif cmd == 'map':
            enable = cmd_obj.get('enable', None)
            response = {"ok": True, "map_publishing": enable if enable is not None else "toggled"}
            conn.sendall((json.dumps(response) + '\n').encode())
        
        elif cmd == 'map_now':
            response = {"ok": True, "position_reported": True}
            conn.sendall((json.dumps(response) + '\n').encode())
        
        else:
            response = {"ok": False, "error": f"unknown command: {cmd}"}
            conn.sendall((json.dumps(response) + '\n').encode())
    
    except Exception as e:
        try:
            conn.sendall((json.dumps({"error": str(e)}) + '\n').encode())
        except:
            pass
    finally:
        conn.close()

def run_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(20)
        print(f"Mock bridge server listening on {HOST}:{PORT}", flush=True)
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()

if __name__ == '__main__':
    run_server()
PYEOF

# Ensure sent log is clean
rm -f /tmp/mesh_sent.log
touch /tmp/mesh_sent.log

# Start mock server in background
python3 /tmp/mock_bridge_server.py &
BRIDGE_PID=$!
echo "Mock bridge started with PID $BRIDGE_PID"

# Wait for server to be ready
sleep 2

# Verify server is up
if nc -z 127.0.0.1 7331 2>/dev/null; then
    echo "Bridge socket server is ready on 127.0.0.1:7331"
else
    echo "WARNING: Bridge socket may not be ready yet"
fi

# Make scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true

echo "Setup complete."