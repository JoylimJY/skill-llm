import sys
import json
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"

def run_eval(workspace):
    checks = []
    registry_path = Path.home() / ".openclaw" / "registries" / "application_registry.json"

    # --- CHECK 1: Registry file exists ---
    exists = registry_path.exists()
    checks.append({
        "name": "registry_file_exists",
        "passed": exists,
        "detail": str(registry_path) if exists else f"Missing: {registry_path}"
    })
    if not exists:
        return checks

    # --- Load registry ---
    data, err = load_json_safe(registry_path)
    checks.append({
        "name": "registry_is_valid_json",
        "passed": data is not None,
        "detail": err if err else "JSON parsed successfully"
    })
    if data is None:
        return checks

    # --- CHECK 2: Registry is pretty-printed (not compact) ---
    raw_text = registry_path.read_text(encoding="utf-8")
    is_pretty = "\n" in raw_text and "  " in raw_text
    checks.append({
        "name": "registry_is_pretty_printed",
        "passed": is_pretty,
        "detail": "Registry appears pretty-printed" if is_pretty else "Registry is compact/minified, not pretty-printed"
    })

    # --- CHECK 3: "Ops Console" entry exists (new app to be added) ---
    ops_console_key = None
    for k in data.keys():
        if k.lower() == "ops console":
            ops_console_key = k
            break
    has_ops_console = ops_console_key is not None
    checks.append({
        "name": "ops_console_entry_exists",
        "passed": has_ops_console,
        "detail": f"Found key '{ops_console_key}'" if has_ops_console else "No 'Ops Console' entry found in registry"
    })

    if has_ops_console:
        oc = data[ops_console_key]

        # CHECK 3a: Ops Console launch_path is non-empty
        lp = oc.get("launch_path", "")
        checks.append({
            "name": "ops_console_has_launch_path",
            "passed": bool(lp),
            "detail": f"launch_path='{lp}'" if lp else "launch_path is empty or missing"
        })

        # CHECK 3b: Ops Console mode is 'allowlist'
        mode = oc.get("mode", "")
        checks.append({
            "name": "ops_console_mode_is_allowlist",
            "passed": mode == "allowlist",
            "detail": f"mode='{mode}'"
        })

        # CHECK 3c: Ops Console allowed_agents is a non-empty array containing 'system_engineer'
        aa = oc.get("allowed_agents", None)
        aa_is_list = isinstance(aa, list)
        aa_nonempty = aa_is_list and len(aa) > 0
        aa_has_se = aa_is_list and "system_engineer" in aa
        checks.append({
            "name": "ops_console_allowed_agents_is_nonempty_list",
            "passed": aa_nonempty,
            "detail": f"allowed_agents={aa}"
        })
        checks.append({
            "name": "ops_console_allowed_agents_contains_system_engineer",
            "passed": aa_has_se,
            "detail": f"allowed_agents={aa}"
        })

        # CHECK 3d: Ops Console key uses friendly name (exact case match check - must be "Ops Console")
        correct_key = ops_console_key == "Ops Console"
        checks.append({
            "name": "ops_console_key_is_exact_friendly_name",
            "passed": correct_key,
            "detail": f"Key is '{ops_console_key}', expected 'Ops Console'"
        })

    # --- CHECK 4: "RobotArm Controller" was updated to mode='full' with cleared allowed_agents ---
    robot_key = None
    for k in data.keys():
        if k.lower() == "robotarm controller":
            robot_key = k
            break
    has_robot = robot_key is not None
    checks.append({
        "name": "robotarm_controller_entry_exists",
        "passed": has_robot,
        "detail": f"Found key '{robot_key}'" if has_robot else "No 'RobotArm Controller' entry found"
    })

    if has_robot:
        ra = data[robot_key]

        # CHECK 4a: mode is 'full'
        mode = ra.get("mode", "")
        checks.append({
            "name": "robotarm_mode_is_full",
            "passed": mode == "full",
            "detail": f"mode='{mode}'"
        })

        # CHECK 4b: allowed_agents is EMPTY array (critical proprietary trap: switching to full must clear agents)
        aa = ra.get("allowed_agents", None)
        aa_is_list = isinstance(aa, list)
        aa_is_empty = aa_is_list and len(aa) == 0
        checks.append({
            "name": "robotarm_allowed_agents_cleared_on_full_mode",
            "passed": aa_is_empty,
            "detail": f"allowed_agents={aa} (must be [] when mode=full)"
        })

        # CHECK 4c: Original fields preserved (launch_path must still be present)
        lp = ra.get("launch_path", "")
        checks.append({
            "name": "robotarm_launch_path_preserved",
            "passed": bool(lp),
            "detail": f"launch_path='{lp}'"
        })

    # --- CHECK 5: "DataVault" still exists and its policy mismatch is corrected OR flagged ---
    # The task asks agent to validate the registry. We check that DataVault's policy is corrected:
    # Either mode was changed to non-allowlist, or allowed_agents was populated.
    dv_key = None
    for k in data.keys():
        if k.lower() == "datavault":
            dv_key = k
            break
    has_dv = dv_key is not None
    checks.append({
        "name": "datavault_entry_exists",
        "passed": has_dv,
        "detail": f"Found key '{dv_key}'" if has_dv else "DataVault entry missing from registry"
    })

    if has_dv:
        dv = data[dv_key]
        mode = dv.get("mode", "")
        aa = dv.get("allowed_agents", None)
        aa_is_list = isinstance(aa, list)
        # Policy is valid if: mode=allowlist AND allowed_agents non-empty, OR mode != allowlist AND aa is empty list
        valid_allowlist = (mode == "allowlist" and aa_is_list and len(aa) > 0)
        valid_full_or_off = (mode in ("full", "off") and aa_is_list and len(aa) == 0)
        dv_policy_ok = valid_allowlist or valid_full_or_off
        checks.append({
            "name": "datavault_policy_is_consistent",
            "passed": dv_policy_ok,
            "detail": f"mode='{mode}', allowed_agents={aa}. Policy must be consistent (allowlist needs agents; full/off need empty agents)"
        })

    # --- CHECK 6: "LegacyTool" still exists and launch_path issue is detectable (empty string is incomplete) ---
    lt_key = None
    for k in data.keys():
        if k.lower() == "legacytool":
            lt_key = k
            break
    has_lt = lt_key is not None
    checks.append({
        "name": "legacytool_entry_exists",
        "passed": has_lt,
        "detail": f"Found key '{lt_key}'" if has_lt else "LegacyTool entry missing — may have been deleted"
    })

    # --- CHECK 7: No extra top-level metadata fields injected (schema purity) ---
    known_app_keys = {"RobotArm Controller", "DataVault", "LegacyTool", "Ops Console"}
    for app_key, app_val in data.items():
        if isinstance(app_val, dict):
            extra_fields = set(app_val.keys()) - {"launch_path", "runtime_exe", "process_name", "mode", "allowed_agents"}
            if extra_fields:
                checks.append({
                    "name": f"no_extra_fields_in_{app_key.replace(' ','_')}",
                    "passed": False,
                    "detail": f"Unexpected extra fields in '{app_key}': {extra_fields}"
                })
            else:
                checks.append({
                    "name": f"no_extra_fields_in_{app_key.replace(' ','_')}",
                    "passed": True,
                    "detail": f"Schema clean for '{app_key}'"
                })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks = run_eval(workspace)
    except Exception as e:
        checks = [{"name": "eval_internal_error", "passed": False, "detail": str(e)}]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()