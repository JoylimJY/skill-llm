import json
import os
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "skills/multi-bot-dedup",
    "skills/auto-reply",
    "skills/sentiment-filter",
    "config/channels",
    "config/routing",
    "logs/2024-01",
    "logs/2024-02",
    "dispatch/queue",
    "dispatch/archive",
    "docs/internal",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "skills/auto-reply/config.json": json.dumps({"enabled": True, "delay_ms": 200}),
    "skills/sentiment-filter/rules.json": json.dumps({"negative_threshold": 0.7}),
    "config/channels/feishu_bots.json": json.dumps([
        {"bot_id": "binbu", "name": "兵部"},
        {"bot_id": "libu", "name": "吏部"},
        {"bot_id": "libu2", "name": "礼部"},
        {"bot_id": "qintian", "name": "钦天监"},
        {"bot_id": "yushufang", "name": "御书房"},
        {"bot_id": "taiyiyuan", "name": "太医院"},
    ]),
    "config/routing/priority.json": json.dumps({"default": "round-robin", "vip": "first-available"}),
    "logs/2024-01/dispatch.log": "2024-01-15 10:00:00 INFO dispatched msg_001\n2024-01-15 10:00:01 INFO dispatched msg_002\n",
    "logs/2024-02/dispatch.log": "2024-02-20 09:30:00 INFO dispatched msg_099\n",
    "dispatch/queue/pending.json": json.dumps([]),
    "dispatch/archive/2024-02.json": json.dumps({"count": 42}),
    "docs/internal/architecture.md": "# OpenClaw Architecture\nSee internal wiki for details.\n",
    "skills/multi-bot-dedup/SKILL.md": open("/dev/null").read() if False else (
        "# multi-bot-dedup\nSee main documentation for usage.\n"
    ),
}
for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- Core: dedup_state.json with existing records ---
# Timestamps for test design:
# NOW is defined in incoming_messages.json as 1742130020000 (the agent must treat this as current time)
#
# User A (ou_aaa): last_reply_time=1742130005000 → delta=15000ms < 30000 → within window
# User B (ou_bbb): last_reply_time=1742129985000 → delta=35000ms > 30000 → outside window
# User C (ou_ccc): last_reply_time=1742130010000 → delta=10000ms < 30000 → within window
# User D (ou_ddd): NOT in state → no record

# We need to know what hashes will be sent to design the test cases.
# hash is computed as: simple hash of (sender_id + message[:50])
# The SKILL.md says "简单 hash" — we use Python's built-in hash() but that's not stable.
# To be deterministic, we use a SHA256 hex of sender_id+msg[:50], but the SKILL.md doesn't specify.
# We'll use hashlib.md5 as a "simple hash" and define it in SKILL.md context.
# Actually, the SKILL.md says "简单 hash" without specifying algorithm. 
# We'll pre-compute using a specific simple method and bake the expected values into dedup_state.json,
# forcing the agent to derive the same hash from the same inputs.
# We'll use: hashlib.md5((sender_id + content[:50]).encode()).hexdigest()

import hashlib

def simple_hash(sender_id, content):
    raw = sender_id + content[:50]
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

# Message contents for state setup:
content_A_prev = "尊敬的客服，我在使用OpenClaw系统时遇到了一个问题，关于多机器人渠道消息重复触发的情况。"  # >50 chars guaranteed
content_C_prev = "你好，请问如何配置钦天监机器人的优先级路由？希望能得到详细的解答，谢谢。"

sender_A = "ou_aaa111222333444555"
sender_B = "ou_bbb666777888999000"
sender_C = "ou_ccc_abcdefghijk12"
sender_D = "ou_ddd_newuser_00001"

hash_A = simple_hash(sender_A, content_A_prev)
hash_C = simple_hash(sender_C, content_C_prev)
hash_B_prev_content = "系统报错：无法连接到御书房机器人端点，错误代码500，请协助排查。"
hash_B = simple_hash(sender_B, hash_B_prev_content)

dedup_state = {
    sender_A: {
        "last_reply_time": 1742130005000,
        "last_message_hash": hash_A
    },
    sender_B: {
        "last_reply_time": 1742129985000,
        "last_message_hash": hash_B
    },
    sender_C: {
        "last_reply_time": 1742130010000,
        "last_message_hash": hash_C
    }
}

with open(os.path.join(WORKSPACE, "skills/multi-bot-dedup/dedup_state.json"), "w") as f:
    json.dump(dedup_state, f, ensure_ascii=False, indent=2)

# --- Incoming messages batch (the agent must process these) ---
# NOW = 1742130020000
#
# Event 1: sender_A, same content as before (first 50 chars same), time delta=15000ms
#   → All 3 conditions met → NO_REPLY, do NOT update state
#
# Event 2: sender_B, same content as before, time delta=35000ms > 30000ms
#   → Condition 2 fails → REPLY, update state
#
# Event 3: sender_C, DIFFERENT content from stored hash
#   → Condition 3 fails (content hash differs) → REPLY, update state
#
# Event 4: sender_D (not in state)
#   → Condition 1 fails → REPLY, update state (new entry)
#
# Event 5: sender_A again, but with different content (new topic)
#   → Condition 3 fails → REPLY, update state
#   NOTE: This is a SECOND message from sender_A in the batch.
#   The agent must use the UPDATED state (from event 1 which was NO_REPLY, state unchanged)
#   Actually event 1 was NO_REPLY so state for A is still at last_reply_time=1742130005000, hash_A.
#   Event 5: different content → hash differs → REPLY, update state.
#
# Edge case event 6: sender_C again with the ORIGINAL content_C_prev (but state was updated by event 3)
#   After event 3: sender_C state is updated to new hash/time.
#   Event 6 comes with content_C_prev again → hash won't match updated state → REPLY
#
# We'll use current_time = 1742130020000 for all events.

NOW = 1742130020000

content_A_same = content_A_prev  # exact same content → hash will match
content_B_same = hash_B_prev_content  # same content as what was stored
content_C_new = "御书房机器人最近响应很慢，大约需要10秒才能收到回复，影响了我们团队的工作效率。"  # different from content_C_prev
content_D_new = "我是新用户，第一次使用OpenClaw，想了解如何开始配置飞书机器人接入。"
content_A_new = "另外，我还想问一下关于去重功能的具体实现方式，文档里描述得不够清晰。"  # different from content_A_prev
content_C_reprev = content_C_prev  # same as what was originally in state (but state will have been updated by event 3)

incoming_messages = [
    {
        "event_id": "evt_001",
        "sender_id": sender_A,
        "content": content_A_same,
        "received_time": NOW,
        "channel": "binbu"
    },
    {
        "event_id": "evt_002",
        "sender_id": sender_B,
        "content": content_B_same,
        "received_time": NOW,
        "channel": "libu"
    },
    {
        "event_id": "evt_003",
        "sender_id": sender_C,
        "content": content_C_new,
        "received_time": NOW,
        "channel": "qintian"
    },
    {
        "event_id": "evt_004",
        "sender_id": sender_D,
        "content": content_D_new,
        "received_time": NOW,
        "channel": "taiyiyuan"
    },
    {
        "event_id": "evt_005",
        "sender_id": sender_A,
        "content": content_A_new,
        "received_time": NOW,
        "channel": "yushufang"
    },
    {
        "event_id": "evt_006",
        "sender_id": sender_C,
        "content": content_C_reprev,
        "received_time": NOW,
        "channel": "libu2"
    },
]

with open(os.path.join(WORKSPACE, "dispatch/queue/incoming_messages.json"), "w") as f:
    json.dump(incoming_messages, f, ensure_ascii=False, indent=2)

# Also write a processing_context.json with the current time reference
processing_context = {
    "processing_time": NOW,
    "batch_id": "batch_20240315_001",
    "description": "Batch of incoming messages from multiple bot channels requiring deduplication processing"
}
with open(os.path.join(WORKSPACE, "dispatch/queue/processing_context.json"), "w") as f:
    json.dump(processing_context, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"hash_A (sender_A + content_A_prev[:50]): {hash_A}")
print(f"hash_B: {hash_B}")
print(f"hash_C (sender_C + content_C_prev[:50]): {hash_C}")
print(f"Expected decisions: evt_001=NO_REPLY, evt_002=REPLY, evt_003=REPLY, evt_004=REPLY, evt_005=REPLY, evt_006=REPLY")