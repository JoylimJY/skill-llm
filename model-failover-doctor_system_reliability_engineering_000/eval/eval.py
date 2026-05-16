#!/usr/bin/env python3
"""
Evaluates whether the agent correctly diagnosed and fixed all OpenClaw failover issues.
"""
import json
import re
import sys
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text())

def run_eval(workspace_dir):
    HOME = Path("/root")
    OPENCLAW = HOME / ".openclaw"
    WS = OPENCLAW / "workspace"

    POOLS_JSON    = WS / "config" / "pools.json"
    SESSION_STATE = WS / "sessions" / "session_model_state.json"
    INJECTOR_TS   = OPENCLAW / "runtime" / "injectors" / "message-injector.ts"
    BACKUPS_DIR   = WS / ".lib" / ".mfd_backups"
    RESTART_MARKER = OPENCLAW / "runtime" / "gateway" / ".last_restart"
    PROVIDERS_DIR  = WS / "providers"

    checks = []

    # Load known providers from providers dir
    known_providers = set()
    try:
        for f in PROVIDERS_DIR.glob("*.json"):
            data = json.loads(f.read_text())
            known_providers.add(data.get("id", f.stem))
    except Exception as e:
        known_providers = {"kimi-coding", "zai", "minimax"}

    # ── CHECK 1: P-1 — pools.json no longer references ghost providers ────────
    try:
        pools_data = load_json(POOLS_JSON)
        ghost_refs = []
        for pool in pools_data.get("pools", []):
            for prov in pool.get("providers", []):
                if prov not in known_providers:
                    ghost_refs.append(f"{pool['id']}:{prov}")
        if not ghost_refs:
            checks.append({
                "name": "P-1: pools.json ghost providers removed",
                "passed": True,
                "detail": f"All pool providers are valid. Known: {sorted(known_providers)}"
            })
        else:
            checks.append({
                "name": "P-1: pools.json ghost providers removed",
                "passed": False,
                "detail": f"Still contains unknown providers: {ghost_refs}"
            })
    except Exception as e:
        checks.append({
            "name": "P-1: pools.json ghost providers removed",
            "passed": False,
            "detail": f"Error reading pools.json: {e}"
        })

    # ── CHECK 2: pools.json still has valid pools (not wiped) ────────────────
    try:
        pools_data = load_json(POOLS_JSON)
        all_pools = pools_data.get("pools", [])
        non_empty = [p for p in all_pools if len(p.get("providers", [])) > 0]
        if len(non_empty) >= 2:
            checks.append({
                "name": "P-1: pools.json valid pools preserved",
                "passed": True,
                "detail": f"{len(non_empty)} pools still have valid providers"
            })
        else:
            checks.append({
                "name": "P-1: pools.json valid pools preserved",
                "passed": False,
                "detail": f"Too few non-empty pools remaining: {len(non_empty)}. Files may have been over-aggressively cleaned."
            })
    except Exception as e:
        checks.append({
            "name": "P-1: pools.json valid pools preserved",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 3: S-1 — sess-alpha now has a fallbackChain ────────────────────
    try:
        sess_data = load_json(SESSION_STATE)
        alpha = sess_data.get("sessions", {}).get("sess-alpha", {})
        chain = alpha.get("fallbackChain")
        if chain and len(chain) > 0:
            checks.append({
                "name": "S-1: sess-alpha has fallbackChain",
                "passed": True,
                "detail": f"fallbackChain = {chain}"
            })
        else:
            checks.append({
                "name": "S-1: sess-alpha has fallbackChain",
                "passed": False,
                "detail": f"sess-alpha still missing fallbackChain. Got: {chain}"
            })
    except Exception as e:
        checks.append({
            "name": "S-1: sess-alpha has fallbackChain",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 4: S-1 fallbackChain uses valid providers ──────────────────────
    try:
        sess_data = load_json(SESSION_STATE)
        alpha = sess_data.get("sessions", {}).get("sess-alpha", {})
        chain = alpha.get("fallbackChain", [])
        invalid_entries = []
        for entry in chain:
            parts = entry.split("/", 1)
            if len(parts) == 2 and parts[0] not in known_providers:
                invalid_entries.append(entry)
        if not invalid_entries:
            checks.append({
                "name": "S-1: sess-alpha fallbackChain uses valid providers",
                "passed": True,
                "detail": f"All entries reference known providers"
            })
        else:
            checks.append({
                "name": "S-1: sess-alpha fallbackChain uses valid providers",
                "passed": False,
                "detail": f"Invalid entries in sess-alpha fallbackChain: {invalid_entries}"
            })
    except Exception as e:
        checks.append({
            "name": "S-1: sess-alpha fallbackChain uses valid providers",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 5: S-2 — sess-beta fallbackChain has no invalid prefixes ───────
    try:
        sess_data = load_json(SESSION_STATE)
        beta = sess_data.get("sessions", {}).get("sess-beta", {})
        chain = beta.get("fallbackChain", [])
        bad_entries = []
        for entry in chain:
            parts = entry.split("/", 1)
            if len(parts) == 2 and parts[0] not in known_providers:
                bad_entries.append(entry)
        if not bad_entries:
            checks.append({
                "name": "S-2: sess-beta fallbackChain has valid provider prefixes",
                "passed": True,
                "detail": f"All entries in sess-beta are valid: {chain}"
            })
        else:
            checks.append({
                "name": "S-2: sess-beta fallbackChain has valid provider prefixes",
                "passed": False,
                "detail": f"sess-beta still has bad entries: {bad_entries}"
            })
    except Exception as e:
        checks.append({
            "name": "S-2: sess-beta fallbackChain has valid provider prefixes",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 6: sess-gamma untouched (was already valid) ────────────────────
    try:
        sess_data = load_json(SESSION_STATE)
        gamma = sess_data.get("sessions", {}).get("sess-gamma", {})
        chain = gamma.get("fallbackChain", [])
        # gamma had a valid chain: ["kimi-coding/k2p5", "zai/k2p5"]
        gamma_ok = len(chain) >= 1 and all(
            e.split("/")[0] in known_providers for e in chain if "/" in e
        )
        if gamma_ok:
            checks.append({
                "name": "S-*: sess-gamma healthy session preserved",
                "passed": True,
                "detail": f"sess-gamma fallbackChain intact: {chain}"
            })
        else:
            checks.append({
                "name": "S-*: sess-gamma healthy session preserved",
                "passed": False,
                "detail": f"sess-gamma was incorrectly modified: {chain}"
            })
    except Exception as e:
        checks.append({
            "name": "S-*: sess-gamma healthy session preserved",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 7: MI-1 — TypeScript injector has lockModel guard ──────────────
    try:
        src = INJECTOR_TS.read_text()
        # Must contain the lockModel ternary pattern
        has_lock_guard = bool(re.search(r'\.\.\.\s*\(\s*lockModel\s*\?', src))
        if has_lock_guard:
            checks.append({
                "name": "MI-1: message-injector.ts has lockModel guard",
                "passed": True,
                "detail": "Found `...(lockModel ? { ... } : {})` pattern in before_agent_start"
            })
        else:
            checks.append({
                "name": "MI-1: message-injector.ts has lockModel guard",
                "passed": False,
                "detail": "Did not find lockModel ternary spread. The unconditional modelOverride return may still be present."
            })
    except Exception as e:
        checks.append({
            "name": "MI-1: message-injector.ts has lockModel guard",
            "passed": False,
            "detail": f"Error reading injector: {e}"
        })

    # ── CHECK 8: MI-1 — modelOverride NOT unconditionally in return ───────────
    try:
        src = INJECTOR_TS.read_text()
        # The broken pattern: a return block with modelOverride as a bare key (not inside ternary)
        # We look for "modelOverride," NOT preceded by a ternary
        broken_still = re.search(
            r'return\s*\{[^}]*(?<!\?)(?<!\?\s)\s*modelOverride\s*,[^}]*\}',
            src, re.DOTALL
        )
        # More targeted: check there's no line with just "      modelOverride," in return
        bare_override = re.search(r'^\s{4,6}modelOverride\s*,\s*$', src, re.MULTILINE)
        if not bare_override:
            checks.append({
                "name": "MI-1: unconditional modelOverride return removed",
                "passed": True,
                "detail": "No bare 'modelOverride,' found in return block"
            })
        else:
            checks.append({
                "name": "MI-1: unconditional modelOverride return removed",
                "passed": False,
                "detail": "Bare 'modelOverride,' still present in return — FIXME pattern not fully resolved"
            })
    except Exception as e:
        checks.append({
            "name": "MI-1: unconditional modelOverride return removed",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 9: Backup files were created ────────────────────────────────────
    try:
        backups = list(BACKUPS_DIR.glob("*.bak"))
        if len(backups) >= 2:
            checks.append({
                "name": "Backup files created before modification",
                "passed": True,
                "detail": f"Found {len(backups)} backup files in {BACKUPS_DIR}"
            })
        else:
            checks.append({
                "name": "Backup files created before modification",
                "passed": False,
                "detail": f"Expected ≥2 backup files, found {len(backups)} in {BACKUPS_DIR}. "
                          f"Backups: {[b.name for b in backups]}"
            })
    except Exception as e:
        checks.append({
            "name": "Backup files created before modification",
            "passed": False,
            "detail": f"Error checking backups: {e}"
        })

    # ── CHECK 10: Gateway restart marker created ──────────────────────────────
    try:
        if RESTART_MARKER.exists():
            ts_content = RESTART_MARKER.read_text().strip()
            checks.append({
                "name": "Gateway restart triggered",
                "passed": True,
                "detail": f"Restart marker found with timestamp: {ts_content}"
            })
        else:
            checks.append({
                "name": "Gateway restart triggered",
                "passed": False,
                "detail": f"No restart marker found at {RESTART_MARKER}. "
                          "Did you run the tool with --restart flag?"
            })
    except Exception as e:
        checks.append({
            "name": "Gateway restart triggered",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    overall = passed_count == total

    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/root"
    run_eval(workspace_dir)