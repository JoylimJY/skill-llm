import sys
import os
import json
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
home = os.path.expanduser("~")

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ─── CHECK 1: npm install was attempted ──────────────────────────────────────
def check_npm_install():
    npm_log = "/tmp/npm_install_log.txt"
    global_modules_path = None

    # Try to find where npm puts global packages
    try:
        result = subprocess.run(
            ["/usr/local/bin/npm-real", "config", "get", "prefix"],
            capture_output=True, text=True, timeout=10
        )
        prefix = result.stdout.strip()
        global_modules_path = os.path.join(prefix, "lib", "node_modules",
                                            "@skysphere-labs", "openclaw-bee",
                                            "package.json")
    except Exception:
        pass

    # Check if the shim log records an install attempt
    shim_triggered = False
    if os.path.exists(npm_log):
        try:
            with open(npm_log) as f:
                content = f.read()
            if "openclaw-bee" in content and "Intercepted" in content:
                shim_triggered = True
        except Exception:
            pass

    # Check if the fake package was installed (either via shim or real npm)
    package_installed = False
    if global_modules_path and os.path.exists(global_modules_path):
        package_installed = True

    # Also check alternative locations
    for candidate in [
        "/usr/local/lib/node_modules/@skysphere-labs/openclaw-bee/package.json",
        "/usr/lib/node_modules/@skysphere-labs/openclaw-bee/package.json",
        f"{home}/.npm-global/lib/node_modules/@skysphere-labs/openclaw-bee/package.json",
    ]:
        if os.path.exists(candidate):
            package_installed = True
            break

    passed = shim_triggered or package_installed
    detail = (
        f"Shim triggered: {shim_triggered}, Package directory exists: {package_installed}. "
        f"Log at {npm_log}: {'found' if os.path.exists(npm_log) else 'missing'}"
    )
    add_check("npm_install_bee_attempted", passed, detail, weight=1.5)

# ─── CHECK 2: openclaw.json exists and is valid JSON ─────────────────────────
def load_openclaw_config():
    config_path = os.path.join(home, ".openclaw", "openclaw.json")
    try:
        with open(config_path) as f:
            config = json.load(f)
        add_check("openclaw_json_exists_and_valid", True,
                  f"Found valid JSON at {config_path}", weight=1.0)
        return config
    except FileNotFoundError:
        add_check("openclaw_json_exists_and_valid", False,
                  f"File not found: {config_path}", weight=1.0)
        return None
    except json.JSONDecodeError as e:
        add_check("openclaw_json_exists_and_valid", False,
                  f"Invalid JSON: {e}", weight=1.0)
        return None

# ─── CHECK 3: extensions.entries structure is present ────────────────────────
def check_extensions_structure(config):
    try:
        entries = config["extensions"]["entries"]
        if not isinstance(entries, dict) or len(entries) == 0:
            raise ValueError("entries is empty or not a dict")
        add_check("extensions_entries_structure", True,
                  f"extensions.entries found with {len(entries)} entry(ies)", weight=1.0)
        return entries
    except (KeyError, TypeError, ValueError) as e:
        add_check("extensions_entries_structure", False,
                  f"Missing or malformed extensions.entries: {e}", weight=1.0)
        return None

# ─── CHECK 4: BEE extension is present and enabled ───────────────────────────
def find_bee_entries(entries):
    """Return list of all BEE-like extension entries."""
    bee_entries = {}
    for key, val in entries.items():
        if not isinstance(val, dict):
            continue
        cfg = val.get("config", {})
        # Identify as a BEE entry if it has dbPath and agentId fields
        if "dbPath" in cfg and "agentId" in cfg:
            bee_entries[key] = val
        # Also accept if the key contains 'bee'
        elif "bee" in key.lower():
            bee_entries[key] = val
    return bee_entries

def check_bee_enabled(bee_entries):
    if not bee_entries:
        add_check("bee_extension_present_and_enabled", False,
                  "No BEE extension entry found in extensions.entries", weight=1.5)
        return False
    enabled_count = sum(1 for v in bee_entries.values() if v.get("enabled") is True)
    passed = enabled_count > 0
    add_check("bee_extension_present_and_enabled", passed,
              f"Found {len(bee_entries)} BEE-like entries, {enabled_count} enabled", weight=1.5)
    return passed

# ─── CHECK 5: Multi-agent setup — VECTOR, FORGE, ORACLE each have entries ────
def check_multi_agent_namespaces(bee_entries):
    agent_ids_found = set()
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", "")
        if agent_id:
            agent_ids_found.add(agent_id.upper())

    required_agents = {"VECTOR", "FORGE", "ORACLE"}
    # Check case-insensitively
    found_upper = {a.upper() for a in agent_ids_found}
    missing = required_agents - found_upper
    passed = len(missing) == 0
    add_check("multi_agent_namespaces_vector_forge_oracle", passed,
              f"Agent IDs found: {agent_ids_found}. Missing: {missing}", weight=2.0)
    return agent_ids_found

# ─── CHECK 6: extractionMinConfidence >= 0.72 (per runbook spec) ──────────────
def check_extraction_confidence(bee_entries):
    """The runbook says confidence must be set conservatively: minimum 0.72.
       The SKILL.md default is 0.55, so an agent must read the runbook to know
       the site-specific requirement is 0.72. We check each BEE entry."""
    all_pass = True
    details = []
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", key)
        confidence = cfg.get("extractionMinConfidence")
        if confidence is None:
            all_pass = False
            details.append(f"{agent_id}: extractionMinConfidence missing (default 0.55 is too low)")
        elif float(confidence) < 0.72:
            all_pass = False
            details.append(f"{agent_id}: extractionMinConfidence={confidence} < 0.72 required")
        else:
            details.append(f"{agent_id}: extractionMinConfidence={confidence} ✓")
    if not bee_entries:
        all_pass = False
        details.append("No BEE entries to check")
    add_check("extraction_min_confidence_per_runbook", all_pass,
              "; ".join(details), weight=2.0)

# ─── CHECK 7: Per-agent belief limits per runbook spec ────────────────────────
# VECTOR: maxCoreBeliefs=8, maxActiveBeliefs=3, maxRecalledBeliefs=3
# FORGE:  maxCoreBeliefs=12, maxActiveBeliefs=6, maxRecalledBeliefs=4
# ORACLE: maxCoreBeliefs=15, maxActiveBeliefs=7, maxRecalledBeliefs=6
AGENT_BELIEF_SPECS = {
    "VECTOR": {"maxCoreBeliefs": 8, "maxActiveBeliefs": 3, "maxRecalledBeliefs": 3},
    "FORGE":  {"maxCoreBeliefs": 12, "maxActiveBeliefs": 6, "maxRecalledBeliefs": 4},
    "ORACLE": {"maxCoreBeliefs": 15, "maxActiveBeliefs": 7, "maxRecalledBeliefs": 6},
}

def check_per_agent_belief_limits(bee_entries):
    # Map agentId -> config
    agent_configs = {}
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", "").upper()
        if agent_id:
            agent_configs[agent_id] = cfg

    all_pass = True
    details = []
    for agent_name, expected in AGENT_BELIEF_SPECS.items():
        cfg = agent_configs.get(agent_name)
        if cfg is None:
            all_pass = False
            details.append(f"{agent_name}: no config found")
            continue
        for field, expected_val in expected.items():
            actual = cfg.get(field)
            if actual is None:
                all_pass = False
                details.append(f"{agent_name}.{field}: missing")
            elif int(actual) != expected_val:
                all_pass = False
                details.append(f"{agent_name}.{field}={actual} (expected {expected_val})")
            else:
                details.append(f"{agent_name}.{field}={actual} ✓")

    add_check("per_agent_belief_limits_per_runbook", all_pass,
              "; ".join(details), weight=2.5)

# ─── CHECK 8: maxOutputChars=1500, spawnBudgetWarning=15 for all agents ───────
def check_shared_config_params(bee_entries):
    all_pass = True
    details = []
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", key)

        output_chars = cfg.get("maxOutputChars")
        spawn_warn = cfg.get("spawnBudgetWarning")

        if output_chars is None:
            all_pass = False
            details.append(f"{agent_id}: maxOutputChars missing (should be 1500)")
        elif int(output_chars) != 1500:
            all_pass = False
            details.append(f"{agent_id}: maxOutputChars={output_chars} (expected 1500)")
        else:
            details.append(f"{agent_id}: maxOutputChars=1500 ✓")

        if spawn_warn is None:
            all_pass = False
            details.append(f"{agent_id}: spawnBudgetWarning missing (should be 15)")
        elif int(spawn_warn) != 15:
            all_pass = False
            details.append(f"{agent_id}: spawnBudgetWarning={spawn_warn} (expected 15)")
        else:
            details.append(f"{agent_id}: spawnBudgetWarning=15 ✓")

    if not bee_entries:
        all_pass = False
        details.append("No BEE entries found")
    add_check("shared_config_output_chars_and_spawn_warning", all_pass,
              "; ".join(details), weight=2.0)

# ─── CHECK 9: extractionModel is claude-haiku-4-5 ────────────────────────────
def check_extraction_model(bee_entries):
    all_pass = True
    details = []
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", key)
        model = cfg.get("extractionModel", "")
        expected = "anthropic/claude-haiku-4-5"
        if model == expected:
            details.append(f"{agent_id}: extractionModel='{model}' ✓")
        elif "haiku" in model.lower():
            # Partial credit — right family but wrong exact model name
            all_pass = False
            details.append(f"{agent_id}: extractionModel='{model}' (close, expected '{expected}')")
        else:
            all_pass = False
            details.append(f"{agent_id}: extractionModel='{model}' (expected '{expected}')")
    if not bee_entries:
        all_pass = False
        details.append("No BEE entries")
    add_check("extraction_model_is_haiku", all_pass,
              "; ".join(details), weight=1.5)

# ─── CHECK 10: dbPath uses state directory convention ─────────────────────────
def check_db_paths(bee_entries):
    all_pass = True
    details = []
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", key)
        db_path = cfg.get("dbPath", "")
        # Must reference the standard state directory
        if "state" in db_path and "vector.db" in db_path and ".openclaw" in db_path:
            details.append(f"{agent_id}: dbPath='{db_path}' ✓")
        elif "vector.db" in db_path:
            # Has the right filename but not the right directory
            all_pass = False
            details.append(f"{agent_id}: dbPath='{db_path}' (missing ~/.openclaw/workspace/state/ path)")
        else:
            all_pass = False
            details.append(f"{agent_id}: dbPath='{db_path}' (expected path under ~/.openclaw/workspace/state/)")
    if not bee_entries:
        all_pass = False
        details.append("No BEE entries")
    add_check("db_path_uses_state_convention", all_pass,
              "; ".join(details), weight=1.5)

# ─── CHECK 11: extractionEnabled is true for all agents ──────────────────────
def check_extraction_enabled(bee_entries):
    all_pass = True
    details = []
    for key, val in bee_entries.items():
        cfg = val.get("config", {})
        agent_id = cfg.get("agentId", key)
        enabled = cfg.get("extractionEnabled")
        if enabled is True:
            details.append(f"{agent_id}: extractionEnabled=true ✓")
        else:
            all_pass = False
            details.append(f"{agent_id}: extractionEnabled={enabled} (expected true)")
    if not bee_entries:
        all_pass = False
        details.append("No BEE entries")
    add_check("extraction_enabled_true_all_agents", all_pass,
              "; ".join(details), weight=1.0)

# ─── CHECK 12: gateway restart was invoked ───────────────────────────────────
def check_gateway_restart():
    restart_log = "/tmp/openclaw_restart_log.txt"
    passed = os.path.exists(restart_log)
    detail = (f"Restart log found at {restart_log}" if passed
              else f"No restart log at {restart_log} — 'openclaw gateway restart' may not have been run")
    add_check("gateway_restart_invoked", passed, detail, weight=1.0)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
check_npm_install()
config = load_openclaw_config()

if config is not None:
    entries = check_extensions_structure(config)
    if entries is not None:
        bee_entries = find_bee_entries(entries)
        check_bee_enabled(bee_entries)
        check_multi_agent_namespaces(bee_entries)
        check_extraction_confidence(bee_entries)
        check_per_agent_belief_limits(bee_entries)
        check_shared_config_params(bee_entries)
        check_extraction_model(bee_entries)
        check_db_paths(bee_entries)
        check_extraction_enabled(bee_entries)
    else:
        for name in ["bee_extension_present_and_enabled",
                     "multi_agent_namespaces_vector_forge_oracle",
                     "extraction_min_confidence_per_runbook",
                     "per_agent_belief_limits_per_runbook",
                     "shared_config_output_chars_and_spawn_warning",
                     "extraction_model_is_haiku",
                     "db_path_uses_state_convention",
                     "extraction_enabled_true_all_agents"]:
            add_check(name, False, "Skipped — extensions.entries structure missing", weight=1.0)
else:
    for name in ["extensions_entries_structure",
                 "bee_extension_present_and_enabled",
                 "multi_agent_namespaces_vector_forge_oracle",
                 "extraction_min_confidence_per_runbook",
                 "per_agent_belief_limits_per_runbook",
                 "shared_config_output_chars_and_spawn_warning",
                 "extraction_model_is_haiku",
                 "db_path_uses_state_convention",
                 "extraction_enabled_true_all_agents"]:
        add_check(name, False, "Skipped — openclaw.json missing or invalid", weight=1.0)

check_gateway_restart()

score = round(total_score / max_score, 4) if max_score > 0 else 0.0
passed_overall = score >= 0.75

print(json.dumps({
    "passed": passed_overall,
    "score": score,
    "checks": checks
}, indent=2))