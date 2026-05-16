#!/usr/bin/env python3
"""
Evaluation script for the am agent-messenger task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import os
import json
import toml
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA   = Path(os.environ.get("XDG_DATA_HOME",   Path.home() / ".local/share"))

CONFIG_FILE    = XDG_CONFIG / "am" / "config.toml"
IDENTITIES_DIR = XDG_DATA   / "am" / "identities"
SEND_LOG       = XDG_DATA   / "am" / "send_log.jsonl"

PARTNER_NPUB   = "npub1qqqqxyz9partner0000000000000000000000000000000000000000000099"

def deterministic_npub(name: str) -> str:
    import hashlib
    h = hashlib.sha256(f"mock-identity-{name}".encode()).hexdigest()[:40]
    return f"npub1{h}"

COORDINATOR_NPUB = deterministic_npub("coordinator")
ANALYST_NPUB     = deterministic_npub("analyst")

checks = []
score_total = 0.0
score_weights = {
    "analyst_identity_exists":      10.0,
    "coordinator_identity_exists":  10.0,
    "two_relays_configured":        10.0,
    "default_identity_coordinator": 15.0,
    "send_used_coordinator":        20.0,
    "send_to_partner_npub":         15.0,
    "send_payload_is_json":         10.0,
    "task_responses_file_exists":   5.0,
    "task_responses_correct_count": 5.0,
    "task_responses_correct_content": 10.0,
}
max_score = sum(score_weights.values())


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    if passed:
        return score_weights.get(name, 0.0)
    return 0.0


# ── 1. Analyst identity exists ───────────────────────────────
try:
    analyst_file = IDENTITIES_DIR / "analyst.nsec"
    assert analyst_file.exists(), "analyst.nsec not found"
    data = json.loads(analyst_file.read_text())
    assert data.get("npub") == ANALYST_NPUB, f"npub mismatch: {data.get('npub')} != {ANALYST_NPUB}"
    score_total += add_check("analyst_identity_exists", True,
        f"analyst identity found with correct npub {ANALYST_NPUB}")
except Exception as e:
    add_check("analyst_identity_exists", False, str(e))

# ── 2. Coordinator identity exists ───────────────────────────
try:
    coord_file = IDENTITIES_DIR / "coordinator.nsec"
    assert coord_file.exists(), "coordinator.nsec not found"
    data = json.loads(coord_file.read_text())
    assert data.get("npub") == COORDINATOR_NPUB, f"npub mismatch: {data.get('npub')} != {COORDINATOR_NPUB}"
    score_total += add_check("coordinator_identity_exists", True,
        f"coordinator identity found with correct npub {COORDINATOR_NPUB}")
except Exception as e:
    add_check("coordinator_identity_exists", False, str(e))

# ── 3. At least two relays configured ────────────────────────
try:
    assert CONFIG_FILE.exists(), "config.toml not found"
    cfg = toml.loads(CONFIG_FILE.read_text())
    relays = cfg.get("relays", [])
    assert len(relays) >= 2, f"Expected >= 2 relays, found {len(relays)}: {relays}"
    score_total += add_check("two_relays_configured", True,
        f"Relays configured: {relays}")
except Exception as e:
    add_check("two_relays_configured", False, str(e))

# ── 4. Default identity is coordinator ───────────────────────
try:
    assert CONFIG_FILE.exists(), "config.toml not found"
    cfg = toml.loads(CONFIG_FILE.read_text())
    default_id = cfg.get("default_identity", "")
    assert default_id == "coordinator", f"default_identity is '{default_id}', expected 'coordinator'"
    score_total += add_check("default_identity_coordinator", True,
        f"default_identity correctly set to 'coordinator'")
except Exception as e:
    add_check("default_identity_coordinator", False, str(e))

# ── 5-7. Send log: used coordinator identity, correct npub, valid JSON payload ──
send_records = []
try:
    assert SEND_LOG.exists(), "send_log.jsonl not found — no sends recorded"
    with open(SEND_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    send_records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    assert len(send_records) > 0, "send_log.jsonl is empty"
except Exception as e:
    add_check("send_used_coordinator", False, str(e))
    add_check("send_to_partner_npub", False, str(e))
    add_check("send_payload_is_json", False, str(e))
    send_records = []

if send_records:
    # Find any record that sent to partner npub using coordinator identity
    matching = [r for r in send_records if r.get("to") == PARTNER_NPUB]

    # Check coordinator identity usage
    coord_sends = [r for r in send_records if r.get("from_identity") == "coordinator"]
    if coord_sends:
        score_total += add_check("send_used_coordinator", True,
            f"Found send(s) using 'coordinator' identity: {len(coord_sends)} record(s)")
    else:
        add_check("send_used_coordinator", False,
            f"No sends found using 'coordinator' identity. Send records: {send_records}")

    # Check sent to partner npub
    if matching:
        score_total += add_check("send_to_partner_npub", True,
            f"Found send to partner npub {PARTNER_NPUB}")
    else:
        add_check("send_to_partner_npub", False,
            f"No send found to partner npub {PARTNER_NPUB}. Sends: {[r.get('to') for r in send_records]}")

    # Check that the payload to partner is valid JSON with expected task structure
    task_sends = [r for r in matching if r.get("from_identity") == "coordinator"]
    json_payload_ok = False
    for rec in task_sends:
        content = rec.get("content", "")
        try:
            parsed = json.loads(content)
            if "task_id" in parsed and "type" in parsed:
                json_payload_ok = True
                break
        except (json.JSONDecodeError, TypeError):
            pass
    if json_payload_ok:
        score_total += add_check("send_payload_is_json", True,
            "Payload sent to partner is valid JSON with task_id and type fields")
    else:
        add_check("send_payload_is_json", False,
            f"Payload to partner is not a valid JSON task object. Matching records: {task_sends}")

# ── 8-10. task_responses.json ─────────────────────────────────
import hashlib

# The pre-seeded inbox last 5 messages (--once --limit 5)
INBOX_ALL = [
    {"from": "npub1sender_aaa000000000000000000000000000000000000000000000000001",
     "content": json.dumps({"task_id": f"t-{8990+k}", "status": "completed", "result": f"pattern_{k}_found"}),
     "created_at": 1700000000 + k * 60,
     "event_id": hashlib.sha256(f"inbox-event-{k}".encode()).hexdigest()}
    for k in range(10)
]
EXPECTED_LAST_5 = INBOX_ALL[-5:]  # last 5 = indices 5..9
EXPECTED_CONTENTS = [json.loads(m["content"]) for m in EXPECTED_LAST_5]

# Search for task_responses.json
try:
    candidates = list(workspace.rglob("task_responses.json"))
    assert len(candidates) > 0, "task_responses.json not found anywhere in workspace"
    resp_file = candidates[0]
    raw = resp_file.read_text().strip()
    parsed = json.loads(raw)
    score_total += add_check("task_responses_file_exists", True,
        f"task_responses.json found at {resp_file}")

    # Count check
    is_list = isinstance(parsed, list)
    count_ok = is_list and len(parsed) == 5
    if count_ok:
        score_total += add_check("task_responses_correct_count", True,
            f"task_responses.json contains exactly 5 entries")
    else:
        add_check("task_responses_correct_count", False,
            f"Expected list of 5, got: {type(parsed).__name__} len={len(parsed) if is_list else 'N/A'}")

    # Content check — each entry should be the `content` field from the last 5 messages
    # Accept either: list of parsed JSON objects OR list of raw JSON strings
    if is_list and len(parsed) == 5:
        content_ok = True
        mismatches = []
        for i, (actual, expected) in enumerate(zip(parsed, EXPECTED_CONTENTS)):
            # actual might be a dict or a JSON string
            if isinstance(actual, str):
                try:
                    actual = json.loads(actual)
                except Exception:
                    pass
            if actual != expected:
                content_ok = False
                mismatches.append(f"[{i}] got {actual} != expected {expected}")
        if content_ok:
            score_total += add_check("task_responses_correct_content", True,
                "All 5 content payloads match the expected inbox messages (last 5 of 10)")
        else:
            add_check("task_responses_correct_content", False,
                f"Content mismatches: {mismatches[:3]}")
    else:
        add_check("task_responses_correct_content", False,
            "Cannot check content — count check failed")

except Exception as e:
    add_check("task_responses_file_exists",    False, str(e))
    add_check("task_responses_correct_count",  False, "file not found")
    add_check("task_responses_correct_content","False", "file not found")

# ── Final result ──────────────────────────────────────────────
final_score = round(score_total / max_score, 4)
passed = final_score >= 0.75 and all(
    c["passed"] for c in checks
    if c["name"] in ("analyst_identity_exists", "coordinator_identity_exists",
                     "two_relays_configured", "default_identity_coordinator",
                     "send_used_coordinator", "send_to_partner_npub")
)

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, indent=2))