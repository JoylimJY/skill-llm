import sys
import json
import os

def load_json(path):
    with open(path, "r") as f:
        content = f.read()
    # Try standard json first, then pyjson5 for json5 comments/trailing commas
    try:
        return json.loads(content)
    except Exception:
        try:
            import pyjson5
            return pyjson5.loads(content)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON/JSON5: {e}")

def find_agent(cfg, agent_id):
    agents_list = cfg.get("agents", {}).get("list", [])
    for a in agents_list:
        if a.get("id") == agent_id:
            return a
    return None

def run_checks(workspace):
    checks = []
    config_path = os.path.join(workspace, ".openclaw", "openclaw.json")

    # Load config
    try:
        cfg = load_json(config_path)
        checks.append({"name": "config_file_parseable", "passed": True, "detail": "openclaw.json loaded successfully"})
    except Exception as e:
        checks.append({"name": "config_file_parseable", "passed": False, "detail": f"Could not load/parse openclaw.json: {e}"})
        return checks

    global_tools = cfg.get("tools", {})

    # ---- CHECK 1: Global alsoAllow includes both plugin tools ----
    also_allow = global_tools.get("alsoAllow", [])
    lobster_in = "lobster" in also_allow
    llmtask_in = "llm-task" in also_allow
    checks.append({
        "name": "global_alsoAllow_lobster",
        "passed": lobster_in,
        "detail": f"global tools.alsoAllow must contain 'lobster'. Got: {also_allow}"
    })
    checks.append({
        "name": "global_alsoAllow_llm_task",
        "passed": llmtask_in,
        "detail": f"global tools.alsoAllow must contain 'llm-task'. Got: {also_allow}"
    })

    # ---- CHECK 2: alsoAllow used (not 'allow' replacing allowlist) ----
    # The SKILL.md says use alsoAllow, not allow, for plugins. 
    # We verify that plugins are NOT placed in top-level 'allow' as the sole mechanism
    # (acceptable to also have allow, but alsoAllow must be present for plugins)
    checks.append({
        "name": "plugin_tools_use_alsoAllow_not_just_allow",
        "passed": lobster_in and llmtask_in,
        "detail": "Plugin tools must be listed in alsoAllow (additive). alsoAllow must be present."
    })

    # ---- CHECK 3: Global exec security - gateway with allowlist and ask on-miss ----
    exec_cfg = global_tools.get("exec", {})
    exec_host = exec_cfg.get("host", "")
    exec_security = exec_cfg.get("security", "")
    exec_ask = exec_cfg.get("ask", "")

    exec_host_ok = exec_host == "gateway"
    exec_security_ok = exec_security == "allowlist"
    exec_ask_ok = exec_ask == "on-miss"

    checks.append({
        "name": "global_exec_host_gateway",
        "passed": exec_host_ok,
        "detail": f"global tools.exec.host must be 'gateway'. Got: '{exec_host}'"
    })
    checks.append({
        "name": "global_exec_security_allowlist",
        "passed": exec_security_ok,
        "detail": f"global tools.exec.security must be 'allowlist'. Got: '{exec_security}'"
    })
    checks.append({
        "name": "global_exec_ask_on_miss",
        "passed": exec_ask_ok,
        "detail": f"global tools.exec.ask must be 'on-miss'. Got: '{exec_ask}'"
    })

    # ---- CHECK 4: byProvider for google/gemini-2.5-flash with coding profile ----
    by_provider = global_tools.get("byProvider", {})
    gemini_key = "google/gemini-2.5-flash"
    gemini_cfg = by_provider.get(gemini_key, {})
    gemini_profile = gemini_cfg.get("profile", "")
    gemini_profile_ok = gemini_profile == "coding"

    checks.append({
        "name": "byProvider_gemini_exists",
        "passed": gemini_key in by_provider,
        "detail": f"tools.byProvider must have entry for '{gemini_key}'. Found keys: {list(by_provider.keys())}"
    })
    checks.append({
        "name": "byProvider_gemini_coding_profile",
        "passed": gemini_profile_ok,
        "detail": f"tools.byProvider['{gemini_key}'].profile must be 'coding'. Got: '{gemini_profile}'"
    })

    # ---- CHECK 5: orchestrator-001 per-agent config ----
    orch = find_agent(cfg, "orchestrator-001")
    if orch is None:
        checks.append({"name": "orchestrator_agent_exists", "passed": False, "detail": "Agent 'orchestrator-001' not found in agents.list"})
    else:
        checks.append({"name": "orchestrator_agent_exists", "passed": True, "detail": "Agent 'orchestrator-001' found"})
        orch_tools = orch.get("tools", {})
        # Orchestrator should have coding profile (trusted main agent)
        orch_profile = orch_tools.get("profile", "")
        orch_profile_ok = orch_profile == "coding"
        checks.append({
            "name": "orchestrator_coding_profile",
            "passed": orch_profile_ok,
            "detail": f"orchestrator-001 tools.profile must be 'coding'. Got: '{orch_profile}'"
        })
        # Orchestrator should NOT have group:ui or group:web in deny (or at minimum should deny group:ui)
        orch_deny = orch_tools.get("deny", [])
        orch_denies_ui = "group:ui" in orch_deny
        checks.append({
            "name": "orchestrator_denies_group_ui",
            "passed": orch_denies_ui,
            "detail": f"orchestrator-001 must deny 'group:ui'. deny list: {orch_deny}"
        })

    # ---- CHECK 6: notifier-003 per-agent config ----
    notifier = find_agent(cfg, "notifier-003")
    if notifier is None:
        checks.append({"name": "notifier_agent_exists", "passed": False, "detail": "Agent 'notifier-003' not found in agents.list"})
    else:
        checks.append({"name": "notifier_agent_exists", "passed": True, "detail": "Agent 'notifier-003' found"})
        notifier_tools = notifier.get("tools", {})
        notifier_profile = notifier_tools.get("profile", "")
        # Notifier should use messaging profile (only needs messaging tools)
        notifier_profile_ok = notifier_profile == "messaging"
        checks.append({
            "name": "notifier_messaging_profile",
            "passed": notifier_profile_ok,
            "detail": f"notifier-003 tools.profile must be 'messaging'. Got: '{notifier_profile}'"
        })
        # Notifier should deny group:runtime (no shell access)
        notifier_deny = notifier_tools.get("deny", [])
        notifier_denies_runtime = "group:runtime" in notifier_deny
        checks.append({
            "name": "notifier_denies_group_runtime",
            "passed": notifier_denies_runtime,
            "detail": f"notifier-003 must deny 'group:runtime'. deny list: {notifier_deny}"
        })

    # ---- CHECK 7: summarizer-002 per-agent config ----
    summarizer = find_agent(cfg, "summarizer-002")
    if summarizer is None:
        checks.append({"name": "summarizer_agent_exists", "passed": False, "detail": "Agent 'summarizer-002' not found in agents.list"})
    else:
        checks.append({"name": "summarizer_agent_exists", "passed": True, "detail": "Agent 'summarizer-002' found"})
        summ_tools = summarizer.get("tools", {})
        # Summarizer (Gemini-based, low-trust) should use minimal profile or have group:runtime denied
        summ_profile = summ_tools.get("profile", "")
        summ_deny = summ_tools.get("deny", [])
        summ_allow = summ_tools.get("allow", [])
        # Accept: minimal profile, or explicit allow with very limited tools, or coding/messaging with runtime denied
        summ_least_privilege = (
            summ_profile == "minimal"
            or (summ_profile in ("", "coding", "messaging") and "group:runtime" in summ_deny)
            or (summ_profile == "" and len(summ_allow) > 0 and "group:runtime" not in summ_allow)
        )
        checks.append({
            "name": "summarizer_least_privilege",
            "passed": summ_least_privilege,
            "detail": (
                f"summarizer-002 must use least-privilege (minimal profile or deny group:runtime). "
                f"profile='{summ_profile}', deny={summ_deny}, allow={summ_allow}"
            )
        })

    # ---- CHECK 8: No interpreter binaries in safeBins ----
    safe_bins = exec_cfg.get("safeBins", [])
    bad_bins = [b for b in safe_bins if b in ("python3", "node", "bash", "sh", "python", "ruby", "perl")]
    no_interpreter_bins = len(bad_bins) == 0
    checks.append({
        "name": "no_interpreter_in_safeBins",
        "passed": no_interpreter_bins,
        "detail": f"tools.exec.safeBins must not contain interpreter binaries. Found: {bad_bins}"
    })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "unexpected_error", "passed": False, "detail": str(e)}]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()