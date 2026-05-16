import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Check 1: tools_message_log.json was created ──────────────────────────────
log_path = Path(workspace) / "tools_message_log.json"
log_entries = []
try:
    with open(log_path, "r") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        log_entries = raw
    elif isinstance(raw, dict):
        log_entries = [raw]
    add_check("tools_message_log_exists", True, f"Found log at {log_path} with {len(log_entries)} entries.")
except FileNotFoundError:
    add_check("tools_message_log_exists", False, f"tools_message_log.json not found at {log_path}. Agent did not call tools.message.")
except json.JSONDecodeError as e:
    add_check("tools_message_log_exists", False, f"tools_message_log.json is malformed JSON: {e}")

# ── Check 2: tools.message called with action="send" ─────────────────────────
msg_entry = None
if log_entries:
    for entry in log_entries:
        params = entry.get("params", {})
        if params.get("action") == "send":
            msg_entry = entry
            break
    if msg_entry:
        add_check("tools_message_action_send", True, "Found tools.message call with action='send'.")
    else:
        add_check("tools_message_action_send", False,
                  f"No tools.message entry with action='send' found. Entries: {log_entries}")
else:
    add_check("tools_message_action_send", False, "No log entries found to check.")

# ── Check 3: channel="feishu" ────────────────────────────────────────────────
if msg_entry:
    channel = msg_entry.get("params", {}).get("channel", "")
    if channel == "feishu":
        add_check("tools_message_channel_feishu", True, "channel='feishu' correctly set.")
    else:
        add_check("tools_message_channel_feishu", False, f"channel='{channel}', expected 'feishu'.")
else:
    add_check("tools_message_channel_feishu", False, "No valid message entry to inspect.")

# ── Check 4: target = correct sender_id from incident_context.json ───────────
EXPECTED_SENDER_ID = "ou_8f2a3b4c5d6e7f8a9b0c1d2e"
if msg_entry:
    target = msg_entry.get("params", {}).get("target", "")
    if target == EXPECTED_SENDER_ID:
        add_check("tools_message_target_sender_id", True, f"target='{target}' matches expected sender_id.")
    else:
        add_check("tools_message_target_sender_id", False,
                  f"target='{target}', expected '{EXPECTED_SENDER_ID}'.")
else:
    add_check("tools_message_target_sender_id", False, "No valid message entry to inspect.")

# ── Check 5: message = "充值二维码" ─────────────────────────────────────────
if msg_entry:
    message = msg_entry.get("params", {}).get("message", "")
    if message == "充值二维码":
        add_check("tools_message_text_correct", True, "message='充值二维码' is correct.")
    else:
        add_check("tools_message_text_correct", False,
                  f"message='{message}', expected '充值二维码'.")
else:
    add_check("tools_message_text_correct", False, "No valid message entry to inspect.")

# ── Check 6: filePath points to an existing QR code file ─────────────────────
if msg_entry:
    fp = msg_entry.get("params", {}).get("filePath", "")
    if fp and os.path.isfile(fp):
        add_check("tools_message_filepath_valid", True, f"filePath='{fp}' exists on disk.")
    elif fp:
        add_check("tools_message_filepath_valid", False,
                  f"filePath='{fp}' was provided but file does not exist.")
    else:
        add_check("tools_message_filepath_valid", False, "filePath is empty or missing from tools.message call.")
else:
    add_check("tools_message_filepath_valid", False, "No valid message entry to inspect.")

# ── Check 7: filePath is under the qrcodes/ directory (qrcode.js --save was used) ──
if msg_entry:
    fp = msg_entry.get("params", {}).get("filePath", "")
    qrcodes_dir = str(Path(workspace) / "qrcodes")
    if fp and fp.startswith(qrcodes_dir):
        add_check("qrcode_js_save_flag_used", True,
                  f"filePath '{fp}' is inside qrcodes/ directory — confirms --save flag was used.")
    elif fp:
        add_check("qrcode_js_save_flag_used", False,
                  f"filePath '{fp}' is NOT inside expected qrcodes/ directory '{qrcodes_dir}'. "
                  "Agent may not have used qrcode.js --save correctly.")
    else:
        add_check("qrcode_js_save_flag_used", False, "No filePath to validate.")
else:
    add_check("qrcode_js_save_flag_used", False, "No valid message entry to inspect.")

# ── Check 8: The payUrl from queryPurchaseDetail was used for QR generation ───
EXPECTED_PAY_URL = "https://pay.duxiaoman.com/qr?product=weather-std&token=TK_abc123xyz987"
if msg_entry:
    fp = msg_entry.get("params", {}).get("filePath", "")
    # qrcode.js creates filename based on md5 of the URL; verify by re-checking expected filename
    import hashlib
    expected_hash = hashlib.md5(EXPECTED_PAY_URL.encode()).hexdigest()[:12]
    expected_filename = f"qr_{expected_hash}.png"
    if fp and os.path.basename(fp) == expected_filename:
        add_check("correct_payurl_used_for_qr", True,
                  f"QR file '{os.path.basename(fp)}' matches hash of expected payUrl.")
    elif fp:
        add_check("correct_payurl_used_for_qr", False,
                  f"QR filename '{os.path.basename(fp)}' does not match expected '{expected_filename}'. "
                  "Wrong URL may have been used, or qrcode.js was not called correctly.")
    else:
        add_check("correct_payurl_used_for_qr", False, "No filePath to validate payUrl derivation.")
else:
    add_check("correct_payurl_used_for_qr", False, "No valid message entry.")

# ── Check 9: Agent produced output mentioning 余额不足 / 微信扫描 guidance ────
# Look for any text file or stdout log the agent may have written as its final response.
# We'll check a few candidate locations: agent_output.txt, response.txt, output.txt, final_response.txt
output_text = ""
candidate_files = [
    "agent_output.txt", "response.txt", "output.txt", "final_response.txt",
    "result.txt", "answer.txt", "reply.txt"
]
for fname in candidate_files:
    cpath = Path(workspace) / fname
    if cpath.exists():
        try:
            output_text = cpath.read_text(encoding="utf-8")
            break
        except Exception:
            pass

if not output_text:
    # Try to find any recently created .txt file
    txt_files = list(Path(workspace).glob("*.txt"))
    if txt_files:
        try:
            output_text = txt_files[0].read_text(encoding="utf-8")
        except Exception:
            pass

# Check for required guidance phrase (余额不足 and 微信扫描 and 二维码)
guidance_keywords = ["余额不足", "微信扫描", "二维码"]
if output_text:
    found_kws = [kw for kw in guidance_keywords if kw in output_text]
    if len(found_kws) == len(guidance_keywords):
        add_check("guidance_text_present", True,
                  f"Output text contains all required guidance keywords: {found_kws}.")
    else:
        missing = [kw for kw in guidance_keywords if kw not in output_text]
        add_check("guidance_text_present", False,
                  f"Output text missing guidance keywords: {missing}. Found text snippet: {output_text[:300]}")
else:
    # Partial credit path: if the tools message was sent correctly, downgrade this to a warning
    add_check("guidance_text_present", False,
              "No agent output text file found (agent_output.txt / response.txt / etc.). "
              "Cannot verify guidance message was shown to user.")

# ── Check 10: Product info present in output (name + price) ──────────────────
product_keywords = ["天气数据查询服务", "99.00", "100次"]
if output_text:
    found_prod = [kw for kw in product_keywords if kw in output_text]
    if len(found_prod) >= 2:
        add_check("product_info_in_output", True,
                  f"Output contains product details: {found_prod}.")
    else:
        add_check("product_info_in_output", False,
                  f"Output missing product info. Found: {found_prod}. Expected at least 2 of: {product_keywords}.")
else:
    add_check("product_info_in_output", False,
              "No output text found; cannot verify product info was presented to user.")

# ── Scoring ───────────────────────────────────────────────────────────────────
# Weights: core workflow checks (1-8) = 0.8, presentation checks (9-10) = 0.2
core_checks = checks[:8]
pres_checks = checks[8:]

core_passed = sum(1 for c in core_checks if c["passed"])
pres_passed = sum(1 for c in pres_checks if c["passed"])

core_score = (core_passed / len(core_checks)) * 0.8
pres_score = (pres_passed / len(pres_checks)) * 0.2 if pres_checks else 0.0
total_score = round(core_score + pres_score, 4)

all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": total_score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))