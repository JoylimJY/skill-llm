import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "scripts",
    "references",
    "config",
    "logs",
    "data/incoming",
    "data/processed",
    "data/archive",
    "tests",
    "docs/internal",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "config/app.yaml": "server:\n  host: 0.0.0.0\n  port: 8080\ndebug: false\n",
    "config/legacy_bot.conf": "[bot]\nid=100001\nprotocol=mtproto\nversion=2\n",
    "logs/2024-01-15.log": "INFO startup\nDEBUG connected\nINFO session ok\n",
    "logs/error.log": "ERROR: null pointer at dispatch.py:88\n",
    "data/archive/old_events.jsonl": json.dumps({"type": "chat", "text": "hello", "from": 99999}) + "\n",
    "docs/internal/architecture.md": "## System Architecture\nSee diagrams in confluence.\n",
    "docs/internal/onboarding.txt": "Welcome! Set up VPN first.\n",
    "tests/test_placeholder.py": "# TODO: write tests\npass\n",
    "tmp/scratch.txt": "user_id=555\ngroup=888\n",
    "data/processed/.gitkeep": "",
    "config/tokens.example": "# example: ONEBOT_TOKEN=mysecrettoken\n",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# --- Mock OneBotClient script (simulates the real script the agent will use) ---
onebot_client_code = '''import os
import json
import requests

class OneBotClient:
    def __init__(self):
        self.http_url = os.environ.get("ONEBOT_HTTP_URL", "http://127.0.0.1:3000")
        self.token = os.environ.get("ONEBOT_TOKEN", "")
        self.headers = {}
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _post(self, endpoint, payload):
        url = f"{self.http_url}/{endpoint}"
        resp = requests.post(url, json=payload, headers=self.headers, timeout=5)
        return resp.json()

    def send_private_msg(self, user_id, message):
        return self._post("send_private_msg", {"user_id": user_id, "message": message})

    def send_group_msg(self, group_id, message):
        return self._post("send_group_msg", {"group_id": group_id, "message": message})

    def get_login_info(self):
        return self._post("get_login_info", {})

    def get_friend_list(self):
        return self._post("get_friend_list", {})

    def get_group_list(self):
        return self._post("get_group_list", {})

    def set_group_kick(self, group_id, user_id):
        return self._post("set_group_kick", {"group_id": group_id, "user_id": user_id})
'''
with open(os.path.join(workspace, "scripts/onebot_client.py"), "w") as f:
    f.write(onebot_client_code)

# --- Mock WebSocket listener script (distractor, not the main task) ---
ws_listener_code = '''import os, asyncio, websockets, json

WS_URL = os.environ.get("ONEBOT_WS_URL", "ws://127.0.0.1:3001")

async def listen():
    async with websockets.connect(WS_URL) as ws:
        while True:
            msg = await ws.recv()
            event = json.loads(msg)
            print(json.dumps(event))

if __name__ == "__main__":
    asyncio.run(listen())
'''
with open(os.path.join(workspace, "scripts/onebot_ws_listener.py"), "w") as f:
    f.write(ws_listener_code)

# --- message-handling reference ---
msg_handling_ref = open(os.path.join(workspace, "references/message-handling.md"), "w")
msg_handling_ref.write("""# OneBot Message Handling

## Message Event Structure

### Private Message
```json
{
  "post_type": "message",
  "message_type": "private",
  "user_id": 123456789,
  "message": "Hello",
  "raw_message": "Hello",
  "message_id": 12345,
  "time": 1234567890
}
```

### Group Message
```json
{
  "post_type": "message",
  "message_type": "group",
  "group_id": 987654321,
  "user_id": 123456789,
  "message": "Hello group",
  "raw_message": "Hello group",
  "message_id": 12345,
  "time": 1234567890
}
```

## Message Segments

### Text
```json
{"type": "text", "data": {"text": "Hello"}}
```

### At (Mention)
```json
{"type": "at", "data": {"qq": "123456789"}}
```

### Image
```json
{"type": "image", "data": {"file": "http://example.com/image.jpg"}}
```

### Reply
```json
{"type": "reply", "data": {"id": "12345"}}
```

## Common Patterns

### 1. Echo Bot (Auto-reply)
```python
async def echo_handler(event):
    if event.get("message") == "ping":
        user_id = event.get("user_id")
        client.send_private_msg(user_id, "pong")
```

### 2. Keyword Response
```python
async def keyword_handler(event):
    message = event.get("message", "")
    
    if "帮助" in message:
        reply = "可用命令: /help, /status, /info"
    elif message.startswith("/"):
        reply = f"执行命令: {message}"
    else:
        return  # Ignore
    
    if event.get("message_type") == "private":
        client.send_private_msg(event["user_id"], reply)
    else:
        client.send_group_msg(event["group_id"], reply)
```

### 3. Group Management
```python
async def admin_handler(event):
    if event.get("message") == "/kick @user":
        group_id = event.get("group_id")
        user_id = extract_user_id(event.get("message"))
        client.set_group_kick(group_id, user_id)
```

## Notice Events

### Group Member Increase
```json
{
  "post_type": "notice",
  "notice_type": "group_increase",
  "group_id": 987654321,
  "user_id": 123456789
}
```

### Group Member Decrease
```json
{
  "post_type": "notice",
  "notice_type": "group_decrease",
  "group_id": 987654321,
  "user_id": 123456789
}
```

### Group Ban
```json
{
  "post_type": "notice",
  "notice_type": "group_ban",
  "group_id": 987654321,
  "user_id": 123456789,
  "duration": 3600
}
```

## Error Handling

### Connection Errors
- Check if OneBot server is running
- Verify WebSocket URL and port
- Check firewall settings

### Authentication Errors
- Verify token is correct
- Check token format (Bearer token)

### Message Errors
- Validate user_id/group_id exists
- Check message format (string or array)
- Verify bot has permission
""")
msg_handling_ref.close()

# --- Raw incoming event batch (messy, mixed types, some ignorable) ---
# These are the events the agent must process
incoming_events = [
    # 1. Private message: "ping" → should reply "pong" to user
    {
        "post_type": "message",
        "message_type": "private",
        "user_id": 111222333,
        "message": "ping",
        "raw_message": "ping",
        "message_id": 1001,
        "time": 1700000001
    },
    # 2. Group message: contains "帮助" → keyword reply to group
    {
        "post_type": "message",
        "message_type": "group",
        "group_id": 500600700,
        "user_id": 444555666,
        "message": "请问帮助在哪里",
        "raw_message": "请问帮助在哪里",
        "message_id": 1002,
        "time": 1700000002
    },
    # 3. Private message: starts with "/" → command reply to user
    {
        "post_type": "message",
        "message_type": "private",
        "user_id": 777888999,
        "message": "/status",
        "raw_message": "/status",
        "message_id": 1003,
        "time": 1700000003
    },
    # 4. Group message: starts with "/" → command reply to group
    {
        "post_type": "message",
        "message_type": "group",
        "group_id": 500600700,
        "user_id": 111222333,
        "message": "/help",
        "raw_message": "/help",
        "message_id": 1004,
        "time": 1700000004
    },
    # 5. Notice event: group_increase → should be recorded but NOT replied to
    {
        "post_type": "notice",
        "notice_type": "group_increase",
        "group_id": 500600700,
        "user_id": 123456789,
        "time": 1700000005
    },
    # 6. Notice event: group_ban with duration → should be recorded but NOT replied to
    {
        "post_type": "notice",
        "notice_type": "group_ban",
        "group_id": 500600700,
        "user_id": 444555666,
        "duration": 3600,
        "time": 1700000006
    },
    # 7. Group message: plain text (no keyword, no slash) → should be IGNORED (no reply)
    {
        "post_type": "message",
        "message_type": "group",
        "group_id": 500600700,
        "user_id": 999000111,
        "message": "晚上吃什么",
        "raw_message": "晚上吃什么",
        "message_id": 1005,
        "time": 1700000007
    },
    # 8. Private message: "ping" from different user → pong
    {
        "post_type": "message",
        "message_type": "private",
        "user_id": 222333444,
        "message": "ping",
        "raw_message": "ping",
        "message_id": 1006,
        "time": 1700000008
    },
    # 9. Group message: contains "帮助" AND starts with content after that — test exact match logic
    {
        "post_type": "message",
        "message_type": "group",
        "group_id": 800900100,
        "user_id": 555444333,
        "message": "帮助我",
        "raw_message": "帮助我",
        "message_id": 1007,
        "time": 1700000009
    },
    # 10. Malformed/unknown post_type → should be silently ignored
    {
        "post_type": "meta_event",
        "meta_event_type": "heartbeat",
        "time": 1700000010
    },
]

with open(os.path.join(workspace, "data/incoming/events_batch.jsonl"), "w") as f:
    for event in incoming_events:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")

# --- Minimal SKILL.md in workspace root (for agent reference) ---
skill_md = """---
name: onebot-adapter
description: Connect OpenClaw to OneBot protocol for QQ bot integration.
version: 1.0.0
---

# OneBot Adapter

Connect OpenClaw to OneBot protocol servers like NapCat for QQ bot functionality.

## Quick Start

### 1. Configure Connection

Set OneBot server URL in environment or config:
```bash
export ONEBOT_WS_URL="ws://127.0.0.1:3001"
export ONEBOT_HTTP_URL="http://127.0.0.1:3000"
export ONEBOT_TOKEN="your-token"
```

### 2. Receive Messages

Use the WebSocket listener script to receive QQ messages:
```bash
python scripts/onebot_ws_listener.py
```

### 3. Send Messages

Use HTTP API to send messages:
```python
from scripts.onebot_client import OneBotClient

client = OneBotClient()
client.send_private_msg(user_id=123456, message="Hello!")
client.send_group_msg(group_id=789012, message="Group message")
```

## Connection Modes

### WebSocket (Recommended)
- Real-time bidirectional communication
- Receives events instantly
- Supports both sending and receiving

### HTTP
- Request-response model
- Good for simple sending
- Requires polling for receiving

## Common Tasks

### Get Login Info
```python
client.get_login_info()
```

### Get Friend/Group List
```python
client.get_friend_list()
client.get_group_list()
```

### Handle Messages
See references/message-handling.md for message parsing and response patterns.

## NapCat Specific

NapCat is a OneBot11 implementation based on NTQQ.

Default ports:
- WebSocket: 3001
- HTTP: 3000
- WebUI: 6099

Token authentication is optional but recommended for public deployments.

## Troubleshooting

**Connection refused**: Check if OneBot server is running and ports are correct.
**Authentication failed**: Verify token matches OneBot server configuration.
**Message not delivered**: Check user_id/group_id exists and bot has permission.
"""
with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

print("Workspace generated successfully.")
print(f"Events batch written: {len(incoming_events)} events")