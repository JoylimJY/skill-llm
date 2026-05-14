import json
import os
import sys
import stat
from pathlib import Path

def load_json_file(path):
    with open(path) as f:
        return json.load(f)

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 6  # 6 equal-weight checks

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 1: mcp_server_config.json — correct package name
    # ══════════════════════════════════════════════════════════════════════
    mcp_config_files = list(workspace.rglob("mcp_server_config.json"))
    if not mcp_config_files:
        checks.append({
            "name": "mcp_config_file_exists",
            "passed": False,
            "detail": "mcp_server_config.json not found anywhere in workspace"
        })
        # Cannot do further checks on this file
        checks.extend([
            {"name": "mcp_config_package_and_version", "passed": False, "detail": "File missing"},
            {"name": "mcp_config_transport_and_command", "passed": False, "detail": "File missing"},
        ])
    else:
        mcp_config_path = mcp_config_files[0]
        try:
            mcp_cfg = load_json_file(mcp_config_path)
        except Exception as e:
            checks.append({"name": "mcp_config_file_exists", "passed": False, "detail": f"JSON parse error: {e}"})
            checks.extend([
                {"name": "mcp_config_package_and_version", "passed": False, "detail": "Unparseable"},
                {"name": "mcp_config_transport_and_command", "passed": False, "detail": "Unparseable"},
            ])
        else:
            checks.append({"name": "mcp_config_file_exists", "passed": True, "detail": str(mcp_config_path)})

            # Check package name and pinned version
            try:
                servers = mcp_cfg.get("mcpServers", {})
                leetcode_entry = servers.get("leetcode", {})
                args = leetcode_entry.get("args", [])
                # Must contain exact pinned package string
                args_str = " ".join(str(a) for a in args)
                has_correct_package = "@sperekrestova/interactive-leetcode-mcp@3.1.1" in args_str
                not_latest = "@latest" not in args_str
                passed_pkg = has_correct_package and not_latest
                checks.append({
                    "name": "mcp_config_package_and_version",
                    "passed": passed_pkg,
                    "detail": f"args={args}, need @sperekrestova/interactive-leetcode-mcp@3.1.1 (not @latest). found_correct={has_correct_package}, no_latest={not_latest}"
                })
            except Exception as e:
                checks.append({"name": "mcp_config_package_and_version", "passed": False, "detail": str(e)})

            # Check command is npx and -y flag is present (stdio transport implied by no transport field or stdio)
            try:
                command = leetcode_entry.get("command", "")
                args = leetcode_entry.get("args", [])
                has_npx = command == "npx"
                has_y_flag = "-y" in args
                # Must NOT specify http transport (stdio is correct — either no transport field or "stdio")
                transport = leetcode_entry.get("transport", "stdio")
                transport_ok = transport in ("stdio", "")
                passed_transport = has_npx and has_y_flag and transport_ok
                checks.append({
                    "name": "mcp_config_transport_and_command",
                    "passed": passed_transport,
                    "detail": f"command={command}, args={args}, transport={transport}. need: npx, -y flag, stdio transport (not http/sse)"
                })
            except Exception as e:
                checks.append({"name": "mcp_config_transport_and_command", "passed": False, "detail": str(e)})

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 2: Credentials file at ~/.leetcode-mcp/credentials.json
    #          with correct fields AND correct permissions 0600
    # ══════════════════════════════════════════════════════════════════════
    # Resolve ~ relative to the actual home dir of devuser
    # In the container, devuser home is /home/devuser
    home_dir = Path("/home/devuser")
    creds_path = home_dir / ".leetcode-mcp" / "credentials.json"

    try:
        if not creds_path.exists():
            checks.append({
                "name": "credentials_file_path_and_fields",
                "passed": False,
                "detail": f"credentials.json not found at {creds_path}"
            })
            checks.append({
                "name": "credentials_file_permissions",
                "passed": False,
                "detail": "File missing — cannot check permissions"
            })
        else:
            creds_data = load_json_file(creds_path)
            required_fields = {"csrftoken", "LEETCODE_SESSION", "createdAt"}
            # The distractor uses "created_at" (underscore) — must catch that
            present_fields = set(creds_data.keys())
            has_all_fields = required_fields.issubset(present_fields)
            # Must NOT have wrong field names from the distractor template
            has_wrong_fields = "created_at" in present_fields or "token" in present_fields or "password" in present_fields
            fields_ok = has_all_fields and not has_wrong_fields
            checks.append({
                "name": "credentials_file_path_and_fields",
                "passed": fields_ok,
                "detail": f"present={sorted(present_fields)}, required={sorted(required_fields)}, wrong_fields={has_wrong_fields}"
            })

            # Check permissions — must be exactly 0600
            file_stat = os.stat(creds_path)
            file_mode = stat.S_IMODE(file_stat.st_mode)
            perms_ok = file_mode == 0o600
            checks.append({
                "name": "credentials_file_permissions",
                "passed": perms_ok,
                "detail": f"actual mode={oct(file_mode)}, expected=0o600 (owner read/write only)"
            })
    except Exception as e:
        checks.append({"name": "credentials_file_path_and_fields", "passed": False, "detail": str(e)})
        checks.append({"name": "credentials_file_permissions", "passed": False, "detail": str(e)})

    # ══════════════════════════════════════════════════════════════════════
    # CHECK 3: session_workflow.json — correct step order + language map
    # ══════════════════════════════════════════════════════════════════════
    workflow_files = list(workspace.rglob("session_workflow.json"))
    if not workflow_files:
        checks.append({
            "name": "session_workflow_steps_order",
            "passed": False,
            "detail": "session_workflow.json not found anywhere in workspace"
        })
        checks.append({
            "name": "session_workflow_language_map",
            "passed": False,
            "detail": "File missing"
        })
    else:
        wf_path = workflow_files[0]
        try:
            wf_data = load_json_file(wf_path)
        except Exception as e:
            checks.append({"name": "session_workflow_steps_order", "passed": False, "detail": f"JSON parse error: {e}"})
            checks.append({"name": "session_workflow_language_map", "passed": False, "detail": "Unparseable"})
        else:
            # Steps must appear in correct order; we look for a list of steps
            # Accept either a key "steps" with a list, or top-level list
            steps = wf_data.get("steps", wf_data if isinstance(wf_data, list) else [])

            # Canonical 6-step flow from SKILL.md (we check keyword presence in order):
            # 1. get_started
            # 2. leetcode_learning_mode
            # 3. (user picks problem)
            # 4. leetcode_problem_workflow
            # 5. leetcode_workspace_setup
            # 6. submit_solution
            REQUIRED_STEP_KEYWORDS_IN_ORDER = [
                "get_started",
                "learning_mode",
                "problem_workflow",
                "workspace_setup",
                "submit",
            ]

            def find_keyword_in_step(keyword, step):
                step_str = json.dumps(step).lower() if not isinstance(step, str) else step.lower()
                return keyword.lower() in step_str

            steps_list = steps if isinstance(steps, list) else []
            last_found_idx = -1
            order_ok = True
            order_detail = []
            for kw in REQUIRED_STEP_KEYWORDS_IN_ORDER:
                found = False
                for i, step in enumerate(steps_list):
                    if i > last_found_idx and find_keyword_in_step(kw, step):
                        last_found_idx = i
                        found = True
                        order_detail.append(f"'{kw}' at position {i}")
                        break
                if not found:
                    order_ok = False
                    order_detail.append(f"'{kw}' NOT FOUND after position {last_found_idx}")

            # CRITICAL: get_started must be FIRST (index 0 or very early)
            first_step_is_get_started = False
            if steps_list:
                first_step_str = json.dumps(steps_list[0]).lower() if not isinstance(steps_list[0], str) else steps_list[0].lower()
                first_step_is_get_started = "get_started" in first_step_str

            # learning_mode must appear BEFORE problem_workflow
            lm_pos = next((i for i, s in enumerate(steps_list) if find_keyword_in_step("learning_mode", s)), None)
            pw_pos = next((i for i, s in enumerate(steps_list) if find_keyword_in_step("problem_workflow", s)), None)
            lm_before_pw = (lm_pos is not None and pw_pos is not None and lm_pos < pw_pos)

            steps_passed = order_ok and first_step_is_get_started and lm_before_pw
            checks.append({
                "name": "session_workflow_steps_order",
                "passed": steps_passed,
                "detail": f"order={order_detail}, get_started_first={first_step_is_get_started}, lm_before_pw={lm_before_pw} (lm@{lm_pos}, pw@{pw_pos})"
            })

            # Language map check — must correctly map Python → python3 (not "python" or "Python3")
            lang_map = wf_data.get("language_map", wf_data.get("languageMap", {}))
            lang_detail = []
            lang_ok = True

            REQUIRED_MAPPINGS = {
                # key variants agent might use → required output value
                "python3_mapping": (["python", "python3", "Python", "Python 3", "Python3"], "python3"),
                "python2_mapping": (["python2", "Python 2", "Python2"], "python"),
                "javascript_mapping": (["javascript", "JavaScript"], "javascript"),
                "typescript_mapping": (["typescript", "TypeScript"], "typescript"),
                "cpp_mapping": (["cpp", "c++", "C++"], "cpp"),
                "java_mapping": (["java", "Java"], "java"),
            }

            if not isinstance(lang_map, dict) or len(lang_map) == 0:
                lang_ok = False
                lang_detail.append("language_map is missing or empty")
            else:
                # CRITICAL TRAP: "Python" (without version) → must map to "python3" not "python"
                # Find the key that represents "Python" (default case)
                python_default_ok = False
                for key, val in lang_map.items():
                    key_lower = key.lower().strip()
                    if key_lower in ("python", "python 3", "python3") and val == "python3":
                        python_default_ok = True
                        break
                    elif key_lower == "python" and val == "python":
                        # This is the common TRAP — Python without version → should be python3
                        lang_ok = False
                        lang_detail.append(f"TRAP: 'Python' mapped to 'python' but should be 'python3'")
                        break

                if not python_default_ok and lang_ok:
                    lang_ok = False
                    lang_detail.append("No correct Python → python3 mapping found")
                else:
                    lang_detail.append(f"Python→python3 correct: {python_default_ok}")

                # Check Python 2 mapping
                python2_ok = any(
                    v == "python"
                    for k, v in lang_map.items()
                    if "2" in k.lower() or k.lower() == "python 2"
                )
                lang_detail.append(f"Python2→python: {python2_ok}")

            checks.append({
                "name": "session_workflow_language_map",
                "passed": lang_ok,
                "detail": "; ".join(lang_detail) + f" | raw_map={lang_map}"
            })

    # ══════════════════════════════════════════════════════════════════════
    # Scoring
    # ══════════════════════════════════════════════════════════════════════
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / max_score, 4)
    all_passed = passed_count == max_score

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/devuser/workspace"
    run_eval(workspace_dir)