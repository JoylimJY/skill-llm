import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "workspace/legacy/adapter/v1",
    "workspace/legacy/adapter/v2",
    "workspace/legacy/configs",
    "workspace/services/gateway/handlers",
    "workspace/services/gateway/middleware",
    "workspace/services/auth",
    "workspace/services/logging",
    "workspace/tests/unit",
    "workspace/tests/integration",
    "workspace/docs/api",
    "workspace/docs/guides",
    "workspace/scripts/deploy",
    "workspace/scripts/migrate",
]
for d in dirs:
    pathlib.Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "workspace/legacy/adapter/v1/mqtt_client.py": """\
# Old MQTT client - DO NOT USE
import paho.mqtt.client as mqtt

class LegacyClient:
    TOPIC_IN = 'device/+/telemetry'
    TOPIC_OUT = 'device/+/command'
    HEARTBEAT = {'type': 'heartbeat', 'role': 'device'}

    def connect(self, host, port=1883):
        self.client = mqtt.Client()
        self.client.connect(host, port)
""",
    "workspace/legacy/adapter/v2/bridge.py": """\
# v2 bridge - deprecated
CHANNEL_FORMAT = 'room/{room_id}/messages'
MSG_FORMAT = {'type': 'chat', 'sender': 'bot', 'body': ''}
""",
    "workspace/legacy/configs/settings.json": json.dumps({
        "broker": "mqtt://old-broker.internal:1883",
        "channel": "default",
        "secret": "old-secret-do-not-use",
        "heartbeat_ms": 10000,
        "reconnect_ms": 2000
    }, indent=2),
    "workspace/services/gateway/handlers/message_handler.py": """\
def handle(payload):
    # Wrong format - old system
    return {
        'type': 'response',
        'sender': 'agent',
        'text': payload.get('text', '')
    }
""",
    "workspace/services/gateway/middleware/auth.py": """\
SECRET = 'placeholder'

def verify(channel_id, token):
    return token == SECRET
""",
    "workspace/services/auth/tokens.py": """\
# Token management - not relevant to MQTT
def generate_token(channel_id, secret):
    import hashlib
    return hashlib.md5((channel_id + secret).encode()).hexdigest()
""",
    "workspace/services/logging/logger.py": """\
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('gateway')
""",
    "workspace/tests/unit/test_handler.py": """\
def test_placeholder():
    assert True
""",
    "workspace/tests/integration/test_mqtt.py": """\
# Integration test stub - not implemented
def test_connection():
    pass
""",
    "workspace/docs/api/endpoints.md": """\
# API Endpoints
- GET /status
- POST /message
- DELETE /channel/{id}
""",
    "workspace/docs/guides/setup.md": """\
# Setup Guide
1. Install dependencies
2. Configure environment
3. Start services
""",
    "workspace/scripts/deploy/deploy.sh": """\
#!/bin/bash
echo 'Deploying...'
""",
    "workspace/scripts/migrate/migrate.py": """\
# Database migration script
print('Migrating...')
""",
}

for filepath, content in distractor_files.items():
    p = pathlib.Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

# --- The actual problem config: a partial/wrong config file that the agent must interpret ---
# This gives the agent the channel credentials but with wrong topic templates (to be corrected by skill knowledge)
config = {
    "channelId": "ch-test-9f3a",
    "channelSecret": "secret-xK9pL2mQ",
    "mqttUrl": "ws://localhost:1883",
    "reconnectInterval": 5000,
    "heartbeatInterval": 30000,
    "wrongTopicHint": "use channel/CHANNEL/messages for everything"
}
pathlib.Path("workspace/channel_config.json").write_text(json.dumps(config, indent=2))

# --- A partial/wrong message template file to mislead ---
bad_template = {
    "heartbeat": {
        "type": "heartbeat",
        "role": "bot",
        "ts": 0
    },
    "message": {
        "type": "chat",
        "from": "agent",
        "text": ""
    }
}
pathlib.Path("workspace/message_templates.json").write_text(json.dumps(bad_template, indent=2))

print("Workspace initialized.")
print("Files created:")
for f in sorted(pathlib.Path("workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")