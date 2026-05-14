import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    MAX_SCORE = 9.0  # sum of all weights

    # ── CHECK 1: relay-workspace/agent/agent.json exists (setup.sh was run) ──
    relay_agent_json = ws / "relay-workspace" / "agent" / "agent.json"
    try:
        content = json.loads(relay_agent_json.read_text())
        is_relay = content.get("id") == "wa-relay" and content.get("role") == "relay"
        owner_phone = content.get("owner_phone", "")
        add_check(
            "relay_workspace_created",
            is_relay,
            f"relay-workspace/agent/agent.json found; id={content.get('id')}, role={content.get('role')}",
            weight=1.0
        )
    except Exception as e:
        add_check("relay_workspace_created", False, f"relay-workspace/agent/agent.json missing or malformed: {e}", weight=1.0)
        owner_phone = ""

    # ── CHECK 2: owner phone is in international format ──────────────────────
    try:
        if not owner_phone:
            # Try to read from routing config
            routing_candidates = list(ws.rglob("wa-relay-routing.yaml"))
            if routing_candidates:
                import re as _re
                text = routing_candidates[0].read_text()
                m = _re.search(r'owner_phone:\s*"([^"]+)"', text)
                if m:
                    owner_phone = m.group(1)

        phone_valid = bool(re.match(r'^\+[0-9]{7,15}$', owner_phone))
        add_check(
            "owner_phone_international_format",
            phone_valid,
            f"owner_phone detected: '{owner_phone}'; must match +[7-15 digits]",
            weight=1.5
        )
    except Exception as e:
        add_check("owner_phone_international_format", False, f"Could not verify owner phone: {e}", weight=1.5)

    # ── CHECK 3: auth-profiles.json copied to relay workspace ────────────────
    relay_auth = ws / "relay-workspace" / "agent" / "auth-profiles.json"
    try:
        auth_content = json.loads(relay_auth.read_text())
        orig_auth = json.loads((ws / "openclaw" / "agents" / "main-agent" / "auth" / "auth-profiles.json").read_text())
        auth_copied = auth_content == orig_auth
        add_check(
            "auth_credentials_copied",
            auth_copied,
            f"auth-profiles.json in relay workspace: {'matches original' if auth_copied else 'differs from original'}",
            weight=1.0
        )
    except Exception as e:
        add_check("auth_credentials_copied", False, f"relay-workspace/agent/auth-profiles.json missing or unreadable: {e}", weight=1.0)

    # ── CHECK 4: SAFE_SESSION_ID_RE patched to allow : and + ─────────────────
    dist_core = ws / "openclaw" / "dist" / "openclaw.core.js"
    try:
        core_text = dist_core.read_text()
        # The patched regex must allow : and + characters
        has_colon = ":" in core_text.split("SAFE_SESSION_ID_RE")[1][:60] if "SAFE_SESSION_ID_RE" in core_text else False
        has_plus = "+" in core_text.split("SAFE_SESSION_ID_RE")[1][:60] if "SAFE_SESSION_ID_RE" in core_text else False
        # More robust: check that original restrictive pattern is gone
        original_strict = bool(re.search(r'SAFE_SESSION_ID_RE\s*=\s*/\^\\?\\[a-zA-Z0-9_\\\\-\\]', core_text))
        # Check that new pattern includes : and +
        has_extended = bool(re.search(r'SAFE_SESSION_ID_RE.*[:\+]', core_text))
        patched = has_extended and not original_strict
        add_check(
            "session_id_regex_patched",
            patched,
            f"openclaw.core.js SAFE_SESSION_ID_RE patched: has_extended={has_extended}, original_strict_pattern_present={original_strict}",
            weight=1.5
        )
    except Exception as e:
        add_check("session_id_regex_patched", False, f"Could not read/inspect openclaw.core.js: {e}", weight=1.5)

    # ── CHECK 5: .bak backup created for dist file ───────────────────────────
    dist_bak = ws / "openclaw" / "dist" / "openclaw.core.js.bak"
    bak_exists = dist_bak.exists()
    add_check(
        "dist_bak_created",
        bak_exists,
        f"openclaw.core.js.bak backup: {'found' if bak_exists else 'NOT found'}",
        weight=0.5
    )

    # ── CHECK 6: SOUL.md has "Relay de WhatsApp" section ─────────────────────
    soul_file = ws / "openclaw" / "agents" / "main-agent" / "SOUL.md"
    try:
        soul_text = soul_file.read_text()
        has_relay_section = "Relay de WhatsApp" in soul_text
        has_no_reply = "NO_REPLY" in soul_text or "no_reply" in soul_text.lower() or "propietario" in soul_text
        soul_ok = has_relay_section and has_no_reply
        add_check(
            "soul_md_relay_section",
            soul_ok,
            f"SOUL.md relay section: has_relay_section={has_relay_section}, has_no_reply_or_owner_ref={has_no_reply}",
            weight=1.0
        )
    except Exception as e:
        add_check("soul_md_relay_section", False, f"Could not read SOUL.md: {e}", weight=1.0)

    # ── CHECK 7: wa-relay-routing.yaml generated by configure.sh ─────────────
    try:
        routing_file = ws / "config" / "routing" / "wa-relay-routing.yaml"
        routing_text = routing_file.read_text()
        has_version = 'version: "0.2.0"' in routing_text or "version: '0.2.0'" in routing_text or 'version: "0.2.0"' in routing_text
        has_relay_agent = "relay_agent_id" in routing_text and "wa-relay" in routing_text
        has_no_reply = "NO_REPLY" in routing_text
        has_main_session = "main-agent" in routing_text
        routing_ok = has_relay_agent and has_no_reply and has_main_session
        add_check(
            "routing_config_applied",
            routing_ok,
            f"config/routing/wa-relay-routing.yaml: has_relay_agent={has_relay_agent}, has_NO_REPLY={has_no_reply}, has_main_session={has_main_session}",
            weight=1.5
        )
    except Exception as e:
        add_check("routing_config_applied", False, f"config/routing/wa-relay-routing.yaml missing or unreadable: {e}", weight=1.5)

    # ── CHECK 8: direct allowlist contains the expected VIP numbers ───────────
    try:
        routing_file = ws / "config" / "routing" / "wa-relay-routing.yaml"
        routing_text = routing_file.read_text()
        # Expected VIP numbers from the prompt
        vip1 = "+447700900111"
        vip2 = "+12025550173"
        has_vip1 = vip1 in routing_text
        has_vip2 = vip2 in routing_text
        allowlist_ok = has_vip1 and has_vip2
        add_check(
            "direct_allowlist_vip_numbers",
            allowlist_ok,
            f"direct_allowlist in routing config: vip1={vip1} found={has_vip1}, vip2={vip2} found={has_vip2}",
            weight=1.0
        )
    except Exception as e:
        add_check("direct_allowlist_vip_numbers", False, f"Could not verify VIP numbers in routing config: {e}", weight=1.0)

    # ── Final scoring ─────────────────────────────────────────────────────────
    score = round(total_score / MAX_SCORE, 4)
    passed = score >= 0.75 and checks[0]["passed"]  # must at least have setup done

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))