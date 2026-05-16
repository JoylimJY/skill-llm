import sys
import json
import os
import subprocess
from pathlib import Path

workspace = sys.argv[1]

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# -------------------------------------------------------------------
# CHECK 1: The agent must have created a Python script somewhere
# -------------------------------------------------------------------
agent_scripts = list(Path(workspace).rglob("*.py"))
# exclude the skill's own push.py and old_push_broken.py
candidate_scripts = [
    p for p in agent_scripts
    if "openclaw-aligenie-push" not in str(p)
    and "old_push_broken" not in str(p.name)
    and p.name != "__init__.py"
    and "/tmp/" not in str(p)
]

if not candidate_scripts:
    checks.append(make_check("agent_script_exists", False, "No agent-created Python script found in workspace."))
else:
    checks.append(make_check("agent_script_exists", True, f"Found candidate scripts: {[str(p) for p in candidate_scripts]}"))

# -------------------------------------------------------------------
# CHECK 2: Verify that the mock server received a push request
# -------------------------------------------------------------------
received_pushes_file = "/tmp/received_pushes.json"
received_pushes = []

try:
    if os.path.exists(received_pushes_file):
        with open(received_pushes_file, "r") as f:
            received_pushes = json.load(f)
        checks.append(make_check("server_received_push", True, f"Server received {len(received_pushes)} push(es)."))
    else:
        checks.append(make_check("server_received_push", False, "Mock server received no pushes (/tmp/received_pushes.json missing)."))
except Exception as e:
    checks.append(make_check("server_received_push", False, f"Error reading received pushes: {e}"))

# -------------------------------------------------------------------
# CHECK 3: device_type must be "screen" (not "speaker" default)
# -------------------------------------------------------------------
if received_pushes:
    last_push = received_pushes[-1]
    device_type_sent = last_push.get("deviceType", "")
    if device_type_sent == "screen":
        checks.append(make_check("correct_device_type_screen", True, f"deviceType='screen' correctly sent."))
    else:
        checks.append(make_check("correct_device_type_screen", False, f"deviceType='{device_type_sent}' — expected 'screen' for the showroom display device."))
else:
    checks.append(make_check("correct_device_type_screen", False, "No push received, cannot check device_type."))

# -------------------------------------------------------------------
# CHECK 4: open_id must be the SCREEN device OID from TOOLS.md
# -------------------------------------------------------------------
EXPECTED_OPEN_ID = "SCREEN_DEVICE_OID_7X9K2M"
if received_pushes:
    last_push = received_pushes[-1]
    open_id_sent = last_push.get("openId", "")
    if open_id_sent == EXPECTED_OPEN_ID:
        checks.append(make_check("correct_open_id", True, f"openId='{EXPECTED_OPEN_ID}' correctly extracted from TOOLS.md."))
    else:
        checks.append(make_check("correct_open_id", False, f"openId='{open_id_sent}' — expected '{EXPECTED_OPEN_ID}' from TOOLS.md showroom screen device."))
else:
    checks.append(make_check("correct_open_id", False, "No push received, cannot check openId."))

# -------------------------------------------------------------------
# CHECK 5: push_server must be the correct URL from TOOLS.md
# -------------------------------------------------------------------
EXPECTED_SERVER_HOST = "localhost"
EXPECTED_SERVER_PORT = "58472"
if received_pushes:
    # The request reached our server at localhost:58472, so this is implicitly correct.
    # But let's also check the agent's script to verify it's reading from TOOLS.md
    server_check_passed = True  # If we got a push, it hit the right server
    checks.append(make_check("correct_push_server", True, "Push reached the correct server at localhost:58472/push."))
else:
    checks.append(make_check("correct_push_server", False, "No push received at localhost:58472/push."))

# -------------------------------------------------------------------
# CHECK 6: The push text must be a non-trivial, non-empty announcement
# -------------------------------------------------------------------
if received_pushes:
    last_push = received_pushes[-1]
    text_sent = last_push.get("text", "")
    if text_sent and len(text_sent.strip()) >= 3:
        checks.append(make_check("push_text_nonempty", True, f"Push text: '{text_sent}'"))
    else:
        checks.append(make_check("push_text_nonempty", False, f"Push text is empty or too short: '{text_sent}'"))
else:
    checks.append(make_check("push_text_nonempty", False, "No push received, cannot check text."))

# -------------------------------------------------------------------
# CHECK 7: Result JSON file saved by the agent
# -------------------------------------------------------------------
result_files = list(Path(workspace).rglob("push_result.json"))
result_file_found = False
result_data = None

if result_files:
    try:
        with open(result_files[0], "r") as f:
            result_data = json.load(f)
        result_file_found = True
        checks.append(make_check("result_file_exists", True, f"Found push_result.json at {result_files[0]}"))
    except Exception as e:
        checks.append(make_check("result_file_exists", False, f"push_result.json found but unreadable: {e}"))
else:
    checks.append(make_check("result_file_exists", False, "push_result.json not found anywhere in workspace."))

# -------------------------------------------------------------------
# CHECK 8: Result JSON contains success=true and a messageId
# -------------------------------------------------------------------
if result_data is not None:
    success_val = result_data.get("success", False)
    msg_id = result_data.get("messageId", "")
    if success_val is True and msg_id.startswith("msg_"):
        checks.append(make_check("result_json_correct", True, f"Result: success=true, messageId='{msg_id}'"))
    else:
        checks.append(make_check("result_json_correct", False, f"Result JSON missing success=true or valid messageId: {result_data}"))
else:
    checks.append(make_check("result_json_correct", False, "No result_data to check."))

# -------------------------------------------------------------------
# CHECK 9: Agent script uses asyncio / async pattern (not just requests)
# -------------------------------------------------------------------
async_used = False
if candidate_scripts:
    for script_path in candidate_scripts:
        try:
            content = script_path.read_text(encoding="utf-8", errors="ignore")
            if "asyncio" in content or "await" in content or "async def" in content or "run_until_complete" in content:
                async_used = True
                break
        except Exception:
            pass

if async_used:
    checks.append(make_check("async_pattern_used", True, "Agent correctly used async/await pattern as required by the push() function."))
else:
    checks.append(make_check("async_pattern_used", False, "Agent did not use asyncio/await — the push() function is async and must be awaited."))

# -------------------------------------------------------------------
# Final scoring
# -------------------------------------------------------------------
critical_checks = [
    "server_received_push",
    "correct_device_type_screen",
    "correct_open_id",
    "result_file_exists",
    "result_json_correct",
]

passed_count = sum(1 for c in checks if c["passed"])
total_count = len(checks)
score = passed_count / total_count

# Must pass all critical checks to fully pass
critical_passed = all(
    any(c["name"] == cc and c["passed"] for c in checks)
    for cc in critical_checks
)

overall_passed = critical_passed and (passed_count >= 6)

print(json.dumps({
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}, ensure_ascii=False, indent=2))