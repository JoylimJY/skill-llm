import sys
import json
import hashlib
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def simple_hash(sender_id, content):
    raw = sender_id + content[:50]
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

# ---- Load original incoming messages ----
try:
    with open(os.path.join(workspace, "dispatch/queue/incoming_messages.json")) as f:
        incoming = json.load(f)
    msg_map = {m["event_id"]: m for m in incoming}
except Exception as e:
    checks.append({"name": "load_incoming_messages", "passed": False, "detail": f"Could not load incoming_messages.json: {e}"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

NOW = 1742130020000

# ---- Load original dedup_state (as created by gen_inputs) ----
try:
    with open(os.path.join(workspace, "skills/multi-bot-dedup/dedup_state.json")) as f:
        final_state = json.load(f)
    checks.append({"name": "dedup_state_exists", "passed": True, "detail": "dedup_state.json is readable"})
except Exception as e:
    checks.append({"name": "dedup_state_exists", "passed": False, "detail": f"Could not read dedup_state.json: {e}"})
    final_state = {}

# ---- Find reply_decisions.json anywhere in workspace ----
decision_files = list(Path(workspace).rglob("reply_decisions.json"))
if not decision_files:
    checks.append({"name": "reply_decisions_exists", "passed": False, "detail": "reply_decisions.json not found anywhere in workspace"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

try:
    with open(decision_files[0]) as f:
        decisions_raw = json.load(f)
    checks.append({"name": "reply_decisions_exists", "passed": True, "detail": f"Found at {decision_files[0]}"})
except Exception as e:
    checks.append({"name": "reply_decisions_exists", "passed": False, "detail": f"reply_decisions.json parse error: {e}"})
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# Normalize decisions: list of dicts with event_id and decision fields
# Accept either a list or a dict keyed by event_id
if isinstance(decisions_raw, list):
    decisions = {item["event_id"]: item["decision"].upper().strip() for item in decisions_raw if "event_id" in item and "decision" in item}
elif isinstance(decisions_raw, dict):
    decisions = {k: v.upper().strip() if isinstance(v, str) else v.get("decision","").upper().strip() 
                 for k, v in decisions_raw.items()}
else:
    decisions = {}

# ---- Reconstruct expected decisions ----
# Original state (as created by gen_inputs):
sender_A = "ou_aaa111222333444555"
sender_B = "ou_bbb666777888999000"
sender_C = "ou_ccc_abcdefghijk12"
sender_D = "ou_ddd_newuser_00001"

content_A_prev = "尊敬的客服，我在使用OpenClaw系统时遇到了一个问题，关于多机器人渠道消息重复触发的情况。"
content_B_prev = "系统报错：无法连接到御书房机器人端点，错误代码500，请协助排查。"
content_C_prev = "你好，请问如何配置钦天监机器人的优先级路由？希望能得到详细的解答，谢谢。"

hash_A_orig = simple_hash(sender_A, content_A_prev)
hash_B_orig = simple_hash(sender_B, content_B_prev)
hash_C_orig = simple_hash(sender_C, content_C_prev)

original_state = {
    sender_A: {"last_reply_time": 1742130005000, "last_message_hash": hash_A_orig},
    sender_B: {"last_reply_time": 1742129985000, "last_message_hash": hash_B_orig},
    sender_C: {"last_reply_time": 1742130010000, "last_message_hash": hash_C_orig},
}

# Simulate processing in order, tracking running state:
running_state = {k: dict(v) for k, v in original_state.items()}

expected_decisions = {}
for event in incoming:
    eid = event["event_id"]
    sid = event["sender_id"]
    content = event["content"]
    t = event["received_time"]

    msg_hash = simple_hash(sid, content)

    if sid not in running_state:
        # No record → REPLY, update state
        decision = "REPLY"
        running_state[sid] = {"last_reply_time": t, "last_message_hash": msg_hash}
    else:
        rec = running_state[sid]
        cond1 = True  # sender exists
        cond2 = (t - rec["last_reply_time"]) < 30000
        cond3 = msg_hash == rec["last_message_hash"]
        if cond1 and cond2 and cond3:
            decision = "NO_REPLY"
            # Do NOT update state
        else:
            decision = "REPLY"
            running_state[sid] = {"last_reply_time": t, "last_message_hash": msg_hash}
    expected_decisions[eid] = decision

# ---- Check 2: Decision correctness per event ----
all_decisions_correct = True
for eid, expected in expected_decisions.items():
    agent_decision = decisions.get(eid, "MISSING")
    passed = agent_decision == expected
    if not passed:
        all_decisions_correct = False
    checks.append({
        "name": f"decision_{eid}",
        "passed": passed,
        "detail": f"Expected {expected}, got {agent_decision}"
    })

# ---- Check 3: Final dedup_state.json correctness ----
# Verify that NO_REPLY events did NOT update state, and REPLY events DID update state.
state_checks_passed = True

for event in incoming:
    eid = event["event_id"]
    sid = event["sender_id"]
    content = event["content"]
    t = event["received_time"]
    expected_d = expected_decisions[eid]
    
    if sid not in final_state:
        # Should exist in final state if at least one REPLY was made for this sender
        # Find if any REPLY was expected for this sender
        any_reply = any(
            expected_decisions[e["event_id"]] == "REPLY" and e["sender_id"] == sid
            for e in incoming
        )
        if any_reply:
            checks.append({
                "name": f"state_has_entry_{sid[:12]}",
                "passed": False,
                "detail": f"Sender {sid} should have a state entry after at least one REPLY, but is missing"
            })
            state_checks_passed = False
        continue

# Verify the final state matches running_state (our ground truth)
for sid, expected_rec in running_state.items():
    if sid not in final_state:
        checks.append({
            "name": f"state_entry_{sid[:12]}",
            "passed": False,
            "detail": f"Missing state entry for {sid}"
        })
        state_checks_passed = False
        continue
    
    agent_rec = final_state[sid]
    
    # Check hash
    hash_ok = agent_rec.get("last_message_hash") == expected_rec["last_message_hash"]
    checks.append({
        "name": f"state_hash_{sid[:12]}",
        "passed": hash_ok,
        "detail": f"Expected hash {expected_rec['last_message_hash']}, got {agent_rec.get('last_message_hash')}"
    })
    if not hash_ok:
        state_checks_passed = False

    # Check timestamp
    time_ok = agent_rec.get("last_reply_time") == expected_rec["last_reply_time"]
    checks.append({
        "name": f"state_time_{sid[:12]}",
        "passed": time_ok,
        "detail": f"Expected time {expected_rec['last_reply_time']}, got {agent_rec.get('last_reply_time')}"
    })
    if not time_ok:
        state_checks_passed = False

# ---- Check 4: NO_REPLY events must NOT have modified state to a new timestamp ----
# For evt_001 (sender_A, NO_REPLY), state should still show last_reply_time=1742130005000
no_reply_state_check = True
agent_A_state = final_state.get(sender_A, {})
# After evt_001 NO_REPLY and evt_005 REPLY, the state should reflect the REPLY update
# (running_state already accounts for this). The critical check is that we didn't
# accidentally update on NO_REPLY—this is captured by the hash/time checks above.

# Specific targeted check: evt_001 is NO_REPLY, and evt_005 IS REPLY for sender_A.
# The final state for sender_A should have the hash/time from evt_005, not from original.
content_A_new = "另外，我还想问一下关于去重功能的具体实现方式，文档里描述得不够清晰。"
expected_A_final_hash = simple_hash(sender_A, content_A_new)
agent_A_final_hash = agent_A_state.get("last_message_hash")
a_hash_correct = agent_A_final_hash == expected_A_final_hash
checks.append({
    "name": "state_A_reflects_evt005_not_evt001",
    "passed": a_hash_correct,
    "detail": (
        f"sender_A final hash should reflect evt_005 (new content, REPLY), not evt_001 (NO_REPLY). "
        f"Expected {expected_A_final_hash}, got {agent_A_final_hash}"
    )
})
if not a_hash_correct:
    state_checks_passed = False

# ---- Compute score ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall = all_decisions_correct and state_checks_passed and score >= 0.85

print(json.dumps({
    "passed": overall,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))