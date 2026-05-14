import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"

def run_eval(workspace: str):
    checks = []
    
    project_dir = Path(workspace) / "platform-engineering" / "ai-workspace"
    skills_json_path = project_dir / "skills.json"
    
    # Load skills.json
    skills_data, err = load_json_safe(skills_json_path)
    if skills_data is None:
        checks.append({"name": "skills.json exists and is valid JSON", "passed": False, "detail": err})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({"name": "skills.json exists and is valid JSON", "passed": True, "detail": str(skills_json_path)})

    # CHECK 1: registries.corp alias
    check_name = "registries.corp alias is set correctly"
    try:
        registries = skills_data.get("registries", {})
        corp_url = registries.get("corp", "")
        expected_url = "https://gitlab.corp-internal.example.com"
        passed = corp_url == expected_url
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected registries.corp='{expected_url}', got '{corp_url}'"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 2: defaults.installDir
    check_name = "defaults.installDir is set to .agent-skills"
    try:
        defaults = skills_data.get("defaults", {})
        install_dir = defaults.get("installDir", "")
        passed = install_dir == ".agent-skills"
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected '.agent-skills', got '{install_dir}'"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 3: defaults.targetAgents contains claude-code and codex
    check_name = "defaults.targetAgents includes claude-code and codex"
    try:
        defaults = skills_data.get("defaults", {})
        target_agents = defaults.get("targetAgents", [])
        has_claude = "claude-code" in target_agents
        has_codex = "codex" in target_agents
        passed = has_claude and has_codex
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected ['claude-code', 'codex'] (any order), got {target_agents}"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 4: defaults.installMode is copy
    check_name = "defaults.installMode is set to copy"
    try:
        defaults = skills_data.get("defaults", {})
        install_mode = defaults.get("installMode", "")
        passed = install_mode == "copy"
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected 'copy', got '{install_mode}'"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 5: skills.api-gateway uses monorepo subpath github format with correct version
    check_name = "skills.api-gateway uses correct github monorepo subpath format @v1.2.0"
    try:
        skills = skills_data.get("skills", {})
        api_gw = skills.get("api-gateway", "")
        # Must match github:nicepkg/reskill/skills/api-gateway@v1.2.0
        # Key: the monorepo subpath /skills/api-gateway and exact version @v1.2.0
        import re
        # Accept the canonical monorepo format: github:nicepkg/reskill/skills/api-gateway@v1.2.0
        pattern = r'^github:nicepkg/reskill/skills/api-gateway@v1\.2\.0$'
        passed = bool(re.match(pattern, api_gw))
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected 'github:nicepkg/reskill/skills/api-gateway@v1.2.0', got '{api_gw}'"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 6: skills.corp-toolkit uses corp registry alias with branch:stable version
    check_name = "skills.corp-toolkit uses corp registry alias with branch:stable version format"
    try:
        skills = skills_data.get("skills", {})
        corp_tk = skills.get("corp-toolkit", "")
        # Must use corp: alias and @branch:stable version format
        # canonical: corp:devops/agent-tools@branch:stable
        import re
        pattern = r'^corp:devops/agent-tools@branch:stable$'
        passed = bool(re.match(pattern, corp_tk))
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"Expected 'corp:devops/agent-tools@branch:stable', got '{corp_tk}'"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 7: The personal/global skill (nicepkg/reskill) is NOT in skills.json
    check_name = "Personal global skill does NOT appear in skills.json (--no-save / -g semantics)"
    try:
        skills = skills_data.get("skills", {})
        # The personal skill source is github:nicepkg/reskill (no subpath, no version)
        # We check no skill value in skills.json refers to the root nicepkg/reskill without subpath
        personal_found = False
        for name, ref in skills.items():
            # The personal skill is github:nicepkg/reskill@... or github:nicepkg/reskill (no subpath)
            # Subpath version like github:nicepkg/reskill/skills/api-gateway is fine
            import re
            # Matches github:nicepkg/reskill but NOT github:nicepkg/reskill/something
            if re.match(r'^github:nicepkg/reskill(@[^/].*)?$', ref):
                personal_found = True
                break
        passed = not personal_found
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": "Personal skill github:nicepkg/reskill (root) should not be in skills.json" if not passed else "Correctly absent from skills.json"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # CHECK 8: The broken legacy fields are removed (no stale "version" key, no old-util)
    check_name = "Stale/broken fields from original skills.json are cleaned up"
    try:
        has_stale_version_key = "version" in skills_data
        skills = skills_data.get("skills", {})
        has_old_util = "old-util" in skills
        passed = not has_stale_version_key and not has_old_util
        checks.append({
            "name": check_name,
            "passed": passed,
            "detail": f"stale 'version' key present: {has_stale_version_key}, 'old-util' skill present: {has_old_util}"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # Score calculation
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    result = {
        "passed": all(c["passed"] for c in checks),
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)