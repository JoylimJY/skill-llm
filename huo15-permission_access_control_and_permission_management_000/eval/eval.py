import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # ── CHECK 1: config.json exists at the exact proprietary path ────────────
    config_path = Path.home() / ".openclaw/workspace/skills/huo15-permission/config.json"
    check1_passed = False
    check1_detail = ""
    try:
        if config_path.exists():
            cfg = load_json_file(config_path)
            check1_passed = True
            check1_detail = f"config.json found at correct path: {config_path}"
        else:
            check1_detail = f"config.json NOT found at required path: {config_path}"
    except Exception as e:
        check1_detail = f"Error reading config.json: {e}"
    checks.append({"name": "config_at_correct_path", "passed": check1_passed, "detail": check1_detail})
    if check1_passed:
        total_score += 1.0

    # ── CHECK 2: config.json has correct schema with required users ───────────
    check2_passed = False
    check2_detail = ""
    cfg = None
    try:
        if check1_passed:
            cfg = load_json_file(config_path)
            perms = cfg.get("permissions", {})
            required_users = {"ZhaoBo": 3, "Xun": 2, "HuangShuo": 2, "LiuYang": 2}
            missing = []
            wrong = []
            for user, expected_level in required_users.items():
                if user not in perms:
                    missing.append(user)
                elif int(perms[user]) != expected_level:
                    wrong.append(f"{user}: expected {expected_level}, got {perms[user]}")
            if not missing and not wrong:
                check2_passed = True
                check2_detail = "All required users present with correct permission levels."
            else:
                check2_detail = f"Missing users: {missing}; Wrong levels: {wrong}"
        else:
            check2_detail = "Skipped: config.json not found."
    except Exception as e:
        check2_detail = f"Error: {e}"
    checks.append({"name": "config_correct_permission_levels", "passed": check2_passed, "detail": check2_detail})
    if check2_passed:
        total_score += 1.0

    # ── CHECK 3: config.json has operation_keywords section ──────────────────
    check3_passed = False
    check3_detail = ""
    try:
        if cfg is None and check1_passed:
            cfg = load_json_file(config_path)
        if cfg:
            op_kw = cfg.get("operation_keywords", {})
            # Must have create, update, delete keys with Chinese keywords
            required_keys = {"create", "update", "delete"}
            has_keys = required_keys.issubset(set(op_kw.keys()))
            # Check some expected Chinese keywords
            create_kw = op_kw.get("create", [])
            update_kw = op_kw.get("update", [])
            delete_kw = op_kw.get("delete", [])
            has_chinese_create = any(k in create_kw for k in ["新增", "创建", "添加", "新建"])
            has_chinese_update = any(k in update_kw for k in ["修改", "编辑", "更新", "变更"])
            has_chinese_delete = any(k in delete_kw for k in ["删除", "移除", "清除"])
            if has_keys and has_chinese_create and has_chinese_update and has_chinese_delete:
                check3_passed = True
                check3_detail = "operation_keywords section present with correct Chinese keywords."
            else:
                check3_detail = (f"has_keys={has_keys}, "
                                 f"create_ok={has_chinese_create}, "
                                 f"update_ok={has_chinese_update}, "
                                 f"delete_ok={has_chinese_delete}")
        else:
            check3_detail = "Skipped: config.json not accessible."
    except Exception as e:
        check3_detail = f"Error: {e}"
    checks.append({"name": "config_has_operation_keywords", "passed": check3_passed, "detail": check3_detail})
    if check3_passed:
        total_score += 1.0

    # ── CHECK 4: Output file permission_check_results.json exists ────────────
    results_files = list(Path(workspace).rglob("permission_check_results.json"))
    check4_passed = len(results_files) > 0
    check4_detail = f"Found at: {results_files[0]}" if check4_passed else "permission_check_results.json not found anywhere in workspace."
    checks.append({"name": "results_file_exists", "passed": check4_passed, "detail": check4_detail})
    if check4_passed:
        total_score += 1.0

    # ── CHECK 5: Results file correctly identifies allowed/denied cases ───────
    check5_passed = False
    check5_detail = ""
    results_data = None
    try:
        if check4_passed:
            results_data = load_json_file(results_files[0])
            # Load original test cases from task_spec.json
            spec_path = Path(workspace) / "task_spec.json"
            spec = load_json_file(spec_path)
            test_cases = spec["test_cases"]

            # Build a lookup from results
            # Results should be a list of objects with at least 'id' and 'allowed' (bool)
            # or could be keyed by id
            if isinstance(results_data, list):
                result_map = {str(r.get("id", "")): r for r in results_data}
            elif isinstance(results_data, dict):
                # Could be {tc001: {...}, ...} or have a 'results' key
                if "results" in results_data:
                    result_map = {str(r.get("id", "")): r for r in results_data["results"]}
                else:
                    result_map = {str(k): v for k, v in results_data.items()}
            else:
                result_map = {}

            correct = 0
            errors = []
            for tc in test_cases:
                tc_id = tc["id"]
                expected = tc["expected_allowed"]
                result_entry = result_map.get(tc_id, None)
                if result_entry is None:
                    errors.append(f"{tc_id}: missing from results")
                    continue
                # Look for 'allowed' or 'permitted' or 'result' key
                actual = None
                for key in ["allowed", "permitted", "result", "is_allowed", "passed"]:
                    if key in result_entry:
                        val = result_entry[key]
                        if isinstance(val, bool):
                            actual = val
                        elif isinstance(val, str):
                            actual = val.lower() in ("true", "allowed", "yes", "permit", "permitted")
                        break
                if actual is None:
                    errors.append(f"{tc_id}: no 'allowed' field found in result entry")
                    continue
                if actual == expected:
                    correct += 1
                else:
                    errors.append(f"{tc_id}: expected allowed={expected}, got allowed={actual} (user={tc['userid']}, action={tc['action']})")

            total_cases = len(test_cases)
            if correct == total_cases:
                check5_passed = True
                check5_detail = f"All {total_cases} test cases correctly evaluated."
            else:
                check5_detail = f"{correct}/{total_cases} correct. Errors: {errors}"
        else:
            check5_detail = "Skipped: results file not found."
    except Exception as e:
        check5_detail = f"Error evaluating results: {e}"
    checks.append({"name": "results_correct_allow_deny", "passed": check5_passed, "detail": check5_detail})
    if check5_passed:
        total_score += 2.0  # Weighted higher

    # ── CHECK 6: Denied responses contain the exact proprietary error message ─
    check6_passed = False
    check6_detail = ""
    EXPECTED_PHRASES = [
        "抱歉，您的权限不足",
        "ZhaoBo"
    ]
    try:
        if check4_passed and results_data is not None:
            # Find any denied case and check the message
            if isinstance(results_data, list):
                denied_entries = [r for r in results_data if r.get("allowed") is False or 
                                  str(r.get("allowed","")).lower() in ("false","denied","no")]
            elif isinstance(results_data, dict) and "results" in results_data:
                denied_entries = [r for r in results_data["results"] if r.get("allowed") is False or 
                                  str(r.get("allowed","")).lower() in ("false","denied","no")]
            else:
                denied_entries = []

            if not denied_entries:
                check6_detail = "No denied entries found to check message content."
            else:
                found_message_checks = []
                for entry in denied_entries:
                    msg = entry.get("message", entry.get("response", entry.get("reason", "")))
                    if msg:
                        has_all = all(phrase in msg for phrase in EXPECTED_PHRASES)
                        found_message_checks.append(has_all)

                if not found_message_checks:
                    check6_detail = "Denied entries present but no 'message'/'response'/'reason' field found."
                elif any(found_message_checks):
                    check6_passed = True
                    check6_detail = f"At least one denied entry contains the required proprietary error message phrases."
                else:
                    check6_detail = (f"Denied entries present but message does not contain required phrases: "
                                     f"{EXPECTED_PHRASES}. Sample msg: {denied_entries[0].get('message', denied_entries[0].get('response', ''))[:200]}")
        else:
            check6_detail = "Skipped: results file not found or inaccessible."
    except Exception as e:
        check6_detail = f"Error: {e}"
    checks.append({"name": "denied_response_correct_message", "passed": check6_passed, "detail": check6_detail})
    if check6_passed:
        total_score += 1.0

    # ── CHECK 7: Distinguish delete-content (allowed) vs delete-skill (denied) for level-2 ─
    check7_passed = False
    check7_detail = ""
    try:
        if check4_passed and results_data is not None:
            if isinstance(results_data, list):
                result_map2 = {str(r.get("id", "")): r for r in results_data}
            elif isinstance(results_data, dict) and "results" in results_data:
                result_map2 = {str(r.get("id", "")): r for r in results_data["results"]}
            else:
                result_map2 = result_map if 'result_map' in dir() else {}

            # tc007: LiuYang + "删除" (content delete) -> allowed=True
            # tc003: HuangShuo + "卸载技能" (uninstall skill) -> allowed=False
            tc007 = result_map2.get("tc007", {})
            tc003 = result_map2.get("tc003", {})

            def get_allowed(entry):
                for key in ["allowed", "permitted", "result", "is_allowed"]:
                    if key in entry:
                        val = entry[key]
                        if isinstance(val, bool):
                            return val
                        if isinstance(val, str):
                            return val.lower() in ("true", "allowed", "yes")
                return None

            tc007_allowed = get_allowed(tc007)
            tc003_allowed = get_allowed(tc003)

            if tc007_allowed is True and tc003_allowed is False:
                check7_passed = True
                check7_detail = "Correctly distinguishes content-delete (allowed) from skill-uninstall (denied) for level-2 users."
            else:
                check7_detail = (f"tc007 (删除 content, LiuYang): expected True, got {tc007_allowed}; "
                                 f"tc003 (卸载技能, HuangShuo): expected False, got {tc003_allowed}")
        else:
            check7_detail = "Skipped: results not available."
    except Exception as e:
        check7_detail = f"Error: {e}"
    checks.append({"name": "content_delete_vs_skill_delete_distinction", "passed": check7_passed, "detail": check7_detail})
    if check7_passed:
        total_score += 2.0  # This is the hardest proprietary trap

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_score = 9.0
    normalized_score = round(total_score / max_score, 4)
    overall_passed = check1_passed and check2_passed and check4_passed and check5_passed and check7_passed

    output = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return output

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)