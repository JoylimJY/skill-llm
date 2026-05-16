import sys
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    
    # The agent should have rebuilt/scaffolded infra-deployer correctly.
    # We look in the most likely location first, then search.
    project_dir = workspace / "infra-deployer"
    
    # ── CHECK 1: Golden layout - main.go exists with correct Execute pattern ──
    main_go = project_dir / "main.go"
    try:
        content = main_go.read_text()
        # Must use os.Exit with Execute pattern per golden layout
        has_os_exit = "os.Exit" in content
        has_execute = "Execute" in content
        # Must NOT use fmt.Println as the primary entrypoint
        has_old_pattern = content.strip().count("fmt.Println") > 1 and "Execute" not in content
        passed = has_os_exit and has_execute and not has_old_pattern
        checks.append(check(
            "main.go uses os.Exit(cmd.Execute(os.Args[1:])) pattern",
            passed,
            f"os.Exit={has_os_exit}, Execute={has_execute}, content_snippet={content[:300]}"
        ))
    except Exception as e:
        checks.append(check("main.go uses os.Exit(cmd.Execute(os.Args[1:])) pattern", False, str(e)))

    # ── CHECK 2: cmd/root.go uses cobrax.Execute with RootSpec ──
    root_go = project_dir / "cmd" / "root.go"
    try:
        content = root_go.read_text()
        has_cobrax = "cobrax" in content
        has_rootspec = "RootSpec" in content
        has_appmeta = "AppMeta" in content
        has_execute = "cobrax.Execute" in content or ("Execute" in content and "RootSpec" in content)
        # Must NOT be the old cobra pattern
        has_old_cobra_pattern = ("var rootCmd = &cobra.Command" in content and "cobrax" not in content)
        passed = has_cobrax and has_rootspec and has_appmeta and not has_old_cobra_pattern
        checks.append(check(
            "cmd/root.go uses cobrax.Execute with RootSpec and AppMeta",
            passed,
            f"cobrax={has_cobrax}, RootSpec={has_rootspec}, AppMeta={has_appmeta}, old_pattern={has_old_cobra_pattern}"
        ))
    except Exception as e:
        checks.append(check("cmd/root.go uses cobrax.Execute with RootSpec and AppMeta", False, str(e)))

    # ── CHECK 3: RootSpec contains correct tool name "infra-deployer" ──
    try:
        content = root_go.read_text()
        has_tool_name = "infra-deployer" in content
        checks.append(check(
            "cmd/root.go RootSpec has correct Use name 'infra-deployer'",
            has_tool_name,
            f"content snippet: {content[:500]}"
        ))
    except Exception as e:
        checks.append(check("cmd/root.go RootSpec has correct Use name 'infra-deployer'", False, str(e)))

    # ── CHECK 4: deploy command exists in cmd/ ──
    deploy_go = project_dir / "cmd" / "deploy.go"
    try:
        content = deploy_go.read_text()
        has_deploy = "deploy" in content.lower() or "Deploy" in content
        has_command_func = "Command" in content and ("func" in content)
        checks.append(check(
            "cmd/deploy.go exists and contains deploy command function",
            has_deploy and has_command_func,
            f"has_deploy={has_deploy}, has_command_func={has_command_func}, snippet={content[:300]}"
        ))
    except Exception as e:
        checks.append(check("cmd/deploy.go exists and contains deploy command function", False, str(e)))

    # ── CHECK 5: deploy command wired in RootSpec Commands list ──
    try:
        content = root_go.read_text()
        # Should reference DeployCommand or similar in Commands slice
        has_deploy_ref = (
            "DeployCommand" in content or
            "deploy" in content.lower() and "Command" in content and "Commands" in content
        )
        checks.append(check(
            "cmd/root.go Commands slice includes deploy command reference",
            has_deploy_ref,
            f"snippet: {content}"
        ))
    except Exception as e:
        checks.append(check("cmd/root.go Commands slice includes deploy command reference", False, str(e)))

    # ── CHECK 6: configx.Load used in internal/config/load.go ──
    config_load = project_dir / "internal" / "config" / "load.go"
    try:
        content = config_load.read_text()
        has_configx = "configx" in content
        has_load = "configx.Load" in content
        checks.append(check(
            "internal/config/load.go uses configx.Load",
            has_configx and has_load,
            f"has_configx={has_configx}, has_load={has_load}, snippet={content[:400]}"
        ))
    except Exception as e:
        checks.append(check("internal/config/load.go uses configx.Load", False, str(e)))

    # ── CHECK 7: configx.NormalizeEnv called with correct "DEPLOYER_" prefix ──
    try:
        content = config_load.read_text()
        # The module is github.com/platform-team/infra-deployer -> tool name is infra-deployer
        # Per SKILL.md: NormalizeEnv("MYTOOL_", os.Environ())
        # The tool is "infra-deployer" -> convention is uppercase + underscore -> "DEPLOYER_" or "INFRA_DEPLOYER_"
        # Accept DEPLOYER_ or INFRA_DEPLOYER_ or INFRADEPLOYER_
        normalize_match = re.search(r'NormalizeEnv\s*\(\s*["\']([^"\']+)["\']', content)
        if normalize_match:
            prefix = normalize_match.group(1)
            # Must be uppercase, must end with underscore, must relate to tool name
            is_uppercase = prefix == prefix.upper()
            ends_with_underscore = prefix.endswith("_")
            is_relevant = any(kw in prefix for kw in ["DEPLOYER", "INFRA", "TOOL"])
            passed = is_uppercase and ends_with_underscore and is_relevant
            checks.append(check(
                "configx.NormalizeEnv called with valid uppercase TOOLNAME_ prefix",
                passed,
                f"Found prefix: '{prefix}', uppercase={is_uppercase}, trailing_={ends_with_underscore}, relevant={is_relevant}"
            ))
        else:
            has_normalize = "NormalizeEnv" in content
            checks.append(check(
                "configx.NormalizeEnv called with valid uppercase TOOLNAME_ prefix",
                False,
                f"NormalizeEnv not found in config/load.go. has_normalize={has_normalize}, content={content[:400]}"
            ))
    except Exception as e:
        checks.append(check("configx.NormalizeEnv called with valid uppercase TOOLNAME_ prefix", False, str(e)))

    # ── CHECK 8: configx.Decode used for typed config ──
    try:
        content = config_load.read_text()
        has_decode = "configx.Decode" in content or ("Decode" in content and "configx" in content)
        checks.append(check(
            "internal/config/load.go uses configx.Decode for typed config",
            has_decode,
            f"has_decode={has_decode}, snippet={content[:400]}"
        ))
    except Exception as e:
        checks.append(check("internal/config/load.go uses configx.Decode for typed config", False, str(e)))

    # ── CHECK 9: Correct precedence chain (Defaults, FilePath, Env, Flags in Options) ──
    try:
        content = config_load.read_text()
        has_defaults = "Defaults" in content
        has_filepath = "FilePath" in content
        has_env = "Env" in content and "NormalizeEnv" in content
        has_flags = "Flags" in content
        passed = has_defaults and has_filepath and has_env
        checks.append(check(
            "configx.Options includes Defaults, FilePath, and Env (full precedence chain)",
            passed,
            f"Defaults={has_defaults}, FilePath={has_filepath}, Env={has_env}, Flags={has_flags}"
        ))
    except Exception as e:
        checks.append(check("configx.Options includes Defaults, FilePath, and Env (full precedence chain)", False, str(e)))

    # ── CHECK 10: Golden layout structure - key directories exist ──
    required_dirs = [
        project_dir / "cmd",
        project_dir / "internal" / "app",
        project_dir / "internal" / "config",
        project_dir / "internal" / "io",
        project_dir / "pkg" / "version",
        project_dir / "test",
    ]
    missing_dirs = [str(d.relative_to(workspace)) for d in required_dirs if not d.is_dir()]
    checks.append(check(
        "Golden layout directories all exist",
        len(missing_dirs) == 0,
        f"Missing: {missing_dirs}" if missing_dirs else "All required directories present"
    ))

    # ── CHECK 11: internal/app has lifecycle.go or RunLifecycle usage ──
    app_dir = project_dir / "internal" / "app"
    try:
        app_files = list(app_dir.glob("*.go"))
        all_app_content = " ".join(f.read_text() for f in app_files)
        has_lifecycle = "lifecycle" in " ".join(f.name for f in app_files).lower() or "RunLifecycle" in all_app_content or "Lifecycle" in all_app_content
        checks.append(check(
            "internal/app/ contains lifecycle handling (lifecycle.go or RunLifecycle usage)",
            has_lifecycle,
            f"Files: {[f.name for f in app_files]}, has_lifecycle={has_lifecycle}"
        ))
    except Exception as e:
        checks.append(check("internal/app/ contains lifecycle handling", False, str(e)))

    # ── CHECK 12: go.mod contains agentcli-go dependency ──
    go_mod = project_dir / "go.mod"
    try:
        content = go_mod.read_text()
        has_agentcli = "agentcli-go" in content or "agentcli" in content
        has_correct_module = "github.com/platform-team/infra-deployer" in content
        checks.append(check(
            "go.mod has correct module path and agentcli-go dependency",
            has_correct_module and has_agentcli,
            f"module_ok={has_correct_module}, agentcli_dep={has_agentcli}, snippet={content[:300]}"
        ))
    except Exception as e:
        checks.append(check("go.mod has correct module path and agentcli-go dependency", False, str(e)))

    # ── CHECK 13: pkg/version/version.go exists ──
    version_go = project_dir / "pkg" / "version" / "version.go"
    try:
        content = version_go.read_text()
        has_version = "Version" in content
        checks.append(check(
            "pkg/version/version.go exists with Version constant",
            has_version,
            f"snippet={content[:200]}"
        ))
    except Exception as e:
        checks.append(check("pkg/version/version.go exists with Version constant", False, str(e)))

    # ── CHECK 14: No manually wired persistent flags (verbose, json, no-color) in root.go ──
    try:
        content = root_go.read_text()
        # These flags are auto-wired by cobrax, should NOT be manually defined
        manually_added_flags = (
            'PersistentFlags().BoolP("verbose"' in content or
            'PersistentFlags().Bool("verbose"' in content or
            'PersistentFlags().BoolP("json"' in content or
            'PersistentFlags().StringP("no-color"' in content
        )
        checks.append(check(
            "cmd/root.go does NOT manually wire cobrax auto-wired flags (verbose/json/no-color)",
            not manually_added_flags,
            f"manually_added_persistent_flags={manually_added_flags}, snippet={content[:400]}"
        ))
    except Exception as e:
        checks.append(check("cmd/root.go does NOT manually wire cobrax auto-wired flags", False, str(e)))

    # ── Compute score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= int(total * 0.75)  # 75% threshold for pass

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))