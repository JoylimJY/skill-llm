import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # =========================================================
    # CHECK 1: ~/.family-chef-profile.json exists
    # =========================================================
    profile_path = Path.home() / ".family-chef-profile.json"
    profile, err = load_json_safe(profile_path)

    check1 = {"name": "profile_file_exists", "passed": False, "detail": ""}
    if profile is None:
        check1["detail"] = err or "Profile file missing at ~/.family-chef-profile.json"
    else:
        check1["passed"] = True
        check1["detail"] = f"Profile found at {profile_path}"
    checks.append(check1)

    # =========================================================
    # CHECK 2: Profile has ALL required keys including Chinese key 忌口
    # Required keys per SKILL.md: family_size, budget, city, preferences, 忌口
    # =========================================================
    check2 = {"name": "profile_has_correct_keys_including_chinese_key", "passed": False, "detail": ""}
    if profile is not None:
        required_keys = {"family_size", "budget", "city", "preferences", "忌口"}
        present_keys = set(profile.keys())
        missing = required_keys - present_keys
        if missing:
            check2["detail"] = f"Missing required keys: {missing}. Found keys: {present_keys}"
        else:
            check2["passed"] = True
            check2["detail"] = f"All required keys present including '忌口'. Keys: {present_keys}"
    else:
        check2["detail"] = "Cannot check keys - profile file missing or invalid"
    checks.append(check2)

    # =========================================================
    # CHECK 3: Profile values are non-empty and family_size/budget are present as strings or numbers
    # =========================================================
    check3 = {"name": "profile_values_populated", "passed": False, "detail": ""}
    if profile is not None and check2["passed"]:
        try:
            fs = profile.get("family_size", "")
            budget = profile.get("budget", "")
            city = profile.get("city", "")
            prefs = profile.get("preferences", "")
            jk = profile.get("忌口", "")

            issues = []
            if not str(fs).strip():
                issues.append("family_size is empty")
            if not str(budget).strip():
                issues.append("budget is empty")
            if not str(city).strip():
                issues.append("city is empty")
            # preferences and 忌口 can be empty (optional), but should be present as strings

            if issues:
                check3["detail"] = f"Profile has empty required fields: {issues}"
            else:
                check3["passed"] = True
                check3["detail"] = f"family_size={fs}, budget={budget}, city={city}, preferences={prefs}, 忌口={jk}"
        except Exception as e:
            check3["detail"] = f"Error checking profile values: {e}"
    else:
        check3["detail"] = "Skipped - profile missing or keys check failed"
    checks.append(check3)

    # =========================================================
    # CHECK 4: weekly_meal_plan.json exists in workspace
    # =========================================================
    plan_candidates = list(workspace.rglob("weekly_meal_plan.json"))
    # Also check workspace root directly
    plan_path = workspace / "weekly_meal_plan.json"
    if plan_path not in plan_candidates:
        plan_candidates.insert(0, plan_path)

    check4 = {"name": "weekly_meal_plan_file_exists", "passed": False, "detail": ""}
    plan = None
    plan_err = None
    used_plan_path = None

    for candidate in plan_candidates:
        p, e = load_json_safe(candidate)
        if p is not None:
            # Must not be the incomplete distractor (has "note" key with "incomplete draft")
            if isinstance(p, dict) and "note" in p and "incomplete" in str(p.get("note", "")).lower():
                continue
            plan = p
            used_plan_path = candidate
            break

    if plan is None:
        # Try workspace root even if it's the distractor - check if it was overwritten
        root_plan, root_err = load_json_safe(plan_path)
        if root_plan is not None:
            if not (isinstance(root_plan, dict) and "note" in root_plan and "incomplete" in str(root_plan.get("note","")).lower()):
                plan = root_plan
                used_plan_path = plan_path
            else:
                check4["detail"] = "Found only the original incomplete distractor file - agent did not overwrite it"
        else:
            check4["detail"] = root_err or "weekly_meal_plan.json not found in workspace"
    
    if plan is not None:
        check4["passed"] = True
        check4["detail"] = f"weekly_meal_plan.json found at {used_plan_path}"
    checks.append(check4)

    # =========================================================
    # CHECK 5: Menu plan contains 7 days of meals
    # The plan must have some structure representing 7 days
    # =========================================================
    check5 = {"name": "menu_has_7_days", "passed": False, "detail": ""}
    if plan is not None:
        try:
            day_count = 0
            day_data = None

            # Try common structures:
            # {"menu": {"周一": ..., "周二": ...}}
            # {"weekly_menu": [...]} with 7 items
            # {"days": [...]} with 7 items
            # {"周一": ..., "周二": ...} flat structure

            chinese_days = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            day_aliases = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
                          "day1", "day2", "day3", "day4", "day5", "day6", "day7",
                          "第一天", "第二天", "第三天", "第四天", "第五天", "第六天", "第七天"]

            def count_days_in_dict(d):
                if not isinstance(d, dict):
                    return 0
                count = 0
                for key in d.keys():
                    if key in chinese_days:
                        count += 1
                    elif key.lower() in day_aliases:
                        count += 1
                return count

            def count_days_in_list(lst):
                if isinstance(lst, list):
                    return len(lst)
                return 0

            # Search recursively for day structures
            def find_max_days(obj, depth=0):
                if depth > 5:
                    return 0
                if isinstance(obj, dict):
                    d = count_days_in_dict(obj)
                    if d >= 5:
                        return d
                    return max((find_max_days(v, depth+1) for v in obj.values()), default=0)
                elif isinstance(obj, list):
                    c = count_days_in_list(obj)
                    if c >= 5:
                        return c
                    return max((find_max_days(item, depth+1) for item in obj), default=0)
                return 0

            day_count = find_max_days(plan)

            if day_count >= 7:
                check5["passed"] = True
                check5["detail"] = f"Found {day_count} days in meal plan"
            elif day_count >= 5:
                # Partial credit check - at least 5 days
                check5["passed"] = False
                check5["detail"] = f"Only {day_count} days found, expected 7. Plan keys: {list(plan.keys()) if isinstance(plan, dict) else type(plan)}"
            else:
                check5["detail"] = f"Could not find 7-day structure. Day count: {day_count}. Top-level keys: {list(plan.keys()) if isinstance(plan, dict) else str(plan)[:200]}"
        except Exception as e:
            check5["detail"] = f"Error parsing menu days: {e}"
    else:
        check5["detail"] = "Skipped - meal plan file missing"
    checks.append(check5)

    # =========================================================
    # CHECK 6: Menu includes autumn seasonal vegetables (October = autumn)
    # Autumn vegetables per SKILL.md: 萝卜, 胡萝卜, 红薯, 土豆, 莲藕, 大白菜, 香菇, 木耳, 金针菇, 南瓜, 冬瓜, 丝瓜, 菠菜, 茼蒿
    # =========================================================
    check6 = {"name": "menu_includes_autumn_seasonal_vegetables", "passed": False, "detail": ""}
    autumn_vegetables = [
        "大白菜", "萝卜", "胡萝卜", "红薯", "土豆", "莲藕", "南瓜", "冬瓜", "丝瓜",
        "香菇", "木耳", "金针菇", "菠菜", "茼蒿", "萝卜缨"
    ]

    if plan is not None:
        try:
            plan_str = json.dumps(plan, ensure_ascii=False)
            found_veggies = [v for v in autumn_vegetables if v in plan_str]

            if len(found_veggies) >= 3:
                check6["passed"] = True
                check6["detail"] = f"Found {len(found_veggies)} autumn vegetables in menu: {found_veggies}"
            else:
                check6["detail"] = f"Only found {len(found_veggies)} autumn vegetables ({found_veggies}), expected at least 3 from: {autumn_vegetables}"
        except Exception as e:
            check6["detail"] = f"Error checking seasonal vegetables: {e}"
    else:
        check6["detail"] = "Skipped - meal plan file missing"
    checks.append(check6)

    # =========================================================
    # CHECK 7: Nutrition data uses SKILL.md values (not generic/USDA values)
    # Key test: 鸡蛋 should be 70 kcal/100g (skill) NOT ~155 kcal (USDA)
    # 鸡胸肉 should be 165 kcal/100g (skill) NOT ~120 kcal
    # 米饭 should be 116 kcal/100g (skill) NOT ~130 kcal
    # We look for these specific values in the nutrition section of the plan
    # =========================================================
    check7 = {"name": "nutrition_uses_skill_table_values_not_generic", "passed": False, "detail": ""}

    SKILL_NUTRITION = {
        "鸡蛋": 70,
        "鸡胸肉": 165,
        "猪肉": 143,
        "牛肉": 250,
        "米饭": 116,
        "豆腐": 76,
        "西红柿": 18,
        "菠菜": 23,
    }

    # Wrong values commonly found in general training data / USDA
    WRONG_VALUES = {
        "鸡蛋": [155, 147, 143, 148, 150, 152, 153],  # USDA whole egg ~155
        "鸡胸肉": [120, 110, 105, 100, 115],
        "米饭": [130, 128, 135, 140],
    }

    if plan is not None:
        try:
            plan_str = json.dumps(plan, ensure_ascii=False)

            # Check for presence of correct skill values
            skill_values_found = []
            wrong_values_found = []

            for food, skill_cal in SKILL_NUTRITION.items():
                if str(skill_cal) in plan_str and food in plan_str:
                    skill_values_found.append(f"{food}={skill_cal}")

            for food, wrong_list in WRONG_VALUES.items():
                for wrong_val in wrong_list:
                    if str(wrong_val) in plan_str and food in plan_str:
                        wrong_values_found.append(f"{food}={wrong_val}(wrong,skill={SKILL_NUTRITION[food]})")

            if len(skill_values_found) >= 2:
                check7["passed"] = True
                check7["detail"] = f"Correct skill nutrition values found: {skill_values_found}. Wrong values: {wrong_values_found if wrong_values_found else 'none'}"
            elif plan_str.count("热量") > 0 or plan_str.count("卡路里") > 0 or plan_str.count("kcal") > 0 or plan_str.count("营养") > 0:
                # Nutrition section exists but values not explicitly matching
                check7["passed"] = False
                check7["detail"] = f"Nutrition section present but skill-specific values not confirmed. Skill values found: {skill_values_found}. Consider: 鸡蛋=70kcal, 鸡胸肉=165kcal per SKILL.md"
            else:
                check7["detail"] = f"No nutrition calculation found in plan. Skill values found: {skill_values_found}"
        except Exception as e:
            check7["detail"] = f"Error checking nutrition values: {e}"
    else:
        check7["detail"] = "Skipped - meal plan file missing"
    checks.append(check7)

    # =========================================================
    # CHECK 8: Shopping list is present and non-trivial
    # =========================================================
    check8 = {"name": "shopping_list_present_and_non_trivial", "passed": False, "detail": ""}

    if plan is not None:
        try:
            plan_str = json.dumps(plan, ensure_ascii=False)

            # Shopping list keywords in Chinese
            shopping_keywords = ["购物清单", "采购清单", "购物", "shopping", "清单", "所需食材", "需要购买"]
            has_shopping_section = any(kw in plan_str for kw in shopping_keywords)

            # Check for at least 5 ingredients in shopping list area
            common_ingredients = [
                "猪肉", "鸡肉", "鸡蛋", "牛肉", "豆腐", "米", "面",
                "白菜", "萝卜", "土豆", "胡萝卜", "香菇", "西红柿", "黄瓜",
                "南瓜", "菠菜", "茄子", "青椒", "葱", "姜", "蒜"
            ]
            found_ingredients = [ing for ing in common_ingredients if ing in plan_str]

            if has_shopping_section and len(found_ingredients) >= 5:
                check8["passed"] = True
                check8["detail"] = f"Shopping list found with {len(found_ingredients)} recognizable ingredients: {found_ingredients[:10]}"
            elif len(found_ingredients) >= 8:
                # Even without explicit "购物清单" label, if many ingredients listed, give credit
                check8["passed"] = True
                check8["detail"] = f"Ingredient list found (implicit shopping list) with {len(found_ingredients)} items: {found_ingredients}"
            else:
                check8["detail"] = f"Shopping list section missing or insufficient. Has shopping keyword: {has_shopping_section}. Found {len(found_ingredients)} ingredients: {found_ingredients}"
        except Exception as e:
            check8["detail"] = f"Error checking shopping list: {e}"
    else:
        check8["detail"] = "Skipped - meal plan file missing"
    checks.append(check8)

    # =========================================================
    # SCORING
    # =========================================================
    # Weights:
    # Check 1: profile exists (essential) - weight 1
    # Check 2: correct keys including 忌口 (THE proprietary trap) - weight 2
    # Check 3: profile values populated - weight 1
    # Check 4: plan file exists - weight 1
    # Check 5: 7-day menu - weight 2
    # Check 6: autumn vegetables - weight 2
    # Check 7: correct nutrition values - weight 2
    # Check 8: shopping list - weight 1

    weights = [1, 2, 1, 1, 2, 2, 2, 1]
    total_weight = sum(weights)
    earned_weight = sum(w for c, w in zip(checks, weights) if c["passed"])

    score = round(earned_weight / total_weight, 3)

    # Overall pass: must pass checks 1,2,4,5,6 at minimum (the core workflow)
    core_checks = [checks[0], checks[1], checks[3], checks[4], checks[5]]
    passed = all(c["passed"] for c in core_checks)

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))