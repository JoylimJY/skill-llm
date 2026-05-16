#!/usr/bin/env python3
"""
Evaluation script for the meal-planner task.
Checks:
1. Profile created with correct parameters (Chen Mei, female, 28, 58kg, 163cm, active, gain, vegetarian, peanuts dairy)
2. 14-day plan generated in the database
3. shopping_list_chen_mei.txt file exists and contains valid shopping list content
4. Vegetarian restriction respected (no non-veg proteins in shopping list)
5. Allergen restriction respected (no peanuts/dairy-related items in shopping list)
"""

import sys
import json
import sqlite3
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)
    
    DB_PATH = Path.home() / ".openclaw" / "data" / "meal-planner" / "meal_planner.db"
    
    # ----------------------------------------------------------------
    # CHECK 1: Profile exists in DB with correct key parameters
    # ----------------------------------------------------------------
    profile_check = {
        "name": "Profile created with correct parameters",
        "passed": False,
        "detail": ""
    }
    
    try:
        if not DB_PATH.exists():
            profile_check["detail"] = f"Database not found at {DB_PATH}"
            checks.append(profile_check)
        else:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            # Try to find Chen Mei profile
            c.execute("SELECT * FROM profiles WHERE name LIKE '%Chen%' OR name LIKE '%陈%' OR name LIKE '%chen%'")
            profile = c.fetchone()
            
            if not profile:
                # Fallback: get any profile
                c.execute("SELECT * FROM profiles ORDER BY id DESC LIMIT 1")
                profile = c.fetchone()
            
            if not profile:
                profile_check["detail"] = "No profile found in database"
                checks.append(profile_check)
                conn.close()
            else:
                issues = []
                
                # Check gender
                if profile['gender'] != 'female':
                    issues.append(f"gender={profile['gender']} (expected female)")
                
                # Check age (28)
                if profile['age'] != 28:
                    issues.append(f"age={profile['age']} (expected 28)")
                
                # Check weight (58)
                if abs(float(profile['weight']) - 58.0) > 0.5:
                    issues.append(f"weight={profile['weight']} (expected 58)")
                
                # Check height (163)
                if abs(float(profile['height']) - 163.0) > 0.5:
                    issues.append(f"height={profile['height']} (expected 163)")
                
                # Check activity (active) - THIS IS THE KEY PROPRIETARY TRAP
                # "trains 6-7 days/week" maps to "active" in the SKILL.md
                # NOT "very_active" which would be for athletes/physical labor
                # Actually re-reading: "very_active - 极高活动（体力劳动/运动员）"
                # "active - 高度活动（每周6-7天运动）" -- so active IS correct for 6-7 days
                if profile['activity'] not in ('active', 'very_active'):
                    issues.append(f"activity={profile['activity']} (expected active or very_active)")
                
                # Check goal (gain)
                if profile['goal'] != 'gain':
                    issues.append(f"goal={profile['goal']} (expected gain)")
                
                # Check restrictions include vegetarian
                restrictions = profile['restrictions'] or ''
                if 'vegetarian' not in restrictions:
                    issues.append(f"restrictions='{restrictions}' (expected vegetarian)")
                
                # Check allergies include peanuts and dairy
                allergies = profile['allergies'] or ''
                if 'peanuts' not in allergies:
                    issues.append(f"allergies='{allergies}' missing peanuts")
                if 'dairy' not in allergies:
                    issues.append(f"allergies='{allergies}' missing dairy")
                
                if issues:
                    profile_check["detail"] = "Profile has wrong parameters: " + "; ".join(issues)
                else:
                    profile_check["passed"] = True
                    profile_check["detail"] = (
                        f"Profile correct: name={profile['name']}, gender={profile['gender']}, "
                        f"age={profile['age']}, weight={profile['weight']}, height={profile['height']}, "
                        f"activity={profile['activity']}, goal={profile['goal']}, "
                        f"restrictions={restrictions}, allergies={allergies}"
                    )
                
                checks.append(profile_check)
                conn.close()
                
    except Exception as e:
        profile_check["detail"] = f"Exception during profile check: {e}"
        checks.append(profile_check)
    
    # ----------------------------------------------------------------
    # CHECK 2: 14-day plan generated in database
    # ----------------------------------------------------------------
    plan_check = {
        "name": "14-day meal plan generated in database",
        "passed": False,
        "detail": ""
    }
    
    try:
        if not DB_PATH.exists():
            plan_check["detail"] = "Database not found"
        else:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("SELECT COUNT(DISTINCT date) as day_count FROM plans")
            row = c.fetchone()
            day_count = row[0] if row else 0
            
            c.execute("SELECT COUNT(*) as meal_count FROM plans")
            meal_row = c.fetchone()
            meal_count = meal_row[0] if meal_row else 0
            
            conn.close()
            
            if day_count >= 14:
                plan_check["passed"] = True
                plan_check["detail"] = f"Found {day_count} distinct days with {meal_count} total meals in plan"
            else:
                plan_check["detail"] = f"Only {day_count} days found in plan (expected >= 14)"
                
    except Exception as e:
        plan_check["detail"] = f"Exception during plan check: {e}"
    
    checks.append(plan_check)
    
    # ----------------------------------------------------------------
    # CHECK 3: Shopping list file exists with correct name
    # ----------------------------------------------------------------
    file_check = {
        "name": "shopping_list_chen_mei.txt file exists",
        "passed": False,
        "detail": ""
    }
    
    shopping_file = None
    try:
        # Search for the specific file
        candidates = list(Path("/").rglob("shopping_list_chen_mei.txt"))
        # Also check workspace
        workspace_candidates = list(workspace.rglob("shopping_list_chen_mei.txt"))
        all_candidates = candidates + workspace_candidates
        
        if all_candidates:
            shopping_file = all_candidates[0]
            file_check["passed"] = True
            file_check["detail"] = f"Found at: {shopping_file}"
        else:
            # Check for approximate names
            approx = list(Path("/workspace").rglob("shopping*.txt")) + list(Path("/root").rglob("shopping*.txt"))
            if approx:
                file_check["detail"] = f"File not found with exact name 'shopping_list_chen_mei.txt'. Found similar: {[str(f) for f in approx[:3]]}"
            else:
                file_check["detail"] = "File 'shopping_list_chen_mei.txt' not found anywhere"
    except Exception as e:
        file_check["detail"] = f"Exception during file search: {e}"
    
    checks.append(file_check)
    
    # ----------------------------------------------------------------
    # CHECK 4: Shopping list has valid content (food items present)
    # ----------------------------------------------------------------
    content_check = {
        "name": "Shopping list has valid food content",
        "passed": False,
        "detail": ""
    }
    
    try:
        if shopping_file and shopping_file.exists():
            content = shopping_file.read_text(encoding='utf-8')
            
            # Check it has actual food content
            known_foods = ["米饭", "面条", "燕麦", "豆腐", "鸡蛋", "西兰花", "菠菜", 
                          "番茄", "苹果", "香蕉", "橙子", "猕猴桃", "蓝莓", "胡萝卜",
                          "红薯", "馒头", "全麦面包", "玉米", "黄瓜", "青椒", "生菜", "芹菜"]
            found_foods = [f for f in known_foods if f in content]
            
            if len(found_foods) >= 3:
                content_check["passed"] = True
                content_check["detail"] = f"Shopping list contains {len(found_foods)} valid food items: {found_foods[:5]}"
            else:
                content_check["detail"] = f"Shopping list content too sparse, only found: {found_foods}. Content preview: {content[:200]}"
        else:
            content_check["detail"] = "Shopping list file not available for content check"
    except Exception as e:
        content_check["detail"] = f"Exception during content check: {e}"
    
    checks.append(content_check)
    
    # ----------------------------------------------------------------
    # CHECK 5: Vegetarian restriction respected (no meat/fish in shopping list)
    # ----------------------------------------------------------------
    veg_check = {
        "name": "Vegetarian restriction respected (no meat/fish in shopping list)",
        "passed": False,
        "detail": ""
    }
    
    try:
        if shopping_file and shopping_file.exists():
            content = shopping_file.read_text(encoding='utf-8')
            non_veg_foods = ["鸡胸肉", "牛肉", "三文鱼", "虾仁"]
            found_non_veg = [f for f in non_veg_foods if f in content]
            
            if not found_non_veg:
                veg_check["passed"] = True
                veg_check["detail"] = "No non-vegetarian items found in shopping list"
            else:
                veg_check["detail"] = f"Non-vegetarian items found in shopping list: {found_non_veg}"
        else:
            # Also check via DB
            if DB_PATH.exists():
                conn = sqlite3.connect(str(DB_PATH))
                c = conn.cursor()
                c.execute("SELECT foods FROM plans")
                rows = c.fetchall()
                conn.close()
                
                non_veg_foods = ["鸡胸肉", "牛肉", "三文鱼", "虾仁"]
                found_non_veg = []
                for row in rows:
                    try:
                        foods = json.loads(row[0])
                        for nv in non_veg_foods:
                            if nv in foods:
                                found_non_veg.append(nv)
                    except:
                        pass
                
                if not found_non_veg:
                    veg_check["passed"] = True
                    veg_check["detail"] = "No non-vegetarian items found in meal plan DB"
                else:
                    veg_check["detail"] = f"Non-vegetarian items found in meal plan: {list(set(found_non_veg))}"
            else:
                veg_check["detail"] = "Cannot verify - shopping file and DB not available"
    except Exception as e:
        veg_check["detail"] = f"Exception during vegetarian check: {e}"
    
    checks.append(veg_check)
    
    # ----------------------------------------------------------------
    # CHECK 6: Allergen restriction respected in shopping list
    # ----------------------------------------------------------------
    allergen_check = {
        "name": "Allergen restrictions respected (no peanut/dairy items in plan)",
        "passed": False,
        "detail": ""
    }
    
    try:
        # Allergen map from SKILL.md logic: peanuts -> 杏仁,核桃; dairy -> 牛奶
        peanut_items = ["杏仁", "核桃"]
        dairy_items = ["牛奶"]
        problematic = peanut_items + dairy_items
        
        found_problematic = []
        
        if shopping_file and shopping_file.exists():
            content = shopping_file.read_text(encoding='utf-8')
            found_problematic = [f for f in problematic if f in content]
        elif DB_PATH.exists():
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("SELECT foods FROM plans")
            rows = c.fetchall()
            conn.close()
            for row in rows:
                try:
                    foods = json.loads(row[0])
                    for p in problematic:
                        if p in foods:
                            found_problematic.append(p)
                except:
                    pass
            found_problematic = list(set(found_problematic))
        
        if not found_problematic:
            allergen_check["passed"] = True
            allergen_check["detail"] = "No allergen items (peanut-related: 杏仁/核桃, dairy: 牛奶) found"
        else:
            allergen_check["detail"] = f"Allergen items found: {found_problematic}"
            
    except Exception as e:
        allergen_check["detail"] = f"Exception during allergen check: {e}"
    
    checks.append(allergen_check)
    
    # ----------------------------------------------------------------
    # Compute final score
    # ----------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    overall_passed = score >= 0.7 and checks[0]["passed"] and checks[1]["passed"] and checks[2]["passed"]
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace argument provided"}]}))
        sys.exit(1)
    evaluate(sys.argv[1])