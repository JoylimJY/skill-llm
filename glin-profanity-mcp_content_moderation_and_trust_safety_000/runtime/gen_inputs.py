import json
import random
import os
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ---- Create realistic distractor directory structure ----
dirs = [
    "platform/backend/logs",
    "platform/backend/config",
    "platform/frontend/assets",
    "platform/frontend/components",
    "analytics/weekly",
    "analytics/monthly",
    "moderation/policies",
    "moderation/appeals",
    "users/profiles",
    "users/bans",
    "infra/deploy",
    "infra/monitoring",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
(workspace / "platform/backend/config/db_config.yaml").write_text(
    "host: localhost\nport: 5432\nname: gaming_platform\npool_size: 10\n"
)
(workspace / "platform/backend/config/redis.conf").write_text(
    "bind 127.0.0.1\nmaxmemory 256mb\nmaxmemory-policy allkeys-lru\n"
)
(workspace / "platform/backend/logs/app.log").write_text(
    "2024-01-15 10:23:11 INFO Server started\n2024-01-15 10:23:12 INFO Listening on :8080\n"
)
(workspace / "platform/frontend/components/ChatBox.tsx").write_text(
    "import React from 'react';\nexport const ChatBox = () => <div>Chat</div>;\n"
)
(workspace / "analytics/weekly/summary_2024_w02.csv").write_text(
    "metric,value\ndau,12430\nsessions,34200\navg_session_min,23\n"
)
(workspace / "analytics/monthly/report_2024_01.json").write_text(
    json.dumps({"month": "2024-01", "new_users": 4320, "churn_rate": 0.03})
)
(workspace / "moderation/policies/community_guidelines.md").write_text(
    "# Community Guidelines\n\n1. Be respectful\n2. No harassment\n3. No hate speech\n"
)
(workspace / "moderation/appeals/appeal_2024_0115.txt").write_text(
    "User u_4421 appeals ban issued 2024-01-14. Reason: misidentified profanity.\n"
)
(workspace / "users/bans/ban_log.csv").write_text(
    "user_id,ban_date,reason\nu_1102,2024-01-10,harassment\nu_2234,2024-01-12,spam\n"
)
(workspace / "infra/deploy/k8s_deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: chat-service\n"
)
(workspace / "infra/monitoring/alerts.json").write_text(
    json.dumps({"alerts": [{"name": "high_error_rate", "threshold": 0.05}]})
)

# ---- Generate the MAIN INPUT: raw chat logs ----
# Users - some are repeat offenders, some clean
users = [
    "u_1001", "u_1002", "u_1003", "u_1004", "u_1005",
    "u_1006", "u_1007", "u_1008", "u_1009", "u_1010",
    "u_1011", "u_1012",
]

# Mix of clean, profane, and borderline messages
clean_messages = [
    "GG everyone, great match!",
    "Nice shot, well played!",
    "Anyone want to team up for the next round?",
    "This map is awesome, love the new update.",
    "Thanks for the tip, I'll try that strategy.",
    "Congratulations on hitting level 50!",
    "The new weapon balance feels much better.",
    "Looking for a 5th player for ranked.",
    "Good game, close match!",
    "Anyone else experiencing lag on this server?",
    "That combo was incredible, how did you do that?",
    "Respawning, cover me please.",
]

# Explicit profanity (will definitely be flagged)
profane_messages = [
    "What the f*** were you thinking?",
    "You stupid a**hole, stop stealing my kills.",
    "This game is bull****, I quit.",
    "Go to hell you piece of s***.",
    "F*** this team, all noobs.",
    "Absolute b****es on this team.",
]

# Leetspeak / obfuscated profanity (tricky)
obfuscated_messages = [
    "You absolute @$$hole camping in the corner.",
    "f4ck this lag, unplayable right now.",
    "sh1t shot bro, you missed completely.",
    "What a b1tch move, really?",
]

# Borderline messages (context-dependent, will differ by strictness)
borderline_messages = [
    "This is freaking ridiculous, fix the servers.",
    "What the heck is wrong with matchmaking?",
    "Those guys are so damn good, gg.",
    "Crap, I missed the objective again.",
    "That was a hell of a play, respect.",
]

# Build chat log: assign messages to users deterministically
chat_log = []
msg_id = 1000

# Repeat offender: u_1003 sends multiple profane messages
repeat_offenders = {
    "u_1003": profane_messages[:4],
    "u_1007": profane_messages[2:5],
    "u_1010": profane_messages[3:6],
}

# Normal users send clean messages
normal_user_msgs = {
    "u_1001": clean_messages[0:3],
    "u_1002": clean_messages[3:6],
    "u_1004": clean_messages[6:9],
    "u_1005": clean_messages[9:12],
    "u_1006": [clean_messages[0], clean_messages[5], clean_messages[10]],
    "u_1008": [clean_messages[1], clean_messages[4], clean_messages[7]],
    "u_1009": obfuscated_messages[:2],   # obfuscated - moderate violations
    "u_1011": obfuscated_messages[2:4],  # obfuscated - moderate violations
    "u_1012": borderline_messages,       # borderline only
}

all_user_msgs = {**repeat_offenders, **normal_user_msgs}

timestamps_base = 1705276800  # 2024-01-15 00:00:00 UTC
for user_id, messages in all_user_msgs.items():
    for i, msg in enumerate(messages):
        chat_log.append({
            "message_id": f"msg_{msg_id}",
            "user_id": user_id,
            "timestamp": timestamps_base + msg_id * 17,
            "channel": random.choice(["general", "team", "lobby"]),
            "message": msg
        })
        msg_id += 1

# Shuffle deterministically
random.shuffle(chat_log)

# Save as JSON
(workspace / "moderation").mkdir(exist_ok=True)
chat_log_path = workspace / "moderation" / "chat_logs_2024_w03.json"
chat_log_path.write_text(json.dumps(chat_log, indent=2))

# Also save a separate list of borderline messages for strictness comparison
borderline_path = workspace / "moderation" / "borderline_messages.json"
borderline_path.write_text(json.dumps(borderline_messages, indent=2))

print(f"Generated {len(chat_log)} chat messages for {len(all_user_msgs)} users.")
print(f"Chat log: {chat_log_path}")
print(f"Borderline messages: {borderline_path}")
print("Workspace structure created.")