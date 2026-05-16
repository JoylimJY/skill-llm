import sys
import json
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []
    target_path = Path("/Users/aibin/.openclaw/workspace/diankeyuan_contacts.json")

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # Check 1: File exists at the correct proprietary path
    if not target_path.exists():
        add_check("file_exists_at_correct_path", False,
                  f"JSON file not found at {target_path}. Agent may have saved to wrong location.")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Load the JSON
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        add_check("file_is_valid_json", True, "JSON file parsed successfully.")
    except Exception as e:
        add_check("file_is_valid_json", False, f"Failed to parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Check 2: Top-level 'departments' key exists
    if "departments" not in data:
        add_check("has_departments_key", False, "Top-level 'departments' key missing from JSON.")
        return {"passed": False, "score": 0.0, "checks": checks}
    else:
        add_check("has_departments_key", True, "'departments' key exists.")

    departments = data["departments"]

    # Helper: find a member by name across all departments
    def find_member(name):
        for dept_name, dept_val in departments.items():
            if isinstance(dept_val, dict):
                for room_name, room_val in dept_val.items():
                    if isinstance(room_val, dict) and "members" in room_val:
                        for m in room_val["members"]:
                            if isinstance(m, dict) and m.get("name") == name:
                                return m, dept_name, room_name, room_val
        return None, None, None, None

    def find_room(dept_key, room_key):
        dept = departments.get(dept_key, {})
        return dept.get(room_key, None)

    # Check 3: 张磊 exists in 系统所 - 二次评估室
    zhang_lei, z_dept, z_room, z_room_val = find_member("张磊")
    if zhang_lei is None:
        add_check("zhang_lei_exists", False, "张磊 not found in any department.")
    else:
        add_check("zhang_lei_exists", True, f"张磊 found in {z_dept} - {z_room}.")

    # Check 4: 张磊 office is 1516 (corrected, NOT 1512)
    if zhang_lei is not None:
        if zhang_lei.get("office") == "1516":
            add_check("zhang_lei_office_corrected", True, "张磊's office correctly set to 1516.")
        else:
            add_check("zhang_lei_office_corrected", False,
                      f"张磊's office is '{zhang_lei.get('office')}', expected '1516' after correction.")
    else:
        add_check("zhang_lei_office_corrected", False, "张磊 not found, cannot check office.")

    # Check 5: 张磊 role is 高级工程师
    if zhang_lei is not None:
        if zhang_lei.get("role") in ("高级工程师",):
            add_check("zhang_lei_role", True, "张磊's role is 高级工程师.")
        else:
            add_check("zhang_lei_role", False,
                      f"张磊's role is '{zhang_lei.get('role')}', expected '高级工程师'.")
    else:
        add_check("zhang_lei_role", False, "张磊 not found, cannot check role.")

    # Check 6: 张磊 in correct department structure (系统所 → 二次评估室)
    if zhang_lei is not None:
        correct_dept = z_dept and ("系统所" in z_dept or z_dept == "系统所")
        correct_room = z_room and ("二次评估室" in z_room or z_room == "二次评估室")
        if correct_dept and correct_room:
            add_check("zhang_lei_correct_department", True, "张磊 in correct nested department structure.")
        else:
            add_check("zhang_lei_correct_department", False,
                      f"张磊 in wrong dept/room: {z_dept}/{z_room}, expected 系统所/二次评估室.")
    else:
        add_check("zhang_lei_correct_department", False, "张磊 not found.")

    # Check 7: 陈小燕 exists in 系统所 - 二次评估室 with correct role
    chen, c_dept, c_room, _ = find_member("陈小燕")
    if chen is None:
        add_check("chen_xiaoyan_exists", False, "陈小燕 not found.")
    else:
        c_correct_dept = c_dept and "系统所" in c_dept
        c_correct_room = c_room and "二次评估室" in c_room
        if c_correct_dept and c_correct_room and chen.get("role") in ("市场专员",):
            add_check("chen_xiaoyan_exists", True, "陈小燕 correctly added with role 市场专员 in 系统所 - 二次评估室.")
        else:
            add_check("chen_xiaoyan_exists", False,
                      f"陈小燕 found but wrong data: dept={c_dept}, room={c_room}, role={chen.get('role')}.")

    # Check 8: 刘强 (误录) should NOT exist
    liu_qiang, _, _, _ = find_member("刘强")
    if liu_qiang is None:
        add_check("liu_qiang_deleted", True, "刘强 (误录) correctly not present in the database.")
    else:
        add_check("liu_qiang_deleted", False, "刘强 (误录) found in the database; should have been deleted or never added.")

    # Check 9: 吴海涛 in 继电所 - 保护研究室, role 研究员
    wu, w_dept, w_room, _ = find_member("吴海涛")
    if wu is None:
        add_check("wu_haitao_exists", False, "吴海涛 not found.")
    else:
        w_cd = w_dept and "继电所" in w_dept
        w_cr = w_room and "保护研究室" in w_room
        if w_cd and w_cr and wu.get("role") == "研究员":
            add_check("wu_haitao_exists", True, "吴海涛 correctly added in 继电所 - 保护研究室 as 研究员.")
        else:
            add_check("wu_haitao_exists", False,
                      f"吴海涛 wrong data: dept={w_dept}, room={w_room}, role={wu.get('role')}.")

    # Check 10: 周敏 in 继电所 - 保护研究室, role corrected to 高级工程师
    zhou, zh_dept, zh_room, _ = find_member("周敏")
    if zhou is None:
        add_check("zhou_min_corrected", False, "周敏 not found.")
    else:
        zh_cd = zh_dept and "继电所" in zh_dept
        zh_cr = zh_room and "保护研究室" in zh_room
        if zh_cd and zh_cr and zhou.get("role") == "高级工程师":
            add_check("zhou_min_corrected", True, "周敏 correctly has role 高级工程师 in 继电所 - 保护研究室.")
        else:
            add_check("zhou_min_corrected", False,
                      f"周敏 wrong data: dept={zh_dept}, room={zh_room}, role={zhou.get('role')} (expected 高级工程师).")

    # Check 11: 赵宇 in 试验所 - 电气试验室, role 技术员
    zhao, z2_dept, z2_room, _ = find_member("赵宇")
    if zhao is None:
        add_check("zhao_yu_exists", False, "赵宇 not found.")
    else:
        z2_cd = z2_dept and "试验所" in z2_dept
        z2_cr = z2_room and "电气试验室" in z2_room
        if z2_cd and z2_cr and zhao.get("role") == "技术员":
            add_check("zhao_yu_exists", True, "赵宇 correctly added in 试验所 - 电气试验室 as 技术员.")
        else:
            add_check("zhao_yu_exists", False,
                      f"赵宇 wrong data: dept={z2_dept}, room={z2_room}, role={zhao.get('role')}.")

    # Check 12: 林建国 in 试验所 - 电气试验室, role 副主任
    lin, l_dept, l_room, _ = find_member("林建国")
    if lin is None:
        add_check("lin_jianguo_exists", False, "林建国 not found.")
    else:
        l_cd = l_dept and "试验所" in l_dept
        l_cr = l_room and "电气试验室" in l_room
        if l_cd and l_cr and lin.get("role") == "副主任":
            add_check("lin_jianguo_exists", True, "林建国 correctly added in 试验所 - 电气试验室 as 副主任.")
        else:
            add_check("lin_jianguo_exists", False,
                      f"林建国 wrong data: dept={l_dept}, room={l_room}, role={lin.get('role')}.")

    # Check 13: Office at room level for 保护研究室 is 806
    try:
        jidian_so = next((v for k, v in departments.items() if "继电所" in k), None)
        baohu_room = None
        if jidian_so:
            baohu_room = next((v for k, v in jidian_so.items() if "保护研究室" in k), None)
        if baohu_room and str(baohu_room.get("office", "")) == "806":
            add_check("baohu_room_office", True, "保护研究室 room-level office is 806.")
        else:
            office_val = baohu_room.get("office") if baohu_room else "ROOM NOT FOUND"
            add_check("baohu_room_office", False, f"保护研究室 office is '{office_val}', expected '806'.")
    except Exception as e:
        add_check("baohu_room_office", False, f"Error checking 保护研究室 office: {e}")

    # Check 14: Office at room level for 电气试验室 is 302
    try:
        shiyan_so = next((v for k, v in departments.items() if "试验所" in k), None)
        dianqi_room = None
        if shiyan_so:
            dianqi_room = next((v for k, v in shiyan_so.items() if "电气试验室" in k), None)
        if dianqi_room and str(dianqi_room.get("office", "")) == "302":
            add_check("dianqi_room_office", True, "电气试验室 room-level office is 302.")
        else:
            office_val = dianqi_room.get("office") if dianqi_room else "ROOM NOT FOUND"
            add_check("dianqi_room_office", False, f"电气试验室 office is '{office_val}', expected '302'.")
    except Exception as e:
        add_check("dianqi_room_office", False, f"Error checking 电气试验室 office: {e}")

    # Compute score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    overall_passed = all(c["passed"] for c in checks)

    return {"passed": overall_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))