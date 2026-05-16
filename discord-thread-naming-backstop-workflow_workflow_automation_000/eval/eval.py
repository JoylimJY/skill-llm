import sys
import json
import re
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ── Load mock server request log ──────────────────────────────────────────────
mock_log_path = os.path.join(workspace, "mock_server_requests.jsonl")
mock_requests = []
try:
    with open(mock_log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    mock_requests.append(json.loads(line))
                except:
                    pass
except Exception as e:
    pass

# ── Load agent output log ──────────────────────────────────────────────────────
log_files = list(Path(workspace).rglob("backstop_run_log.json"))
agent_log = None
agent_log_raw = None
if log_files:
    try:
        with open(log_files[0]) as f:
            agent_log_raw = f.read()
            agent_log = json.loads(agent_log_raw)
    except Exception as e:
        agent_log = None

total_score += add_check(
    "output_file_exists",
    agent_log is not None,
    f"backstop_run_log.json found and parseable: {log_files[0] if log_files else 'NOT FOUND'}"
)

# ── CHECK 1: thread-list called with correct parameters ───────────────────────
thread_list_calls = [r for r in mock_requests if r.get("action") == "thread-list"]
tl_correct = False
tl_detail = "No thread-list call found"
for call in thread_list_calls:
    if (call.get("guildId") == "1478785964896817267" and
        call.get("channelId") == "1478785965580357754" and
        call.get("includeArchived") == False and
        call.get("limit") == 50):
        tl_correct = True
        tl_detail = f"Correct thread-list call found: {call}"
        break

if not tl_correct and thread_list_calls:
    tl_detail = f"thread-list called but with wrong params: {thread_list_calls}"

total_score += add_check("thread_list_correct_params", tl_correct, tl_detail, weight=1.5)

# ── CHECK 2: Thread D (historical, 2026-03-13) was NOT processed ──────────────
edit_calls = [r for r in mock_requests if r.get("action") == "channel-edit"]
historical_edited = any(r.get("target") == "1482300000000000004" for r in edit_calls)
total_score += add_check(
    "historical_thread_not_touched",
    not historical_edited,
    "Thread 1482300000000000004 (created 2026-03-13) must NOT be renamed" if not historical_edited else "ERROR: historical thread was renamed"
)

# ── CHECK 3: Thread C (already compliant) was NOT processed ───────────────────
compliant_edited = any(r.get("target") == "1482300000000000003" for r in edit_calls)
total_score += add_check(
    "compliant_thread_not_touched",
    not compliant_edited,
    "Thread 1482300000000000003 (already 【修复】OAuth登录异常 - 20260314) must not be renamed"
)

# ── CHECK 4: Thread E (already compliant, within 20min) was NOT processed ─────
compliant_e_edited = any(r.get("target") == "1482300000000000005" for r in edit_calls)
total_score += add_check(
    "compliant_thread_E_not_touched",
    not compliant_e_edited,
    "Thread 1482300000000000005 (already 【任务】用户权限审查 - 20260314) must not be renamed"
)

# ── CHECK 5: Thread A renamed (JSON-polluted, within 20min) ───────────────────
thread_a_edits = [r for r in edit_calls if r.get("target") == "1482300000000000001"]
thread_a_renamed = len(thread_a_edits) > 0
total_score += add_check(
    "thread_A_was_processed",
    thread_a_renamed,
    f"Thread 1482300000000000001 (JSON-polluted, 12min ago) should be renamed. Edits: {thread_a_edits}"
)

# ── CHECK 6: Thread A new name matches 【运维】...deploy/nginx/service... - 20260314
thread_a_name_correct = False
thread_a_name_detail = "No edit for thread A found"
if thread_a_edits:
    # Any edit attempt (even failed first) — check what name was used
    # The name should be 【运维】<target> - 20260314
    name_used = thread_a_edits[0].get("name", "")
    if (re.match(r'^【运维】.+ - 20260314$', name_used) and
        len(name_used) <= 100):
        # Check target phrase length 8-28
        inner = re.sub(r'^【运维】', '', name_used)
        inner = re.sub(r' - 20260314$', '', inner)
        thread_a_name_correct = 8 <= len(inner) <= 28
        thread_a_name_detail = f"Name: {name_used}, inner phrase: {inner} (len={len(inner)})"
    else:
        thread_a_name_detail = f"Name {name_used!r} does not match 【运维】...20260314 or exceeds 100 chars"

total_score += add_check(
    "thread_A_name_is_correct_type_and_format",
    thread_a_name_correct,
    thread_a_name_detail,
    weight=1.5
)

# ── CHECK 7: Thread A had retry (2 channel-edit calls) due to first failure ────
thread_a_retry = len(thread_a_edits) >= 2
total_score += add_check(
    "thread_A_retry_attempted",
    thread_a_retry,
    f"Thread A should have 2 channel-edit calls (first fails, second succeeds). Got: {len(thread_a_edits)}"
)

# ── CHECK 8: Thread B renamed (long title, within 20min) ──────────────────────
thread_b_edits = [r for r in edit_calls if r.get("target") == "1482300000000000002"]
thread_b_renamed = len(thread_b_edits) > 0
total_score += add_check(
    "thread_B_was_processed",
    thread_b_renamed,
    f"Thread 1482300000000000002 (long title, 5min ago) should be renamed. Edits: {thread_b_edits}"
)

# ── CHECK 9: Thread B new name uses 【运维】 (监控 triggers 运维 priority) ──────
thread_b_name_correct = False
thread_b_name_detail = "No edit for thread B"
if thread_b_edits:
    name_b = thread_b_edits[0].get("name", "")
    if (re.match(r'^【运维】.+ - 20260314$', name_b) and len(name_b) <= 100):
        inner_b = re.sub(r'^【运维】', '', name_b)
        inner_b = re.sub(r' - 20260314$', '', inner_b)
        thread_b_name_correct = 8 <= len(inner_b) <= 28
        thread_b_name_detail = f"Name: {name_b}, inner: {inner_b} (len={len(inner_b)})"
    else:
        thread_b_name_detail = f"Name {name_b!r} wrong type or format"

total_score += add_check(
    "thread_B_name_correct_type",
    thread_b_name_correct,
    thread_b_name_detail,
    weight=1.5
)

# ── CHECK 10: Thread F renamed (today, >20min, but long/口语异常) ──────────────
thread_f_edits = [r for r in edit_calls if r.get("target") == "1482300000000000006"]
thread_f_renamed = len(thread_f_edits) > 0
total_score += add_check(
    "thread_F_was_processed",
    thread_f_renamed,
    f"Thread 1482300000000000006 (today, 50min, long 口语 with 报错/异常) should be renamed. Edits: {thread_f_edits}"
)

# ── CHECK 11: Thread F new name uses 【修复】 (报错/异常/修复 keywords) ───────────
thread_f_name_correct = False
thread_f_name_detail = "No edit for thread F"
if thread_f_edits:
    name_f = thread_f_edits[0].get("name", "")
    if (re.match(r'^【修复】.+ - 20260314$', name_f) and len(name_f) <= 100):
        inner_f = re.sub(r'^【修复】', '', name_f)
        inner_f = re.sub(r' - 20260314$', '', inner_f)
        thread_f_name_correct = 8 <= len(inner_f) <= 28
        thread_f_name_detail = f"Name: {name_f}, inner: {inner_f} (len={len(inner_f)})"
    else:
        thread_f_name_detail = f"Name {name_f!r} wrong type or format (expected 【修复】)"

total_score += add_check(
    "thread_F_name_correct_type",
    thread_f_name_correct,
    thread_f_name_detail,
    weight=1.5
)

# ── CHECK 12: Max 3 threads processed (A, B, F) ───────────────────────────────
all_edited_ids = set(r.get("target") for r in edit_calls if r.get("target"))
total_score += add_check(
    "max_3_threads_processed",
    len(all_edited_ids) <= 3,
    f"At most 3 distinct threads should be renamed. Got: {all_edited_ids}"
)

# ── CHECK 13: opId format in agent log ────────────────────────────────────────
opid_pattern = re.compile(r'^rename-\d+-\d{14}$')
opid_check = False
opid_detail = "Could not find opId fields in log"

if agent_log:
    # Look for opId in various structures
    log_str = json.dumps(agent_log, ensure_ascii=False)
    opids_found = re.findall(r'rename-\d+-\d{14}', log_str)
    if len(opids_found) >= 1:
        opid_check = all(opid_pattern.match(o) for o in opids_found)
        opid_detail = f"Found opIds: {opids_found}"
    else:
        opid_detail = "No opId matching rename-<threadId>-<YYYYMMDDHHmmss> found in log"

total_score += add_check("opid_format_correct", opid_check, opid_detail, weight=1.0)

# ── CHECK 14: RESOLVED notification sent for Thread A (first-fail-then-succeed) ─
send_msg_calls = [r for r in mock_requests if r.get("action") == "send-message"]
resolved_sent = False
resolved_detail = "No send-message calls found"
for msg in send_msg_calls:
    content = msg.get("content", "")
    channel = msg.get("channelId", "") or msg.get("channel_id", "")
    # Check for RESOLVED template or threadId A mention with RESOLVED/回补
    if ("RESOLVED" in content or "回补" in content or "✅" in content):
        if "1482300000000000001" in content:
            if channel == "1478996389727043584":
                resolved_sent = True
                resolved_detail = f"RESOLVED sent to correct channel for thread A"
                break
            else:
                resolved_detail = f"RESOLVED found but wrong channel: {channel}"

# Also check agent log for RESOLVED record
if not resolved_sent and agent_log:
    log_str = json.dumps(agent_log, ensure_ascii=False)
    if "RESOLVED" in log_str and "1482300000000000001" in log_str:
        resolved_sent = True
        resolved_detail = "RESOLVED record found in agent log for thread A"

total_score += add_check(
    "resolved_notification_for_thread_A",
    resolved_sent,
    resolved_detail,
    weight=1.5
)

# ── CHECK 15: No spurious P2 for cleanly-renamed threads (B, F) ───────────────
p2_calls = []
for msg in send_msg_calls:
    content = msg.get("content", "")
    if ("P2" in content or "🚨" in content or "失败" in content) and "RESOLVED" not in content:
        p2_calls.append(msg)

# P2 for B or F would be spurious
spurious_p2 = any(
    "1482300000000000002" in str(m) or "1482300000000000006" in str(m)
    for m in p2_calls
)
total_score += add_check(
    "no_spurious_p2_for_clean_renames",
    not spurious_p2,
    f"No P2 should be fired for threads B/F (clean renames). P2 calls: {p2_calls}"
)

# ── CHECK 16: naming regex compliance of all generated names ──────────────────
NAMING_REGEX = re.compile(r'^【[^】]+】.+ - \d{8}$')
all_new_names = [r.get("name", "") for r in edit_calls if r.get("name")]
bad_names = [n for n in all_new_names if n and not NAMING_REGEX.match(n)]
total_score += add_check(
    "all_generated_names_match_regex",
    len(bad_names) == 0,
    f"All new names must match ^【[^】]+】.+ - \\d{{8}}$. Bad names: {bad_names}",
    weight=1.0
)

# ── CHECK 17: Type whitelist enforced ─────────────────────────────────────────
ALLOWED_TYPES = {"任务", "分析", "阅读", "修复", "运维", "文档", "复盘", "审查", "复核", "评估"}
invalid_types = []
for n in all_new_names:
    m = re.match(r'^【([^】]+)】', n)
    if m and m.group(1) not in ALLOWED_TYPES:
        invalid_types.append((n, m.group(1)))

total_score += add_check(
    "type_from_whitelist",
    len(invalid_types) == 0,
    f"All types must be in whitelist. Invalid: {invalid_types}"
)

# ── Summary ────────────────────────────────────────────────────────────────────
max_score = 1.0 + 1.5 + 1.0 + 1.0 + 1.0 + 1.5 + 1.0 + 1.0 + 1.5 + 1.0 + 1.5 + 1.0 + 1.0 + 1.5 + 1.0 + 1.0 + 1.0
normalized_score = round(min(total_score / max_score, 1.0), 4)

passed = (
    checks[0]["passed"] and  # file exists
    checks[1]["passed"] and  # thread-list params
    checks[4]["passed"] and  # thread A processed
    checks[7]["passed"] and  # thread B processed
    checks[9]["passed"] and  # thread F processed
    checks[11]["passed"] and  # max 3
    checks[14]["passed"] and  # RESOLVED for A
    checks[15]["passed"]   # no spurious P2
)

print(json.dumps({
    "passed": passed,
    "score": normalized_score,
    "checks": checks
}, ensure_ascii=False, indent=2))