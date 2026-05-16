#!/usr/bin/env python3
import sys
import json
import time
import os
import subprocess
import pathlib

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
workspace = pathlib.Path(workspace)

checks = []
score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight

# ---- Wait for capture to have collected data ----
time.sleep(5)

# ---- CHECK 1: Agent script exists ----
agent_scripts = list(workspace.rglob("*.py"))
relay_script = None
for s in agent_scripts:
    # Exclude distractor files in legacy/services/tests dirs
    parts = str(s).split(os.sep)
    skip_dirs = {"legacy", "tests", "services", "scripts", "docs"}
    if not any(d in parts for d in skip_dirs):
        try:
            content = s.read_text()
            if "mqtt" in content.lower() or "paho" in content.lower():
                relay_script = s
                break
        except:
            pass

if relay_script is None:
    # Broader search
    for s in agent_scripts:
        try:
            content = s.read_text()
            if "channel/" in content and "agent/action" in content.lower():
                relay_script = s
                break
        except:
            pass

if relay_script:
    add_check("relay_script_exists", True, f"Found relay script: {relay_script}", weight=1.0)
else:
    add_check("relay_script_exists", False, "No MQTT relay script found in workspace", weight=1.0)

# ---- CHECK 2: Correct topic structure in the script ----
if relay_script:
    try:
        content = relay_script.read_text()
        channel_id = "ch-test-9f3a"
        
        subscribe_topic = f"channel/{channel_id}/user/event"
        publish_topic = f"channel/{channel_id}/agent/action"
        
        # Check for topic patterns (may use f-strings or direct strings)
        has_user_event = (
            "user/event" in content
        )
        has_agent_action = (
            "agent/action" in content
        )
        
        if has_user_event and has_agent_action:
            add_check("correct_mqtt_topics", True,
                      f"Script uses correct asymmetric topics: user/event (subscribe) and agent/action (publish)",
                      weight=2.0)
        elif has_user_event:
            add_check("correct_mqtt_topics", False,
                      "Script has user/event topic but missing agent/action publish topic",
                      weight=2.0)
        elif has_agent_action:
            add_check("correct_mqtt_topics", False,
                      "Script has agent/action topic but missing user/event subscribe topic",
                      weight=2.0)
        else:
            add_check("correct_mqtt_topics", False,
                      f"Script does NOT use correct topics. Missing both 'user/event' and 'agent/action'. Content snippet: {content[:300]}",
                      weight=2.0)
    except Exception as e:
        add_check("correct_mqtt_topics", False, f"Error reading script: {e}", weight=2.0)
else:
    add_check("correct_mqtt_topics", False, "No relay script found to check topics", weight=2.0)

# ---- CHECK 3: Heartbeat format correctness ----
if relay_script:
    try:
        content = relay_script.read_text()
        has_ping_type = '"ping"' in content or "'ping'" in content
        has_agent_role = '"agent"' in content or "'agent'" in content
        has_timestamp = "timestamp" in content
        
        if has_ping_type and has_agent_role and has_timestamp:
            add_check("correct_heartbeat_format", True,
                      "Script includes correct heartbeat format: type=ping, role=agent, timestamp",
                      weight=2.0)
        else:
            missing = []
            if not has_ping_type: missing.append("type='ping'")
            if not has_agent_role: missing.append("role='agent'")
            if not has_timestamp: missing.append("timestamp field")
            add_check("correct_heartbeat_format", False,
                      f"Heartbeat format incorrect. Missing: {', '.join(missing)}",
                      weight=2.0)
    except Exception as e:
        add_check("correct_heartbeat_format", False, f"Error: {e}", weight=2.0)
else:
    add_check("correct_heartbeat_format", False, "No relay script found", weight=2.0)

# ---- CHECK 4: Message reply format correctness ----
if relay_script:
    try:
        content = relay_script.read_text()
        has_message_type = '"message"' in content or "'message'" in content
        has_role_agent = '"agent"' in content or "'agent'" in content
        has_content_field = '"content"' in content or "'content'" in content
        
        if has_message_type and has_role_agent and has_content_field:
            add_check("correct_message_format", True,
                      "Script includes correct message format: type=message, role=agent, content field",
                      weight=2.0)
        else:
            missing = []
            if not has_message_type: missing.append("type='message'")
            if not has_role_agent: missing.append("role='agent'")
            if not has_content_field: missing.append("'content' field")
            add_check("correct_message_format", False,
                      f"Message reply format incorrect. Missing: {', '.join(missing)}",
                      weight=2.0)
    except Exception as e:
        add_check("correct_message_format", False, f"Error: {e}", weight=2.0)
else:
    add_check("correct_message_format", False, "No relay script found", weight=2.0)

# ---- CHECK 5: Does NOT use wrong topics from distractors ----
if relay_script:
    try:
        content = relay_script.read_text()
        uses_wrong_topic_1 = "device/+" in content
        uses_wrong_topic_2 = "room/{room_id}" in content
        uses_wrong_topic_3 = "channel/CHANNEL/messages" in content or "/messages" in content
        
        if not (uses_wrong_topic_1 or uses_wrong_topic_2 or uses_wrong_topic_3):
            add_check("avoids_distractor_topics", True,
                      "Script does not use any legacy/wrong topic formats from distractor files",
                      weight=1.0)
        else:
            used = []
            if uses_wrong_topic_1: used.append("device/+/... (legacy v1)")
            if uses_wrong_topic_2: used.append("room/{room_id}/... (legacy v2)")
            if uses_wrong_topic_3: used.append("channel/.../messages (wrong template)")
            add_check("avoids_distractor_topics", False,
                      f"Script uses wrong legacy topic formats: {', '.join(used)}",
                      weight=1.0)
    except Exception as e:
        add_check("avoids_distractor_topics", False, f"Error: {e}", weight=1.0)
else:
    add_check("avoids_distractor_topics", False, "No relay script found", weight=1.0)

# ---- CHECK 6: Runtime - check captured heartbeats ----
heartbeat_file = pathlib.Path("/tmp/mqtt_capture/heartbeats.jsonl")
try:
    if heartbeat_file.exists() and heartbeat_file.stat().st_size > 0:
        lines = [l for l in heartbeat_file.read_text().strip().split("\n") if l.strip()]
        heartbeats = [json.loads(l) for l in lines]
        
        valid_heartbeats = [
            h for h in heartbeats
            if h.get("type") == "ping"
            and h.get("role") == "agent"
            and isinstance(h.get("timestamp"), (int, float))
            and h["timestamp"] > 0
        ]
        
        if valid_heartbeats:
            add_check("runtime_heartbeat_published", True,
                      f"Agent published {len(valid_heartbeats)} valid heartbeat(s) with correct format to broker",
                      weight=3.0)
        else:
            add_check("runtime_heartbeat_published", False,
                      f"Found {len(heartbeats)} messages in heartbeat file but none match required format (type=ping, role=agent, timestamp). Sample: {heartbeats[:2]}",
                      weight=3.0)
    else:
        add_check("runtime_heartbeat_published", False,
                  "No heartbeats captured. Agent may not have connected or published to broker.",
                  weight=3.0)
except Exception as e:
    add_check("runtime_heartbeat_published", False, f"Error reading heartbeat capture: {e}", weight=3.0)

# ---- CHECK 7: Runtime - check captured reply messages ----
messages_file = pathlib.Path("/tmp/mqtt_capture/agent_messages.jsonl")
try:
    if messages_file.exists() and messages_file.stat().st_size > 0:
        lines = [l for l in messages_file.read_text().strip().split("\n") if l.strip()]
        messages = [json.loads(l) for l in lines]
        
        valid_replies = [
            m for m in messages
            if m.get("type") == "message"
            and m.get("role") == "agent"
            and isinstance(m.get("timestamp"), (int, float))
            and m["timestamp"] > 0
            and "content" in m
            and len(str(m.get("content", ""))) > 0
        ]
        
        if valid_replies:
            add_check("runtime_message_reply_published", True,
                      f"Agent published {len(valid_replies)} valid reply message(s) with correct format. Sample content: '{valid_replies[0]['content'][:60]}'",
                      weight=3.0)
        else:
            add_check("runtime_message_reply_published", False,
                      f"Found {len(messages)} messages but none match required format (type=message, role=agent, timestamp, content). Sample: {messages[:2]}",
                      weight=3.0)
    else:
        add_check("runtime_message_reply_published", False,
                  "No agent reply messages captured. Agent may not have responded to user/event or published to wrong topic.",
                  weight=3.0)
except Exception as e:
    add_check("runtime_message_reply_published", False, f"Error reading message capture: {e}", weight=3.0)

# ---- CHECK 8: Uses channel config from workspace ----
if relay_script:
    try:
        content = relay_script.read_text()
        uses_channel_id = "ch-test-9f3a" in content or "channel_config.json" in content or "channelId" in content
        
        if uses_channel_id:
            add_check("uses_channel_config", True,
                      "Script references channel ID or reads from channel_config.json",
                      weight=1.0)
        else:
            add_check("uses_channel_config", False,
                      "Script does not appear to use the provided channel config. Check that it reads channelId from channel_config.json",
                      weight=1.0)
    except Exception as e:
        add_check("uses_channel_config", False, f"Error: {e}", weight=1.0)
else:
    add_check("uses_channel_config", False, "No relay script found", weight=1.0)

# ---- Final scoring ----
final_score = round(score / total_weight, 3) if total_weight > 0 else 0.0
passed = final_score >= 0.65

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))