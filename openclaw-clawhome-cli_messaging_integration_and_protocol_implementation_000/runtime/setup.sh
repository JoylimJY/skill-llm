#!/bin/bash
set -e

# Configure and start a local Mosquitto MQTT broker (WebSocket + TCP)
mkdir -p /etc/mosquitto/conf.d

cat > /etc/mosquitto/conf.d/local.conf << 'EOF'
listener 1883
protocol mqtt
allow_anonymous true

listener 9001
protocol websockets
allow_anonymous true
EOF

# Start mosquitto in background
mosquitto -c /etc/mosquitto/conf.d/local.conf -d
sleep 1

echo "Mosquitto broker started"

# Verify broker is up
nc -z localhost 1883 && echo "MQTT TCP port 1883: OK" || echo "MQTT TCP port 1883: FAILED"
nc -z localhost 9001 && echo "MQTT WS port 9001: OK" || echo "MQTT WS port 9001: FAILED"

# Create a message capture directory
mkdir -p /tmp/mqtt_capture

# Create a capture script that subscribes to agent/action topic and saves messages
cat > /tmp/capture_agent_messages.py << 'PYEOF'
#!/usr/bin/env python3
"""
Subscribes to the agent action topic and captures published messages for evaluation.
Channel ID is read from the config.
"""
import paho.mqtt.client as mqtt
import json
import time
import sys
import os

CHANNEL_ID = "ch-test-9f3a"
CAPTURE_FILE = "/tmp/mqtt_capture/agent_messages.jsonl"
HEARTBEAT_FILE = "/tmp/mqtt_capture/heartbeats.jsonl"
PING_TOPIC = f"channel/{CHANNEL_ID}/agent/action"

received = []
heartbeats = []

def on_connect(client, userdata, flags, rc):
    print(f"Capture client connected with rc={rc}", flush=True)
    client.subscribe(PING_TOPIC)
    print(f"Subscribed to: {PING_TOPIC}", flush=True)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Captured: {payload}", flush=True)
        if payload.get("type") == "ping":
            heartbeats.append(payload)
            with open(HEARTBEAT_FILE, "a") as f:
                f.write(json.dumps(payload) + "\n")
        elif payload.get("type") == "message":
            received.append(payload)
            with open(CAPTURE_FILE, "a") as f:
                f.write(json.dumps(payload) + "\n")
    except Exception as e:
        print(f"Error parsing message: {e}", flush=True)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

# Run for 45 seconds to capture messages
time.sleep(45)
client.loop_stop()
print(f"Capture complete. Messages: {len(received)}, Heartbeats: {len(heartbeats)}", flush=True)
PYEOF
chmod +x /tmp/capture_agent_messages.py

# Start the capture process in background
python3 /tmp/capture_agent_messages.py > /tmp/mqtt_capture/capture.log 2>&1 &
echo "Capture process PID: $!"

# Create a test message injector: will inject a user message after 8 seconds
cat > /tmp/inject_user_message.py << 'PYEOF'
#!/usr/bin/env python3
"""
Injects a fake user message into the user/event topic after a short delay,
simulating a real user sending a message from Clawhome platform.
"""
import paho.mqtt.client as mqtt
import json
import time

CHANNEL_ID = "ch-test-9f3a"
USER_TOPIC = f"channel/{CHANNEL_ID}/user/event"

time.sleep(8)

client = mqtt.Client()
client.connect("localhost", 1883, 60)
client.loop_start()

user_msg = {
    "type": "message",
    "role": "user",
    "timestamp": int(time.time() * 1000),
    "content": "Hello, can you help me with my smart home setup?"
}

result = client.publish(USER_TOPIC, json.dumps(user_msg))
print(f"Injected user message to {USER_TOPIC}: {result.rc}", flush=True)
time.sleep(1)
client.loop_stop()
PYEOF
chmod +x /tmp/inject_user_message.py

python3 /tmp/inject_user_message.py > /tmp/mqtt_capture/inject.log 2>&1 &
echo "Injector PID: $!"

echo "Setup complete. Capture and injector running in background."
echo "Workspace contents:"
find /workspace -type f | sort