import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
ogp_dir = Path.home() / ".ogp"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ---- Load config.json ----
config_data = None
try:
    config_path = ogp_dir / "config.json"
    config_data = json.loads(config_path.read_text())
    add_check("config.json is valid JSON", True, f"Loaded from {config_path}")
except Exception as e:
    add_check("config.json is valid JSON", False, f"Error: {e}")

# ---- Load peers.json ----
peers_data = None
try:
    peers_path = ogp_dir / "peers.json"
    peers_raw = json.loads(peers_path.read_text())
    # peers.json may be a list or a dict keyed by peer id
    if isinstance(peers_raw, list):
        peers_by_id = {p["id"]: p for p in peers_raw if "id" in p}
    elif isinstance(peers_raw, dict):
        peers_by_id = peers_raw
    else:
        peers_by_id = {}
    peers_data = peers_by_id
    add_check("peers.json is valid JSON", True, f"Loaded {len(peers_by_id)} peers")
except Exception as e:
    add_check("peers.json is valid JSON", False, f"Error: {e}")
    peers_data = {}

# ---- CHECK 1: Global defaults configured in config.json ----
try:
    agent_comms = config_data.get("agentComms", {}) if config_data else {}
    global_policy = agent_comms.get("globalPolicy", {})

    # Expected: general → summary, status-updates → summary
    general_ok = global_policy.get("general", {}).get("level", "").lower() == "summary"
    status_ok = global_policy.get("status-updates", {}).get("level", "").lower() == "summary"

    if general_ok and status_ok:
        add_check(
            "Global policy: general=summary, status-updates=summary",
            True,
            f"globalPolicy found: {json.dumps(global_policy)}"
        )
    else:
        add_check(
            "Global policy: general=summary, status-updates=summary",
            False,
            f"Expected general:summary and status-updates:summary, got: {json.dumps(global_policy)}"
        )
except Exception as e:
    add_check("Global policy: general=summary, status-updates=summary", False, f"Exception: {e}")

# ---- CHECK 2: Global policy notes present ----
try:
    agent_comms = config_data.get("agentComms", {}) if config_data else {}
    # Check for defaultLevel or notes at agentComms level
    notes_field = agent_comms.get("notes", "") or ""
    global_policy = agent_comms.get("globalPolicy", {})
    # notes may be in any topic or at agentComms level
    has_notes = bool(notes_field)
    if not has_notes:
        for topic_val in global_policy.values():
            if isinstance(topic_val, dict) and topic_val.get("notes"):
                has_notes = True
                break
    add_check(
        "Global policy has notes field",
        has_notes,
        f"notes found: {has_notes}. agentComms keys: {list(agent_comms.keys())}"
    )
except Exception as e:
    add_check("Global policy has notes field", False, f"Exception: {e}")

# ---- CHECK 3: ResearchBot-Alpha peer has responsePolicy with memory-management=full ----
ALPHA_ID = "a1b2c3d4e5f6a1b2"
try:
    alpha_peer = peers_data.get(ALPHA_ID, {})
    if not alpha_peer:
        # Try partial match
        for pid, pdata in peers_data.items():
            if ALPHA_ID in pid or pid in ALPHA_ID:
                alpha_peer = pdata
                break
    
    alpha_policy = alpha_peer.get("responsePolicy", {})
    mm_level = alpha_policy.get("memory-management", {}).get("level", "").lower()
    mm_ok = mm_level == "full"

    add_check(
        f"Alpha peer ({ALPHA_ID}): memory-management=full",
        mm_ok,
        f"memory-management policy: {alpha_policy.get('memory-management', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Alpha peer ({ALPHA_ID}): memory-management=full", False, f"Exception: {e}")

# ---- CHECK 4: ResearchBot-Alpha has testing=full ----
try:
    alpha_peer = peers_data.get(ALPHA_ID, {})
    alpha_policy = alpha_peer.get("responsePolicy", {})
    testing_level = alpha_policy.get("testing", {}).get("level", "").lower()
    testing_ok = testing_level == "full"
    add_check(
        f"Alpha peer ({ALPHA_ID}): testing=full",
        testing_ok,
        f"testing policy: {alpha_policy.get('testing', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Alpha peer ({ALPHA_ID}): testing=full", False, f"Exception: {e}")

# ---- CHECK 5: ResearchBot-Alpha has general=full ----
try:
    alpha_peer = peers_data.get(ALPHA_ID, {})
    alpha_policy = alpha_peer.get("responsePolicy", {})
    general_level = alpha_policy.get("general", {}).get("level", "").lower()
    general_ok = general_level == "full"
    add_check(
        f"Alpha peer ({ALPHA_ID}): general=full",
        general_ok,
        f"general policy: {alpha_policy.get('general', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Alpha peer ({ALPHA_ID}): general=full", False, f"Exception: {e}")

# ---- CHECK 6: ResearchBot-Alpha has notes for initial configure ----
try:
    alpha_peer = peers_data.get(ALPHA_ID, {})
    alpha_policy = alpha_peer.get("responsePolicy", {})
    # Notes should be present somewhere in the peer-level config or on the responsePolicy itself
    peer_notes = alpha_peer.get("notes", "") or alpha_peer.get("responsePolicy", {}).get("notes", "")
    # Also accept notes at the agentComms level or per-topic
    has_alpha_notes = bool(peer_notes)
    if not has_alpha_notes:
        for tv in alpha_policy.values():
            if isinstance(tv, dict) and tv.get("notes"):
                has_alpha_notes = True
                break
    add_check(
        f"Alpha peer ({ALPHA_ID}): notes present",
        has_alpha_notes,
        f"peer data keys: {list(alpha_peer.keys())}, policy: {json.dumps(alpha_policy)[:200]}"
    )
except Exception as e:
    add_check(f"Alpha peer ({ALPHA_ID}): notes present", False, f"Exception: {e}")

# ---- CHECK 7: ResearchBot-Alpha has code-review=escalate (added via add-topic) ----
try:
    alpha_peer = peers_data.get(ALPHA_ID, {})
    alpha_policy = alpha_peer.get("responsePolicy", {})
    cr_level = alpha_policy.get("code-review", {}).get("level", "").lower()
    cr_ok = cr_level == "escalate"
    add_check(
        f"Alpha peer ({ALPHA_ID}): code-review=escalate (via add-topic)",
        cr_ok,
        f"code-review policy: {alpha_policy.get('code-review', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Alpha peer ({ALPHA_ID}): code-review=escalate (via add-topic)", False, f"Exception: {e}")

# ---- CHECK 8: DataBot-Beta has general=summary ----
BETA_ID = "9f8e7d6c5b4a9f8e"
try:
    beta_peer = peers_data.get(BETA_ID, {})
    beta_policy = beta_peer.get("responsePolicy", {})
    beta_general = beta_policy.get("general", {}).get("level", "").lower()
    beta_general_ok = beta_general == "summary"
    add_check(
        f"Beta peer ({BETA_ID}): general=summary",
        beta_general_ok,
        f"general policy: {beta_policy.get('general', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Beta peer ({BETA_ID}): general=summary", False, f"Exception: {e}")

# ---- CHECK 9: DataBot-Beta has status-updates=summary ----
try:
    beta_peer = peers_data.get(BETA_ID, {})
    beta_policy = beta_peer.get("responsePolicy", {})
    beta_su = beta_policy.get("status-updates", {}).get("level", "").lower()
    beta_su_ok = beta_su == "summary"
    add_check(
        f"Beta peer ({BETA_ID}): status-updates=summary",
        beta_su_ok,
        f"status-updates policy: {beta_policy.get('status-updates', 'NOT FOUND')}"
    )
except Exception as e:
    add_check(f"Beta peer ({BETA_ID}): status-updates=summary", False, f"Exception: {e}")

# ---- CHECK 10: DataBot-Beta has notes ----
try:
    beta_peer = peers_data.get(BETA_ID, {})
    beta_policy = beta_peer.get("responsePolicy", {})
    peer_notes = beta_peer.get("notes", "") or ""
    has_beta_notes = bool(peer_notes)
    if not has_beta_notes:
        for tv in beta_policy.values():
            if isinstance(tv, dict) and tv.get("notes"):
                has_beta_notes = True
                break
    add_check(
        f"Beta peer ({BETA_ID}): notes present",
        has_beta_notes,
        f"peer data keys: {list(beta_peer.keys())}, policy: {json.dumps(beta_policy)[:200]}"
    )
except Exception as e:
    add_check(f"Beta peer ({BETA_ID}): notes present", False, f"Exception: {e}")

# ---- CHECK 11: Revoked peer (deadbeef) has no responsePolicy set ----
try:
    revoked_peer = peers_data.get("deadbeef12345678", {})
    revoked_policy = revoked_peer.get("responsePolicy", {})
    revoked_clean = not bool(revoked_policy)
    add_check(
        "Revoked peer (deadbeef12345678) was NOT configured",
        revoked_clean,
        f"responsePolicy: {revoked_policy}"
    )
except Exception as e:
    add_check("Revoked peer (deadbeef12345678) was NOT configured", False, f"Exception: {e}")

# ---- CHECK 12: agentComms.activityLog is set in config (optional bonus) ----
try:
    agent_comms = config_data.get("agentComms", {}) if config_data else {}
    activity_log = agent_comms.get("activityLog", None)
    has_activity = activity_log is not None
    add_check(
        "agentComms.activityLog is present in config.json",
        has_activity,
        f"activityLog value: {activity_log}"
    )
except Exception as e:
    add_check("agentComms.activityLog is present in config.json", False, f"Exception: {e}")

# ---- Score calculation ----
# Core checks (weighted more heavily): 1,3,4,5,7,8,9,11 = critical
# Supporting checks: 2,6,10,12 = nice-to-have
critical_check_names = {
    "Global policy: general=summary, status-updates=summary",
    f"Alpha peer ({ALPHA_ID}): memory-management=full",
    f"Alpha peer ({ALPHA_ID}): testing=full",
    f"Alpha peer ({ALPHA_ID}): general=full",
    f"Alpha peer ({ALPHA_ID}): code-review=escalate (via add-topic)",
    f"Beta peer ({BETA_ID}): general=summary",
    f"Beta peer ({BETA_ID}): status-updates=summary",
    "Revoked peer (deadbeef12345678) was NOT configured",
}

critical_passed = sum(1 for c in checks if c["name"] in critical_check_names and c["passed"])
critical_total = len(critical_check_names)
supporting_passed = sum(1 for c in checks if c["name"] not in critical_check_names and c["passed"])
supporting_total = len(checks) - critical_total

# Score: 80% weight on critical, 20% on supporting
if critical_total > 0:
    critical_score = critical_passed / critical_total
else:
    critical_score = 0.0

if supporting_total > 0:
    supporting_score = supporting_passed / supporting_total
else:
    supporting_score = 1.0

score = round(0.8 * critical_score + 0.2 * supporting_score, 3)
passed = critical_passed == critical_total  # Must pass ALL critical checks

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))