import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    """Load a JSON file, return (data, error)"""
    try:
        with open(path, "r") as f:
            content = f.read()
        # Try standard JSON first
        try:
            return json.loads(content), None
        except json.JSONDecodeError:
            # Try stripping JSONC comments
            import re
            stripped = re.sub(r'//.*', '', content)
            stripped = re.sub(r'/\*.*?\*/', '', stripped, flags=re.DOTALL)
            return json.loads(stripped), None
    except Exception as e:
        return None, str(e)

def deep_get(d, *keys, default=None):
    """Navigate nested dict safely"""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
        if d is None:
            return default
    return d

def run_checks(workspace):
    checks = []
    score_total = 0.0
    score_max = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal score_total, score_max
        score_max += weight
        if passed:
            score_total += weight

    # Find openclaw.json
    candidates = list(Path(workspace).rglob("openclaw.json"))
    # Prefer root-level
    root_candidate = Path(workspace) / "openclaw.json"
    
    if root_candidate.exists():
        config_path = root_candidate
    elif candidates:
        config_path = candidates[0]
    else:
        add_check("config_file_exists", False, "openclaw.json not found in workspace", weight=3.0)
        return checks, 0.0, score_max

    data, err = load_json_file(config_path)
    if data is None:
        add_check("config_file_parseable", False, f"Could not parse openclaw.json: {err}", weight=3.0)
        return checks, 0.0, score_max

    add_check("config_file_parseable", True, f"openclaw.json found and parsed at {config_path}", weight=1.0)

    # Navigate to plugin config - support both nesting styles
    # Style 1: plugins.policy-engine.config {...}  (DESIGN.md §4.5 example)
    # Style 2: plugins.policy-engine {...} (Quick Start example)
    
    pe_root = deep_get(data, "plugins", "policy-engine")
    if pe_root is None:
        pe_root = deep_get(data, "plugins", "entries", "policy-engine")
    
    if pe_root is None:
        add_check("plugin_section_exists", False, "No plugins.policy-engine section found", weight=2.0)
        return checks, 0.0, score_max
    
    add_check("plugin_section_exists", True, "plugins.policy-engine section found", weight=1.0)

    # The actual config might be nested under 'config' key or at top level of pe_root
    cfg = pe_root.get("config", pe_root)

    # CHECK 1: Plugin enabled
    enabled = cfg.get("enabled", pe_root.get("enabled", True))
    add_check(
        "plugin_enabled",
        enabled is True,
        f"enabled = {enabled!r} (expected true)",
        weight=1.0
    )

    # CHECK 2: dryRun = true
    dry_run = cfg.get("dryRun", False)
    add_check(
        "dry_run_enabled",
        dry_run is True,
        f"dryRun = {dry_run!r} (expected true)",
        weight=1.5
    )

    # CHECK 3: dryRunAllowT0 = true
    dry_run_allow_t0 = cfg.get("dryRunAllowT0", True)  # default is true per spec
    add_check(
        "dry_run_allow_t0",
        dry_run_allow_t0 is True,
        f"dryRunAllowT0 = {dry_run_allow_t0!r} (expected true)",
        weight=1.0
    )

    # CHECK 4: maxBlockedRetries = 5 (non-default, default is 3)
    max_retries = cfg.get("maxBlockedRetries", 3)
    add_check(
        "max_blocked_retries_5",
        max_retries == 5,
        f"maxBlockedRetries = {max_retries!r} (expected 5)",
        weight=1.5
    )

    # CHECK 5: Allowlist profiles - must have all three profiles
    allowlists = cfg.get("allowlists", {})
    
    # Find analyst profile (name may vary, but must map to data-analyst-bot and contain correct tools)
    routing = cfg.get("routing", {})
    
    # Get profile name for data-analyst-bot
    analyst_routing = routing.get("data-analyst-bot", {})
    analyst_profile = analyst_routing.get("toolProfile") if isinstance(analyst_routing, dict) else None
    
    ops_routing = routing.get("ops-bot", {})
    ops_profile = ops_routing.get("toolProfile") if isinstance(ops_routing, dict) else None
    
    audit_routing = routing.get("audit-bot", {})
    audit_profile = audit_routing.get("toolProfile") if isinstance(audit_routing, dict) else None

    # CHECK 5a: Routing uses dict with toolProfile (not direct string - this is the proprietary trap)
    routing_correct_format = (
        isinstance(analyst_routing, dict) and "toolProfile" in analyst_routing
        or isinstance(ops_routing, dict) and "toolProfile" in ops_routing
        or isinstance(audit_routing, dict) and "toolProfile" in audit_routing
    )
    add_check(
        "routing_uses_toolProfile_object",
        routing_correct_format,
        f"routing entries must be objects with 'toolProfile' key. "
        f"data-analyst-bot routing: {analyst_routing!r}, ops-bot: {ops_routing!r}, audit-bot: {audit_routing!r}",
        weight=2.0
    )

    # CHECK 5b: All three agents have routing entries
    all_agents_routed = (
        "data-analyst-bot" in routing and
        "ops-bot" in routing and
        "audit-bot" in routing
    )
    add_check(
        "all_three_agents_routed",
        all_agents_routed,
        f"routing keys found: {list(routing.keys())}",
        weight=1.5
    )

    # CHECK 5c: Analyst profile tools - must include read, web_fetch, web_search, memory_search, message
    ANALYST_REQUIRED = {"read", "web_fetch", "web_search", "memory_search", "message"}
    analyst_tools = set(allowlists.get(analyst_profile, [])) if analyst_profile else set()
    analyst_ok = analyst_tools >= ANALYST_REQUIRED if analyst_tools else False
    add_check(
        "analyst_profile_tools",
        analyst_ok,
        f"analyst profile '{analyst_profile}' tools: {sorted(analyst_tools)}. Required: {sorted(ANALYST_REQUIRED)}",
        weight=1.5
    )

    # CHECK 5d: Ops profile tools - must include read, write, edit, exec, process, message
    OPS_REQUIRED = {"read", "write", "edit", "exec", "process", "message"}
    ops_tools = set(allowlists.get(ops_profile, [])) if ops_profile else set()
    ops_ok = ops_tools >= OPS_REQUIRED if ops_tools else False
    add_check(
        "ops_profile_tools",
        ops_ok,
        f"ops profile '{ops_profile}' tools: {sorted(ops_tools)}. Required: {sorted(OPS_REQUIRED)}",
        weight=1.5
    )

    # CHECK 5e: Audit profile tools - must include read, memory_search, memory_get, session_status, message
    AUDIT_REQUIRED = {"read", "memory_search", "memory_get", "session_status", "message"}
    audit_tools = set(allowlists.get(audit_profile, [])) if audit_profile else set()
    audit_ok = audit_tools >= AUDIT_REQUIRED if audit_tools else False
    add_check(
        "audit_profile_tools",
        audit_ok,
        f"audit profile '{audit_profile}' tools: {sorted(audit_tools)}. Required: {sorted(AUDIT_REQUIRED)}",
        weight=1.5
    )

    # CHECK 6: Deny patterns - must be scoped to 'exec' tool only
    deny_patterns = cfg.get("denyPatterns", {})
    
    # Must have exec deny patterns
    exec_patterns = deny_patterns.get("exec", [])
    has_exec_patterns = len(exec_patterns) > 0
    add_check(
        "deny_patterns_for_exec_exist",
        has_exec_patterns,
        f"denyPatterns.exec = {exec_patterns!r} (must have at least one pattern)",
        weight=1.5
    )

    # Check that npm publish is blocked (some form)
    import re
    npm_blocked = any("npm" in p and "publish" in p for p in exec_patterns)
    add_check(
        "deny_pattern_npm_publish",
        npm_blocked,
        f"exec patterns must block 'npm publish'. Found patterns: {exec_patterns!r}",
        weight=1.0
    )

    # Check that docker push is blocked
    docker_blocked = any("docker" in p and "push" in p for p in exec_patterns)
    add_check(
        "deny_pattern_docker_push",
        docker_blocked,
        f"exec patterns must block 'docker push'. Found patterns: {exec_patterns!r}",
        weight=1.0
    )

    # Check pipe-to-shell pattern (curl|bash or wget|sh)
    pipe_blocked = any(
        ("curl" in p or "wget" in p) and ("bash" in p or "sh" in p)
        for p in exec_patterns
    )
    add_check(
        "deny_pattern_pipe_to_shell",
        pipe_blocked,
        f"exec patterns must block curl/wget pipe-to-shell. Found patterns: {exec_patterns!r}",
        weight=1.0
    )

    # CRITICAL PROPRIETARY TRAP: Deny patterns must NOT be on 'write' for content filtering
    # (write deny patterns only check file_path/path, not content - so adding content patterns
    # to write would be an incorrect approach showing misunderstanding of scoping)
    write_patterns = deny_patterns.get("write", [])
    # Check if agent incorrectly added content-based patterns to write
    content_like_patterns_in_write = [
        p for p in write_patterns 
        if any(keyword in p.lower() for keyword in ["npm", "curl", "bash", "docker", "fork", "bomb"])
    ]
    no_content_patterns_on_write = len(content_like_patterns_in_write) == 0
    add_check(
        "no_content_deny_patterns_on_write_tool",
        no_content_patterns_on_write,
        f"Write tool deny patterns should only restrict paths, not content. "
        f"Incorrectly added content patterns to write: {content_like_patterns_in_write!r}",
        weight=2.0
    )

    # CHECK 7: Path allowlists for write and edit
    path_allowlists = cfg.get("pathAllowlists", {})
    
    write_paths = path_allowlists.get("write", [])
    REQUIRED_PATH = "/opt/fintech/workspace"
    write_path_ok = any(REQUIRED_PATH in p or p.startswith(REQUIRED_PATH) for p in write_paths)
    add_check(
        "path_allowlist_write",
        write_path_ok,
        f"pathAllowlists.write must include '{REQUIRED_PATH}'. Found: {write_paths!r}",
        weight=1.5
    )

    edit_paths = path_allowlists.get("edit", [])
    edit_path_ok = any(REQUIRED_PATH in p or p.startswith(REQUIRED_PATH) for p in edit_paths)
    add_check(
        "path_allowlist_edit",
        edit_path_ok,
        f"pathAllowlists.edit must include '{REQUIRED_PATH}'. Found: {edit_paths!r}",
        weight=1.5
    )

    # CHECK 8: riskTiers override for deploy_hook as T2
    risk_tiers = cfg.get("riskTiers", {})
    
    # riskTiers can be either a flat map {tool: "T0"|"T1"|"T2"} or structured {T0:[], T1:[], T2:[]}
    deploy_hook_tier = None
    if isinstance(risk_tiers, dict):
        # Flat map format: {"deploy_hook": "T2"}
        if "deploy_hook" in risk_tiers:
            deploy_hook_tier = risk_tiers["deploy_hook"]
        # Structured format: {T0: [...], T1: [...], T2: [..., "deploy_hook", ...]}
        elif "T2" in risk_tiers and isinstance(risk_tiers["T2"], list):
            if "deploy_hook" in risk_tiers["T2"]:
                deploy_hook_tier = "T2"
        elif "T0" in risk_tiers or "T1" in risk_tiers:
            # Check all tiers
            for tier_name in ["T0", "T1", "T2"]:
                tier_list = risk_tiers.get(tier_name, [])
                if isinstance(tier_list, list) and "deploy_hook" in tier_list:
                    deploy_hook_tier = tier_name
                    break

    deploy_hook_t2 = deploy_hook_tier == "T2"
    add_check(
        "deploy_hook_risk_tier_T2",
        deploy_hook_t2,
        f"riskTiers must set 'deploy_hook' to T2. Found tier: {deploy_hook_tier!r}. Full riskTiers: {risk_tiers!r}",
        weight=2.0
    )

    # CHECK 9: Essential tools understanding - gateway should NOT be in any allowlist
    # (because gateway is T2 AND essential, it bypasses allowlist entirely per the evaluation chain)
    # If an agent adds gateway to an allowlist it's not wrong per se, but the key test is:
    # gateway must not be MISSING from ops profile if agent thinks they need to add it
    # Actually the real test: the agent should NOT add gateway to allowlists thinking that's
    # required for it to work - because essential tools bypass allowlists entirely (Step 4)
    # We test this indirectly: the ops profile should NOT need gateway listed to function
    # Better check: ensure agent knows that essential tools (message, gateway, session_status etc.)
    # are always allowed - verify they haven't added redundant/incorrect restrictions
    
    # Check: dryRunEssentialTools if overridden should include at minimum the core 6 tools
    dry_run_essential = cfg.get("dryRunEssentialTools", None)
    if dry_run_essential is not None:
        REQUIRED_ESSENTIAL = {"message", "gateway", "session_status"}
        essential_set = set(dry_run_essential)
        essential_ok = REQUIRED_ESSENTIAL.issubset(essential_set)
        add_check(
            "dry_run_essential_tools_complete",
            essential_ok,
            f"If dryRunEssentialTools is overridden, it must include {sorted(REQUIRED_ESSENTIAL)}. "
            f"Found: {sorted(essential_set)}",
            weight=1.0
        )
    else:
        # Using defaults - that's fine, skip this check with a pass
        add_check(
            "dry_run_essential_tools_complete",
            True,
            "dryRunEssentialTools not overridden, defaults used (includes message, gateway, session_status)",
            weight=1.0
        )

    # Compute final score
    final_score = score_total / score_max if score_max > 0 else 0.0
    return checks, final_score, score_max

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score, score_max = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }))
        return

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    
    # Pass if score >= 0.75 (must get most checks right including critical ones)
    overall_passed = score >= 0.75 and passed_count >= int(total_count * 0.75)

    print(json.dumps({
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()