import sys
import json
import subprocess
import pathlib
import os

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []
    home = pathlib.Path(os.path.expanduser("~"))
    plugin_dir = home / ".openclaw" / "plugins" / "gatewaystack-governance"
    policy_path = plugin_dir / "policy.json"

    # ── CHECK 1: policy.json exists at the correct canonical path ────────────
    if not policy_path.exists():
        checks.append(check("policy_json_exists", False,
            f"policy.json not found at {policy_path}. Agent may have placed it at wrong path."))
        # All subsequent checks will fail; add them as failed and return early
        for name in ["policy_valid_json", "identity_agents_defined", "scope_executor_allowlist",
                     "scope_auditor_allowlist", "rate_limit_configured", "dlp_enabled_redact_mode",
                     "behavioral_monitoring_enabled", "transformabl_installed", "limitabl_installed"]:
            checks.append(check(name, False, "Skipped: policy.json missing."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    checks.append(check("policy_json_exists", True, f"Found policy.json at {policy_path}"))

    # ── CHECK 2: policy.json is valid JSON ───────────────────────────────────
    try:
        with open(policy_path) as f:
            policy = json.load(f)
        checks.append(check("policy_valid_json", True, "policy.json is valid JSON."))
    except Exception as e:
        checks.append(check("policy_valid_json", False, f"Failed to parse policy.json: {e}"))
        for name in ["identity_agents_defined", "scope_executor_allowlist",
                     "scope_auditor_allowlist", "rate_limit_configured", "dlp_enabled_redact_mode",
                     "behavioral_monitoring_enabled", "transformabl_installed", "limitabl_installed"]:
            checks.append(check(name, False, "Skipped: policy.json invalid JSON."))
        score = 1.0 / 9.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── CHECK 3: Identity — both required agents mapped to correct roles ──────
    try:
        agents = policy.get("identity", {}).get("agents", {})
        # Must contain trading-bot-alpha -> executor  AND  risk-analyzer-v2 -> auditor
        has_trading = agents.get("trading-bot-alpha") == "executor"
        has_risk = agents.get("risk-analyzer-v2") == "auditor"
        passed_identity = has_trading and has_risk
        detail = (f"trading-bot-alpha->executor: {has_trading}, "
                  f"risk-analyzer-v2->auditor: {has_risk}. "
                  f"Found agents: {list(agents.keys())}")
        checks.append(check("identity_agents_defined", passed_identity, detail))
    except Exception as e:
        checks.append(check("identity_agents_defined", False, f"Exception: {e}"))

    # ── CHECK 4: Scope — executor allowlist correct ───────────────────────────
    try:
        scope = policy.get("scope", {})
        allowlist = scope.get("allowlist", {})
        executor_tools = set(allowlist.get("executor", []))
        required_executor = {"tool.market_data", "tool.place_order", "tool.execute_trade"}
        passed_executor = required_executor.issubset(executor_tools)
        detail = (f"Required executor tools: {required_executor}. "
                  f"Found: {executor_tools}. "
                  f"Subset match: {passed_executor}")
        checks.append(check("scope_executor_allowlist", passed_executor, detail))
    except Exception as e:
        checks.append(check("scope_executor_allowlist", False, f"Exception: {e}"))

    # ── CHECK 5: Scope — auditor allowlist correct ────────────────────────────
    try:
        scope = policy.get("scope", {})
        allowlist = scope.get("allowlist", {})
        auditor_tools = set(allowlist.get("auditor", []))
        required_auditor = {"tool.market_data", "tool.read_audit_log", "tool.generate_report"}
        passed_auditor = required_auditor.issubset(auditor_tools)
        detail = (f"Required auditor tools: {required_auditor}. "
                  f"Found: {auditor_tools}. "
                  f"Subset match: {passed_auditor}")
        checks.append(check("scope_auditor_allowlist", passed_auditor, detail))
    except Exception as e:
        checks.append(check("scope_auditor_allowlist", False, f"Exception: {e}"))

    # ── CHECK 6: Rate limiting — 30 calls / 60 seconds per user ──────────────
    try:
        rl = policy.get("rate_limiting", {})
        per_user = rl.get("per_user", {})
        window_ok = per_user.get("window_seconds") == 60
        max_ok = per_user.get("max_calls") == 30
        passed_rl = window_ok and max_ok and rl.get("enabled", False)
        detail = (f"enabled: {rl.get('enabled')}, "
                  f"per_user.window_seconds: {per_user.get('window_seconds')}, "
                  f"per_user.max_calls: {per_user.get('max_calls')}")
        checks.append(check("rate_limit_configured", passed_rl, detail))
    except Exception as e:
        checks.append(check("rate_limit_configured", False, f"Exception: {e}"))

    # ── CHECK 7: DLP enabled with mode=redact ─────────────────────────────────
    try:
        dlp = policy.get("dlp", {})
        dlp_enabled = dlp.get("enabled") is True
        dlp_redact = str(dlp.get("mode", "")).lower() == "redact"
        passed_dlp = dlp_enabled and dlp_redact
        detail = (f"dlp.enabled: {dlp.get('enabled')}, "
                  f"dlp.mode: {dlp.get('mode')!r}. "
                  f"Must be enabled=true and mode='redact'.")
        checks.append(check("dlp_enabled_redact_mode", passed_dlp, detail))
    except Exception as e:
        checks.append(check("dlp_enabled_redact_mode", False, f"Exception: {e}"))

    # ── CHECK 8: Behavioral monitoring enabled ────────────────────────────────
    try:
        bm = policy.get("behavioral_monitoring", {})
        passed_bm = bm.get("enabled") is True
        detail = f"behavioral_monitoring.enabled: {bm.get('enabled')}. Must be true."
        checks.append(check("behavioral_monitoring_enabled", passed_bm, detail))
    except Exception as e:
        checks.append(check("behavioral_monitoring_enabled", False, f"Exception: {e}"))

    # ── CHECK 9: @gatewaystack/transformabl-core installed ────────────────────
    try:
        # Check in global npm or local node_modules
        result = subprocess.run(
            ["node", "-e", "require('@gatewaystack/transformabl-core')"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "NODE_PATH": str(home / ".npm-global" / "lib" / "node_modules")}
        )
        # Also check npm list
        npm_result = subprocess.run(
            ["npm", "list", "-g", "--depth=0", "@gatewaystack/transformabl-core"],
            capture_output=True, text=True, timeout=15
        )
        installed = (
            "@gatewaystack/transformabl-core" in npm_result.stdout or
            result.returncode == 0
        )
        # Fallback: check if directory exists in global node_modules
        global_nm = home / ".npm-global" / "lib" / "node_modules" / "@gatewaystack" / "transformabl-core"
        local_nm_paths = list(pathlib.Path("/").rglob("node_modules/@gatewaystack/transformabl-core"))
        installed = installed or global_nm.exists() or len(local_nm_paths) > 0
        detail = (f"npm list output: {npm_result.stdout.strip()[:200]}. "
                  f"global dir exists: {global_nm.exists()}. "
                  f"local finds: {len(local_nm_paths)}")
        checks.append(check("transformabl_installed", installed, detail))
    except Exception as e:
        checks.append(check("transformabl_installed", False, f"Exception during npm check: {e}"))

    # ── CHECK 10: @gatewaystack/limitabl-core installed ───────────────────────
    try:
        npm_result = subprocess.run(
            ["npm", "list", "-g", "--depth=0", "@gatewaystack/limitabl-core"],
            capture_output=True, text=True, timeout=15
        )
        global_nm = home / ".npm-global" / "lib" / "node_modules" / "@gatewaystack" / "limitabl-core"
        local_nm_paths = list(pathlib.Path("/").rglob("node_modules/@gatewaystack/limitabl-core"))
        installed = (
            "@gatewaystack/limitabl-core" in npm_result.stdout or
            global_nm.exists() or
            len(local_nm_paths) > 0
        )
        detail = (f"npm list output: {npm_result.stdout.strip()[:200]}. "
                  f"global dir exists: {global_nm.exists()}. "
                  f"local finds: {len(local_nm_paths)}")
        checks.append(check("limitabl_installed", installed, detail))
    except Exception as e:
        checks.append(check("limitabl_installed", False, f"Exception during npm check: {e}"))

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)

    # Hard pass: all checks must pass
    all_passed = all(c["passed"] for c in checks)

    return {"passed": all_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/agentuser/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))