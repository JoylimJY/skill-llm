import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # --- Find the output file ---
    candidates = list(Path(workspace).rglob("legal_ops_team_config.json"))
    
    if not candidates:
        add_check("file_exists", False, "No file named 'legal_ops_team_config.json' found anywhere in workspace.", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    # Use the first found
    config_path = candidates[0]
    add_check("file_exists", True, f"Found config at: {config_path}", weight=1.0)

    # --- Parse JSON ---
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
        add_check("valid_json", True, "File is valid JSON.", weight=1.0)
    except Exception as e:
        add_check("valid_json", False, f"JSON parse error: {e}", weight=1.0)
        return {"passed": False, "score": total_score / max(max_score, 1), "checks": checks}

    # --- Top-level structure: must have "agents" and "bindings" ---
    has_agents_key = "agents" in cfg
    has_bindings_key = "bindings" in cfg
    add_check("top_level_agents_key", has_agents_key, 
              "'agents' key present at top level." if has_agents_key else "Missing 'agents' key at top level.", weight=1.0)
    add_check("top_level_bindings_key", has_bindings_key,
              "'bindings' key present at top level." if has_bindings_key else "Missing 'bindings' key at top level.", weight=1.0)

    if not has_agents_key or not has_bindings_key:
        return {"passed": False, "score": total_score / max(max_score, 1), "checks": checks}

    # --- agents must be {"list": [...]} structure ---
    agents_val = cfg["agents"]
    agents_is_dict_with_list = isinstance(agents_val, dict) and "list" in agents_val and isinstance(agents_val["list"], list)
    add_check("agents_schema_list_wrapper", agents_is_dict_with_list,
              "'agents' is correctly structured as {'list': [...]}." if agents_is_dict_with_list 
              else f"'agents' must be an object with a 'list' array. Got: {type(agents_val).__name__}", weight=2.0)

    if not agents_is_dict_with_list:
        return {"passed": False, "score": total_score / max(max_score, 1), "checks": checks}

    agent_list = agents_val["list"]

    # --- Must have exactly 5 agents ---
    expected_agent_count = 5
    agent_count_ok = len(agent_list) == expected_agent_count
    add_check("agent_count", agent_count_ok,
              f"Found {len(agent_list)} agents (expected {expected_agent_count}).", weight=1.5)

    # --- Each agent must have id, workspace, agentDir, config ---
    required_agent_fields = {"id", "workspace", "agentDir", "config"}
    all_agents_have_required_fields = True
    missing_fields_detail = []
    for agent in agent_list:
        missing = required_agent_fields - set(agent.keys())
        if missing:
            all_agents_have_required_fields = False
            missing_fields_detail.append(f"Agent '{agent.get('id','?')}' missing: {missing}")

    add_check("agent_required_fields", all_agents_have_required_fields,
              "All agents have 'id', 'workspace', 'agentDir', 'config'." if all_agents_have_required_fields
              else "Some agents missing required fields: " + "; ".join(missing_fields_detail), weight=2.0)

    # --- config sub-object must have role, expertise, responsibilities ---
    required_config_fields = {"role", "expertise", "responsibilities"}
    all_configs_valid = True
    config_issues = []
    for agent in agent_list:
        config = agent.get("config", {})
        if not isinstance(config, dict):
            all_configs_valid = False
            config_issues.append(f"Agent '{agent.get('id','?')}' config is not a dict.")
            continue
        missing_cfg = required_config_fields - set(config.keys())
        if missing_cfg:
            all_configs_valid = False
            config_issues.append(f"Agent '{agent.get('id','?')}' config missing: {missing_cfg}")
        # responsibilities must be a list
        if "responsibilities" in config and not isinstance(config["responsibilities"], list):
            all_configs_valid = False
            config_issues.append(f"Agent '{agent.get('id','?')}' 'responsibilities' must be an array, got {type(config['responsibilities']).__name__}.")

    add_check("config_subfields", all_configs_valid,
              "All agent configs have 'role', 'expertise', 'responsibilities' (responsibilities as array)." if all_configs_valid
              else "Config issues: " + "; ".join(config_issues), weight=2.0)

    # --- Role values must match exactly the named roles in SKILL.md ---
    valid_roles = {
        "Strategic Planner", "Data Analyst", "Risk Manager",
        "Creative Director", "Content Strategist", "UX Designer",
        "Technical Architect", "Full-Stack Developer", "QA Engineer",
        "Project Manager", "Process Optimization Specialist", "Customer Support Manager"
    }
    roles_used = []
    invalid_role_agents = []
    for agent in agent_list:
        config = agent.get("config", {})
        role = config.get("role", "")
        roles_used.append(role)
        if role not in valid_roles:
            invalid_role_agents.append(f"Agent '{agent.get('id','?')}' has invalid role: '{role}'")

    all_roles_valid = len(invalid_role_agents) == 0
    add_check("valid_role_names", all_roles_valid,
              f"All agents use valid canonical role names. Roles found: {roles_used}." if all_roles_valid
              else "Invalid role names: " + "; ".join(invalid_role_agents), weight=2.0)

    # --- Expected roles: Strategic Planner, Data Analyst, Risk Manager, QA Engineer, Technical Architect ---
    expected_roles_set = {"Strategic Planner", "Data Analyst", "Risk Manager", "QA Engineer", "Technical Architect"}
    roles_set = set(roles_used)
    expected_roles_present = expected_roles_set.issubset(roles_set)
    add_check("expected_roles_present", expected_roles_present,
              f"All required roles present: {expected_roles_set}." if expected_roles_present
              else f"Missing roles: {expected_roles_set - roles_set}. Found: {roles_set}.", weight=2.0)

    # --- Expected agent IDs from requirements ---
    expected_ids = {"case_strategy_lead", "discovery_analyst", "compliance_reviewer", "document_qa", "platform_architect"}
    actual_ids = {a.get("id", "") for a in agent_list}
    ids_ok = expected_ids.issubset(actual_ids)
    add_check("agent_ids", ids_ok,
              f"All expected agent IDs found." if ids_ok
              else f"Missing agent IDs: {expected_ids - actual_ids}. Found: {actual_ids}.", weight=1.5)

    # --- Workspace and agentDir paths ---
    expected_workspaces = {
        "case_strategy_lead": "/workspaces/legal-ops/strategy",
        "discovery_analyst": "/workspaces/legal-ops/discovery",
        "compliance_reviewer": "/workspaces/legal-ops/compliance",
        "document_qa": "/workspaces/legal-ops/qa",
        "platform_architect": "/workspaces/legal-ops/platform",
    }
    expected_agentdirs = {
        "case_strategy_lead": "/agents/case-strategy-lead",
        "discovery_analyst": "/agents/discovery-analyst",
        "compliance_reviewer": "/agents/compliance-reviewer",
        "document_qa": "/agents/document-qa",
        "platform_architect": "/agents/platform-architect",
    }
    agent_by_id = {a.get("id", ""): a for a in agent_list}
    
    workspace_path_ok = True
    agentdir_path_ok = True
    path_issues = []
    for aid, expected_ws in expected_workspaces.items():
        agent = agent_by_id.get(aid)
        if agent is None:
            continue
        if agent.get("workspace") != expected_ws:
            workspace_path_ok = False
            path_issues.append(f"Agent '{aid}' workspace: expected '{expected_ws}', got '{agent.get('workspace')}'")
        if agent.get("agentDir") != expected_agentdirs[aid]:
            agentdir_path_ok = False
            path_issues.append(f"Agent '{aid}' agentDir: expected '{expected_agentdirs[aid]}', got '{agent.get('agentDir')}'")

    add_check("workspace_paths", workspace_path_ok and agentdir_path_ok,
              "All workspace and agentDir paths are correct." if (workspace_path_ok and agentdir_path_ok)
              else "Path issues: " + "; ".join(path_issues), weight=2.0)

    # --- Bindings: must be a list ---
    bindings = cfg.get("bindings", [])
    bindings_is_list = isinstance(bindings, list)
    add_check("bindings_is_list", bindings_is_list,
              "'bindings' is a list." if bindings_is_list else f"'bindings' must be a list, got {type(bindings).__name__}.", weight=1.0)

    if not bindings_is_list:
        return {"passed": False, "score": total_score / max(max_score, 1), "checks": checks}

    # --- Must have exactly 5 bindings ---
    expected_binding_count = 5
    binding_count_ok = len(bindings) == expected_binding_count
    add_check("binding_count", binding_count_ok,
              f"Found {len(bindings)} bindings (expected {expected_binding_count}).", weight=1.0)

    # --- KEY PROPRIETARY TRAP 1: case_strategy_lead binding must use peer: {kind: "direct"} ---
    # Find binding for case_strategy_lead
    csl_binding = next((b for b in bindings if b.get("agentId") == "case_strategy_lead"), None)
    if csl_binding is None:
        add_check("case_strategy_lead_binding_exists", False, "No binding found for 'case_strategy_lead'.", weight=2.0)
        add_check("case_strategy_lead_peer_kind_direct", False, "No binding for 'case_strategy_lead' to check peer structure.", weight=3.0)
        add_check("case_strategy_lead_no_text_filter", False, "No binding for 'case_strategy_lead' to verify absence of text filter.", weight=1.0)
    else:
        add_check("case_strategy_lead_binding_exists", True, "Binding for 'case_strategy_lead' found.", weight=2.0)
        match = csl_binding.get("match", {})
        
        # peer must be {"kind": "direct"} — not "direct" string
        peer_val = match.get("peer", None)
        peer_is_correct_object = (
            isinstance(peer_val, dict) and 
            peer_val.get("kind") == "direct"
        )
        add_check("case_strategy_lead_peer_kind_direct", peer_is_correct_object,
                  "case_strategy_lead binding uses correct peer: {'kind': 'direct'} object." if peer_is_correct_object
                  else f"case_strategy_lead binding 'peer' must be object {{'kind': 'direct'}}, got: {peer_val!r}. "
                       f"Common mistake: using string 'direct' instead of object.", weight=3.0)
        
        # Should NOT have text.contains filter (it catches all direct messages)
        has_text_filter = "text" in match
        add_check("case_strategy_lead_no_text_filter", not has_text_filter,
                  "case_strategy_lead binding correctly has no text filter (catches all direct messages)." if not has_text_filter
                  else "case_strategy_lead binding should NOT have a text filter; it handles all direct peer messages.", weight=1.0)
        
        # channel should be "any"
        channel_any = match.get("channel") == "any"
        add_check("case_strategy_lead_channel_any", channel_any,
                  "case_strategy_lead binding has channel: 'any'." if channel_any
                  else f"case_strategy_lead binding channel should be 'any', got: {match.get('channel')!r}.", weight=1.0)

    # --- KEY PROPRIETARY TRAP 2: text.contains must be arrays, not strings ---
    keyword_agents = ["discovery_analyst", "compliance_reviewer", "document_qa", "platform_architect"]
    expected_keywords = {
        "discovery_analyst": ["evidence", "discovery", "data"],
        "compliance_reviewer": ["risk", "compliance", "regulation"],
        "document_qa": ["review", "quality", "QA"],
        "platform_architect": ["architecture", "system", "technical"],
    }

    all_contains_are_arrays = True
    contains_issues = []
    keyword_match_ok = True
    keyword_issues = []

    for aid in keyword_agents:
        binding = next((b for b in bindings if b.get("agentId") == aid), None)
        if binding is None:
            all_contains_are_arrays = False
            contains_issues.append(f"No binding for '{aid}'")
            keyword_match_ok = False
            keyword_issues.append(f"No binding for '{aid}'")
            continue

        match = binding.get("match", {})
        text_obj = match.get("text", {})

        # channel should be any
        # contains must be array
        contains_val = text_obj.get("contains", None)
        if not isinstance(contains_val, list):
            all_contains_are_arrays = False
            contains_issues.append(
                f"Agent '{aid}' binding text.contains is {type(contains_val).__name__!r} (must be array). "
                f"Got: {contains_val!r}"
            )
        
        # Check that expected keywords are present
        if isinstance(contains_val, list):
            expected = expected_keywords[aid]
            missing_kw = [kw for kw in expected if kw not in contains_val]
            if missing_kw:
                keyword_match_ok = False
                keyword_issues.append(f"Agent '{aid}' missing keywords: {missing_kw}")
        else:
            keyword_match_ok = False
            keyword_issues.append(f"Agent '{aid}' contains is not a list, can't check keywords.")

    add_check("text_contains_are_arrays", all_contains_are_arrays,
              "All keyword-based bindings use text.contains as an array." if all_contains_are_arrays
              else "text.contains must be an array of strings: " + "; ".join(contains_issues), weight=3.0)

    add_check("keyword_matches_correct", keyword_match_ok,
              "All agents have their expected routing keywords." if keyword_match_ok
              else "Keyword issues: " + "; ".join(keyword_issues), weight=2.0)

    # --- All keyword-agent bindings have channel: "any" ---
    all_channel_any = True
    channel_issues = []
    for aid in keyword_agents:
        binding = next((b for b in bindings if b.get("agentId") == aid), None)
        if binding is None:
            continue
        ch = binding.get("match", {}).get("channel")
        if ch != "any":
            all_channel_any = False
            channel_issues.append(f"Agent '{aid}' channel is '{ch}' (expected 'any')")

    add_check("keyword_agents_channel_any", all_channel_any,
              "All keyword-based agent bindings use channel: 'any'." if all_channel_any
              else "Channel issues: " + "; ".join(channel_issues), weight=1.0)

    # --- Final determination ---
    # Must pass core structural checks to be considered passing
    critical_checks = [
        "valid_json",
        "top_level_agents_key",
        "top_level_bindings_key",
        "agents_schema_list_wrapper",
        "agent_count",
        "valid_role_names",
        "expected_roles_present",
        "case_strategy_lead_peer_kind_direct",
        "text_contains_are_arrays",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    final_score = total_score / max_score if max_score > 0 else 0.0
    overall_passed = critical_passed and final_score >= 0.80

    return {
        "passed": overall_passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))