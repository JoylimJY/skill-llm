import sys
import json
import subprocess
import os

def run_eval(workspace_dir):
    checks = []
    memo_dir = os.path.join(workspace_dir, "memo-collect")
    memos_json_path = os.path.join(memo_dir, "memos.json")

    # Check 1: memos.json exists (any operations were performed)
    check_file_exists = {"name": "memos.json_exists", "passed": False, "detail": ""}
    if os.path.isfile(memos_json_path):
        check_file_exists["passed"] = True
        check_file_exists["detail"] = "memos.json file found."
    else:
        check_file_exists["detail"] = "memos.json not found. No memo operations seem to have been performed."
    checks.append(check_file_exists)

    # Load current memo state via list_memo command
    check_list_output = {"name": "list_memo_runs_successfully", "passed": False, "detail": ""}
    try:
        result = subprocess.run(
            ["node", "dist/index.js", "list_memo"],
            capture_output=True, text=True, cwd=memo_dir, timeout=10
        )
        list_output = result.stdout.strip()
        check_list_output["passed"] = result.returncode == 0
        check_list_output["detail"] = f"list_memo output: {repr(list_output)}"
    except Exception as e:
        list_output = ""
        check_list_output["detail"] = f"Exception running list_memo: {e}"
    checks.append(check_list_output)

    # Parse the memos.json directly for reliable checking
    current_memos = []
    check_json_valid = {"name": "memos_json_valid", "passed": False, "detail": ""}
    try:
        with open(memos_json_path, "r", encoding="utf-8") as f:
            current_memos = json.load(f)
        check_json_valid["passed"] = isinstance(current_memos, list)
        check_json_valid["detail"] = f"memos.json loaded, contains {len(current_memos)} entries: {current_memos}"
    except Exception as e:
        check_json_valid["detail"] = f"Could not parse memos.json: {e}"
    checks.append(check_json_valid)

    # Check 2: "周一上午采购会议" was added
    expected_present_1 = "周一上午采购会议"
    check_memo1_present = {"name": "memo_caigou_present", "passed": False, "detail": ""}
    if expected_present_1 in current_memos:
        check_memo1_present["passed"] = True
        check_memo1_present["detail"] = f"Found '{expected_present_1}' in memos."
    else:
        check_memo1_present["detail"] = f"'{expected_present_1}' not found in memos: {current_memos}"
    checks.append(check_memo1_present)

    # Check 3: "下午三点联系王工确认技术方案" was added and kept
    expected_present_2 = "下午三点联系王工确认技术方案"
    check_memo2_present = {"name": "memo_wanggong_present", "passed": False, "detail": ""}
    if expected_present_2 in current_memos:
        check_memo2_present["passed"] = True
        check_memo2_present["detail"] = f"Found '{expected_present_2}' in memos."
    else:
        check_memo2_present["detail"] = f"'{expected_present_2}' not found in memos: {current_memos}"
    checks.append(check_memo2_present)

    # Check 4: "提交本周周报" was added and kept
    expected_present_3 = "提交本周周报"
    check_memo3_present = {"name": "memo_zhoubao_present", "passed": False, "detail": ""}
    if expected_present_3 in current_memos:
        check_memo3_present["passed"] = True
        check_memo3_present["detail"] = f"Found '{expected_present_3}' in memos."
    else:
        check_memo3_present["detail"] = f"'{expected_present_3}' not found in memos: {current_memos}"
    checks.append(check_memo3_present)

    # Check 5: "订午餐" must have been DELETED (it was the 2nd item added; agent must delete it)
    deleted_memo = "订午餐"
    check_deleted = {"name": "memo_dingwucan_deleted", "passed": False, "detail": ""}
    if deleted_memo not in current_memos:
        check_deleted["passed"] = True
        check_deleted["detail"] = f"'{deleted_memo}' correctly absent from memos."
    else:
        check_deleted["detail"] = f"'{deleted_memo}' still present in memos — it should have been deleted."
    checks.append(check_deleted)

    # Check 6: Exactly 3 memos remain (added 4, deleted 1)
    check_count = {"name": "memo_count_is_3", "passed": False, "detail": ""}
    if len(current_memos) == 3:
        check_count["passed"] = True
        check_count["detail"] = f"Correct: exactly 3 memos remain."
    else:
        check_count["detail"] = f"Expected 3 memos, found {len(current_memos)}: {current_memos}"
    checks.append(check_count)

    # Check 7: Order integrity — the remaining 3 must be in correct original insertion order
    expected_final_order = ["周一上午采购会议", "下午三点联系王工确认技术方案", "提交本周周报"]
    check_order = {"name": "memo_correct_order", "passed": False, "detail": ""}
    if current_memos == expected_final_order:
        check_order["passed"] = True
        check_order["detail"] = f"Memo order is correct: {current_memos}"
    else:
        check_order["detail"] = f"Memo order mismatch. Expected {expected_final_order}, got {current_memos}"
    checks.append(check_order)

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = all(c["passed"] for c in checks)

    return {"passed": all_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))