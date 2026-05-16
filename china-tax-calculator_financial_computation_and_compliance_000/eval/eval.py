import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find and load the hr_tax_report.json file."""
    matches = list(Path(workspace).rglob("hr_tax_report.json"))
    if not matches:
        return None, "File hr_tax_report.json not found anywhere in workspace"
    return matches[0], None

def check_bonus_trap_detection(report):
    """
    Verify that bonus trap zones are correctly identified.
    Trap zones from SKILL.md:
    - 36,000: trap zone 36,001-37,000
    - 144,000: trap zone 144,001-154,000  
    - 300,000: trap zone 300,001-310,000
    
    E001: 36,001 -> IN TRAP (just above 36,000 threshold)
    E002: 144,500 -> IN TRAP (144,001-154,000 range)
    E003: 300,500 -> IN TRAP (300,001-310,000 range)
    E004: 60,000 -> SAFE (between 36,000 and 144,000, no trap)
    E005: 200,000 -> SAFE (between 144,000 and 300,000, no trap)
    E006: 96,000 -> SAFE (between 36,000 and 144,000, no trap)
    """
    checks = []
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        # Try top-level keys
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    
    if not employees:
        return [{"name": "bonus_trap_structure", "passed": False, 
                 "detail": f"Cannot find employee list in report. Top-level keys: {list(report.keys())}"}]
    
    # Find employees by ID or name
    def find_emp(id_val=None, name=None):
        for e in employees:
            if isinstance(e, dict):
                eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
                ename = str(e.get("姓名", e.get("name", "")))
                if id_val and id_val in eid:
                    return e
                if name and name in ename:
                    return e
        return None
    
    trap_employees = [
        ("E001", "陈晓明", 36001, True),
        ("E002", "王芳", 144500, True),
        ("E003", "刘建国", 300500, True),
        ("E004", "赵丽", 60000, False),
        ("E005", "孙伟", 200000, False),
    ]
    
    for eid, ename, bonus, should_be_trapped in trap_employees:
        emp = find_emp(eid) or find_emp(name=ename)
        if not emp:
            checks.append({"name": f"trap_detection_{eid}", "passed": False,
                           "detail": f"Employee {eid} ({ename}) not found in report"})
            continue
        
        # Check if trap is flagged - look for various field names
        trap_fields = ["年终奖陷阱", "bonus_trap", "trap_warning", "陷阱预警", "is_trap", 
                       "trap_detected", "bonus_warning", "in_trap_zone", "trap"]
        
        trap_value = None
        for field in trap_fields:
            if field in emp:
                trap_value = emp[field]
                break
        
        # Also check nested structures
        if trap_value is None:
            bonus_info = emp.get("年终奖信息", emp.get("bonus_info", emp.get("bonus", {})))
            if isinstance(bonus_info, dict):
                for field in trap_fields:
                    if field in bonus_info:
                        trap_value = bonus_info[field]
                        break
        
        if trap_value is None:
            # Check if there's a recommendation field that implies trap detection
            rec_fields = ["推荐金额", "recommended_bonus", "safe_amount", "建议金额", "优化建议"]
            for field in rec_fields:
                if field in emp:
                    # If there's a recommendation different from original, implies trap was detected
                    rec_val = emp[field]
                    if should_be_trapped and rec_val != bonus:
                        trap_value = True
                    break
        
        if trap_value is None:
            checks.append({"name": f"trap_detection_{eid}", "passed": not should_be_trapped,
                           "detail": f"No trap detection field found for {eid}. Employee data: {list(emp.keys())[:10]}"})
        else:
            # Normalize trap value
            is_trapped = bool(trap_value) if not isinstance(trap_value, str) else trap_value.lower() in ["true", "yes", "是", "警告", "危险"]
            passed = (is_trapped == should_be_trapped)
            checks.append({
                "name": f"trap_detection_{eid}",
                "passed": passed,
                "detail": f"Employee {eid} bonus={bonus}: expected trap={should_be_trapped}, got trap={is_trapped}"
            })
    
    return checks

def check_safe_bonus_recommendation(report):
    """
    For trapped employees, verify safe bonus recommendations are at or below the threshold.
    E001 (36001): recommended should be ≤36000
    E002 (144500): recommended should be ≤144000
    E003 (300500): recommended should be ≤300000
    """
    checks = []
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    if not employees:
        return [{"name": "safe_bonus_rec_structure", "passed": False,
                 "detail": "Cannot find employee list for safe bonus check"}]

    def find_emp(id_val=None, name=None):
        for e in employees:
            if isinstance(e, dict):
                eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
                ename = str(e.get("姓名", e.get("name", "")))
                if id_val and id_val in eid:
                    return e
                if name and name in ename:
                    return e
        return None

    trapped = [
        ("E001", "陈晓明", 36000),   # safe threshold
        ("E002", "王芳", 144000),
        ("E003", "刘建国", 300000),
    ]

    for eid, ename, safe_threshold in trapped:
        emp = find_emp(eid) or find_emp(name=ename)
        if not emp:
            checks.append({"name": f"safe_rec_{eid}", "passed": False,
                           "detail": f"Employee {eid} not found"})
            continue

        rec_fields = ["推荐金额", "recommended_bonus", "safe_amount", "建议金额", "安全金额",
                      "adjusted_bonus", "优化金额", "recommended_amount"]
        rec_val = None
        for field in rec_fields:
            if field in emp:
                try:
                    rec_val = float(str(emp[field]).replace(",", "").replace("元", "").replace("¥", ""))
                    break
                except:
                    pass
        
        # Also check nested
        if rec_val is None:
            bonus_info = emp.get("年终奖信息", emp.get("bonus_info", {}))
            if isinstance(bonus_info, dict):
                for field in rec_fields:
                    if field in bonus_info:
                        try:
                            rec_val = float(str(bonus_info[field]).replace(",", "").replace("元", "").replace("¥", ""))
                            break
                        except:
                            pass

        if rec_val is None:
            checks.append({"name": f"safe_rec_{eid}", "passed": False,
                           "detail": f"No safe bonus recommendation found for {eid}. Keys: {list(emp.keys())[:10]}"})
        else:
            passed = rec_val <= safe_threshold
            checks.append({
                "name": f"safe_rec_{eid}",
                "passed": passed,
                "detail": f"Employee {eid}: safe threshold={safe_threshold}, recommended={rec_val}. {'OK' if passed else 'FAIL: recommendation exceeds threshold'}"
            })
    
    return checks

def check_deductions_applied(report):
    """
    Verify that special deductions are correctly applied per SKILL.md 2025 standards:
    - E001 (已婚一孩+房贷+赡养独生子女): 子女教育2000 + 房贷1000 + 赡养3000 = 6000/month
    - E002 (单身租房): 租房扣除 800-1500/month (北京/上海/深圳/广州大城市1500)
    - E003 (已婚二孩+房贷): 子女教育2000*2=4000 + 房贷1000 = 5000/month
    - E004 (已婚无孩+房贷): 房贷1000/month
    - E005 (已婚一孩+房贷+赡养独生子女): 子女教育2000 + 房贷1000 + 赡养3000 = 6000/month
    - E006 (继续教育+单身租房): 继续教育400 + 租房扣除
    """
    checks = []
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    if not employees:
        return [{"name": "deductions_structure", "passed": False,
                 "detail": "Cannot find employee list for deduction check"}]

    def find_emp(id_val=None, name=None):
        for e in employees:
            if isinstance(e, dict):
                eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
                ename = str(e.get("姓名", e.get("name", "")))
                if id_val and id_val in eid:
                    return e
                if name and name in ename:
                    return e
        return None

    # Check E001: total monthly deduction should be >= 6000
    # (子女教育2000 + 房贷1000 + 赡养3000 = 6000)
    emp = find_emp("E001") or find_emp(name="陈晓明")
    if emp:
        ded_fields = ["月专项附加扣除", "monthly_deductions", "special_deductions", 
                      "专项附加扣除", "deductions", "monthly_special_deduction"]
        total_ded = None
        for field in ded_fields:
            if field in emp:
                try:
                    val = emp[field]
                    if isinstance(val, (int, float)):
                        total_ded = float(val)
                    elif isinstance(val, str):
                        total_ded = float(val.replace(",", "").replace("元", "").replace("¥", ""))
                    elif isinstance(val, dict):
                        total_ded = sum(float(str(v).replace(",","").replace("元","")) 
                                       for v in val.values() if str(v).replace(",","").replace("元","").replace(".","").isdigit())
                    break
                except:
                    pass
        
        if total_ded is not None:
            # E001 should have at least 6000 in deductions (child 2000 + mortgage 1000 + elderly 3000)
            passed = total_ded >= 6000
            checks.append({
                "name": "deduction_E001_married_one_child_mortgage_elderly",
                "passed": passed,
                "detail": f"E001 monthly special deductions: {total_ded}. Expected ≥6000 (child edu 2000 + mortgage 1000 + elderly care 3000)"
            })
        else:
            checks.append({
                "name": "deduction_E001_married_one_child_mortgage_elderly",
                "passed": False,
                "detail": f"Cannot find deduction amount for E001. Keys: {list(emp.keys())[:10]}"
            })
    else:
        checks.append({"name": "deduction_E001_not_found", "passed": False,
                       "detail": "E001 not found in report"})

    # Check E003: total monthly deduction should be >= 5000
    # (子女教育4000 [2 children x 2000] + 房贷1000 = 5000)
    emp3 = find_emp("E003") or find_emp(name="刘建国")
    if emp3:
        ded_fields = ["月专项附加扣除", "monthly_deductions", "special_deductions",
                      "专项附加扣除", "deductions", "monthly_special_deduction"]
        total_ded3 = None
        for field in ded_fields:
            if field in emp3:
                try:
                    val = emp3[field]
                    if isinstance(val, (int, float)):
                        total_ded3 = float(val)
                    elif isinstance(val, str):
                        total_ded3 = float(val.replace(",", "").replace("元", "").replace("¥", ""))
                    elif isinstance(val, dict):
                        total_ded3 = sum(float(str(v).replace(",","").replace("元",""))
                                        for v in val.values() if str(v).replace(",","").replace("元","").replace(".","").isdigit())
                    break
                except:
                    pass
        
        if total_ded3 is not None:
            # E003: two children (4000) + mortgage (1000) = 5000
            passed3 = total_ded3 >= 5000
            checks.append({
                "name": "deduction_E003_two_children_mortgage",
                "passed": passed3,
                "detail": f"E003 monthly special deductions: {total_ded3}. Expected ≥5000 (2 children edu 4000 + mortgage 1000)"
            })
        else:
            checks.append({
                "name": "deduction_E003_two_children_mortgage",
                "passed": False,
                "detail": f"Cannot find deduction for E003. Keys: {list(emp3.keys())[:10]}"
            })
    else:
        checks.append({"name": "deduction_E003_not_found", "passed": False,
                       "detail": "E003 not found"})
    
    return checks

def check_monthly_tax_calculation(report):
    """
    Verify monthly after-tax is computed using cumulative withholding method.
    Check E001: monthly salary 35000, social insurance 7000
    Taxable base per month (month 1) = 35000 - 7000 - 5000 (standard deduction) - 6000 (special deductions) = 17000
    Tax on 17000 = 17000*20% - 1410 = 3400 - 1410 = 1990 (month 1)
    After-tax ≈ 35000 - 7000 - 1990 = 26010
    
    We check that the after-tax monthly net for E001 is roughly in the right range (23000-28000)
    """
    checks = []
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    if not employees:
        return [{"name": "monthly_tax_structure", "passed": False,
                 "detail": "Cannot find employee list for monthly tax check"}]

    def find_emp(id_val=None, name=None):
        for e in employees:
            if isinstance(e, dict):
                eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
                ename = str(e.get("姓名", e.get("name", "")))
                if id_val and id_val in eid:
                    return e
                if name and name in ename:
                    return e
        return None

    emp = find_emp("E001") or find_emp(name="陈晓明")
    if not emp:
        return [{"name": "monthly_tax_E001", "passed": False, "detail": "E001 not found"}]

    net_fields = ["月净收入", "monthly_net", "after_tax_monthly", "月到手", "税后月薪",
                  "net_salary", "月税后", "monthly_after_tax", "after_tax"]
    net_val = None
    for field in net_fields:
        if field in emp:
            try:
                net_val = float(str(emp[field]).replace(",","").replace("元","").replace("¥",""))
                break
            except:
                pass

    if net_val is not None:
        # E001: gross 35000 - social 7000 = 28000 gross-of-tax
        # Taxable: 28000 - 5000 - 6000 = 17000
        # Tax rate 20% bracket: 17000*20% - 1410 = 1990
        # Net: 28000 - 1990 = 26010 (month 1 approximation)
        # Allow range 22000-28000 to account for different month calculations
        passed = 22000 <= net_val <= 28000
        checks.append({
            "name": "monthly_net_E001_reasonable_range",
            "passed": passed,
            "detail": f"E001 monthly net salary: {net_val}. Expected range [22000, 28000] (accounting for cumulative withholding)"
        })
    else:
        checks.append({
            "name": "monthly_net_E001_reasonable_range",
            "passed": False,
            "detail": f"No monthly net salary found for E001. Available keys: {list(emp.keys())[:15]}"
        })
    
    return checks

def check_bonus_tax_comparison(report):
    """
    Verify that the report includes comparison of single-taxation vs combined-taxation for year-end bonus.
    """
    checks = []
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    if not employees:
        return [{"name": "bonus_comparison_structure", "passed": False,
                 "detail": "Cannot find employee list for bonus comparison check"}]

    def find_emp(id_val=None, name=None):
        for e in employees:
            if isinstance(e, dict):
                eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
                ename = str(e.get("姓名", e.get("name", "")))
                if id_val and id_val in eid:
                    return e
                if name and name in ename:
                    return e
        return None

    # Check E004 or E005 - safe bonuses - for single vs combined comparison
    comparison_found = False
    for eid, ename in [("E004", "赵丽"), ("E005", "孙伟"), ("E006", "周明")]:
        emp = find_emp(eid) or find_emp(name=ename)
        if not emp:
            continue
        
        # Look for comparison fields
        comp_fields = ["单独计税", "合并计税", "single_tax", "combined_tax", 
                       "separate_taxation", "combined_taxation", "bonus_tax_comparison",
                       "年终奖计税方式", "optimal_method", "推荐计税方式"]
        for field in comp_fields:
            if field in emp:
                comparison_found = True
                break
        
        # Check nested
        if not comparison_found:
            for key in emp:
                val = emp[key]
                if isinstance(val, dict):
                    for field in comp_fields:
                        if field in val:
                            comparison_found = True
                            break
        
        if comparison_found:
            break

    checks.append({
        "name": "bonus_taxation_method_comparison",
        "passed": comparison_found,
        "detail": "Report includes single vs combined bonus taxation comparison" if comparison_found 
                  else "Report missing single vs combined bonus taxation comparison (单独计税 vs 合并计税)"
    })
    
    return checks

def check_all_employees_present(report):
    """Verify all 6 employees are present in the report."""
    employees = report.get("employees", report.get("员工列表", report.get("results", [])))
    if not employees:
        emp_keys = [k for k in report.keys() if isinstance(report[k], list)]
        if emp_keys:
            employees = report[emp_keys[0]]
    
    if not employees:
        return [{"name": "all_employees_present", "passed": False,
                 "detail": f"Cannot find employee list. Report keys: {list(report.keys())}"}]
    
    expected_ids = ["E001", "E002", "E003", "E004", "E005", "E006"]
    expected_names = ["陈晓明", "王芳", "刘建国", "赵丽", "孙伟", "周明"]
    
    found_count = 0
    for e in employees:
        if isinstance(e, dict):
            eid = str(e.get("员工ID", e.get("id", e.get("employee_id", ""))))
            ename = str(e.get("姓名", e.get("name", "")))
            for i, (exp_id, exp_name) in enumerate(zip(expected_ids, expected_names)):
                if exp_id in eid or exp_name in ename:
                    found_count += 1
                    break
    
    passed = found_count >= 5  # Allow missing 1 for partial credit
    return [{
        "name": "all_employees_present",
        "passed": passed,
        "detail": f"Found {found_count}/6 employees in report"
    }]

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # 1. Load the report
    report_path, err = load_report(workspace)
    if err:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": err}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    all_checks.append({"name": "file_exists", "passed": True, 
                       "detail": f"Found hr_tax_report.json at {report_path}"})
    
    # 2. Parse JSON
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        all_checks.append({"name": "valid_json", "passed": True, "detail": "JSON parsed successfully"})
    except Exception as e:
        all_checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    # 3. Run all checks
    try:
        all_checks.extend(check_all_employees_present(report))
    except Exception as e:
        all_checks.append({"name": "all_employees_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_bonus_trap_detection(report))
    except Exception as e:
        all_checks.append({"name": "trap_detection_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_safe_bonus_recommendation(report))
    except Exception as e:
        all_checks.append({"name": "safe_rec_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_deductions_applied(report))
    except Exception as e:
        all_checks.append({"name": "deductions_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_monthly_tax_calculation(report))
    except Exception as e:
        all_checks.append({"name": "monthly_tax_check_error", "passed": False, "detail": str(e)})
    
    try:
        all_checks.extend(check_bonus_tax_comparison(report))
    except Exception as e:
        all_checks.append({"name": "bonus_comparison_check_error", "passed": False, "detail": str(e)})
    
    # 4. Compute score
    passed_checks = [c for c in all_checks if c["passed"]]
    total = len(all_checks)
    score = len(passed_checks) / total if total > 0 else 0.0
    overall_passed = score >= 0.70
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()