import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic directory structure with distractor files
dirs = [
    "bots/analytics",
    "bots/scrapers",
    "bots/posters",
    "config/rooms",
    "config/credentials",
    "logs/2024-01",
    "logs/2024-02",
    "reports/q1",
    "reports/q2",
    "scripts/utils",
    "scripts/legacy",
    "data/raw",
    "data/processed",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
files = {
    "bots/analytics/user_tracker.py": """# Tracks user activity across sessions
import json

def track_user(screen_name, room, timestamp):
    return {"user": screen_name, "room": room, "ts": timestamp}
""",
    "bots/scrapers/price_scraper.js": """// Scrapes token prices from CMC
const fetch = require('node-fetch');
async function getPrice(token) {
    // TODO: implement
    return null;
}
module.exports = { getPrice };
""",
    "bots/posters/announcement_bot.py": """# Posts announcements to rooms
# DEPRECATED: use new posting API
def post_announcement(room, message):
    pass
""",
    "config/rooms/room_config.yaml": """rooms:
  - id: welcome
    topic: "General welcome room"
    max_users: 100
  - id: mim
    topic: "$MIM token discussion"
    max_users: 50
  - id: rap-battles
    topic: "Freestyle rap battles"
    max_users: 30
""",
    "config/credentials/bot_registry.json": """{
  "registered_bots": [
    {"name": "PriceWatcherBot", "last_seen": "2024-01-15"},
    {"name": "MimTracker99", "last_seen": "2024-02-03"},
    {"name": "CrustBot", "last_seen": "2024-01-28"}
  ]
}
""",
    "logs/2024-01/session_log.txt": """2024-01-10 12:00:01 - PriceWatcherBot connected
2024-01-10 12:00:05 - PriceWatcherBot joined #welcome
2024-01-10 12:01:20 - PriceWatcherBot sent: "gm everyone"
2024-01-10 12:15:00 - PriceWatcherBot disconnected
""",
    "logs/2024-02/session_log.txt": """2024-02-01 09:00:00 - MimTracker99 connected
2024-02-01 09:00:10 - MimTracker99 joined #mim
2024-02-01 09:02:15 - MimTracker99 sent: "MIM to the moon!"
2024-02-01 09:30:00 - MimTracker99 disconnected
""",
    "reports/q1/summary.txt": """Q1 Activity Report
==================
Total messages: 1,243
Active rooms: 4
Peak concurrent bots: 12
""",
    "reports/q2/summary.txt": """Q2 Activity Report
==================
Total messages: 2,891
Active rooms: 5
Peak concurrent bots: 19
""",
    "scripts/utils/format_history.py": """# Utility to format message history for reports
def format_messages(messages):
    result = []
    for msg in messages:
        if msg.get('type') == 'message':
            result.append(f"{msg['screenName']}: {msg['text']}")
    return result
""",
    "scripts/legacy/old_connect.js": """// LEGACY - DO NOT USE
// Old IRC-style connection (deprecated)
const net = require('net');
const client = new net.Socket();
client.connect(6667, 'old-irc-server.example.com', function() {
    client.write('NICK OldBot\\r\\n');
});
""",
    "data/raw/message_dump_jan.jsonl": '\n'.join([
        json.dumps({"id": f"msg_{i}", "room": random.choice(["welcome", "mim", "rap-battles"]),
                    "user": f"Bot{i}", "text": f"Sample message {i}", "ts": 1704067200 + i*60})
        for i in range(20)
    ]),
    "data/processed/aggregated_stats.json": json.dumps({
        "total_rooms": 5,
        "total_messages_indexed": 4134,
        "rooms": {
            "welcome": {"msg_count": 2100, "unique_users": 45},
            "mim": {"msg_count": 890, "unique_users": 23},
            "rap-battles": {"msg_count": 412, "unique_users": 18},
            "crustafarianism": {"msg_count": 321, "unique_users": 12},
            "memes": {"msg_count": 411, "unique_users": 29}
        }
    }, indent=2),
    "scripts/legacy/migrate_logs.sh": """#!/bin/bash
# Migrate old log format to new JSONL format
for f in logs/**/*.txt; do
    echo "Processing $f..."
done
""",
}

for filepath, content in files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# The mission briefing file — gives context but NO technical hints
mission = """MISSION BRIEF: Chat Room Audit Bot
===================================
Date: 2024-03-01
Requestor: Community Analytics Team

We need an automated audit of our MOL Instant Messenger platform.

Objective:
  Connect to our messaging platform, discover which rooms are active,
  find the most active non-default room, retrieve its recent message history,
  and send a brief status update message in that room.

The bot should use the screen name: AuditBot42

Deliverable:
  A file named `chat_report.json` placed anywhere in the workspace.
  
  The report must include:
  - A snapshot of room activity (how many users are in each room)
  - The full message history retrieved from the most active non-default room
  - Confirmation of the screen name used
  - The room ID where the status message was sent

Server connection details are available in the environment variable MOL_IM_SERVER.
"""

with open(os.path.join(workspace, "MISSION.txt"), "w") as f:
    f.write(mission)

print("Workspace generated successfully.")