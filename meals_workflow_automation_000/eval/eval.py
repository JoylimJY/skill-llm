import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    home = Path("/root")
    meals_root = home / "meals"

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # --- CHECK 1: Core directory structure ---
    required_dirs = [
        meals_root / "plans",
        meals_root / "meals",
        meals_root / "shopping",
    ]
    all_dirs_exist = all(d.exists() and d.is_dir() for d in required_dirs)
    add_check(
        "core_directory_structure",
        all_dirs_exist,
        f"Required dirs: {[str(d) for d in required_dirs]}. Exist: {[d.exists() for d in required_dirs]}"
    )

    # --- CHECK 2: preferences.md exists with dietary info ---
    prefs_file = meals_root / "preferences.md"
    prefs_ok = False
    prefs_detail = "preferences.md not found"
    if prefs_file.exists():
        prefs_content = prefs_file.read_text().lower()
        has_dairy_free = "dairy" in prefs_content
        has_no_mushrooms = "mushroom" in prefs_content
        has_vegetarian = "vegetarian" in prefs_content
        prefs_ok = has_dairy_free and has_no_mushrooms
        prefs_detail = (
            f"dairy mention: {has_dairy_free}, mushroom mention: {has_no_mushrooms}, "
            f"vegetarian mention: {has_vegetarian}"
        )
    add_check("preferences_file_with_dietary_info", prefs_ok, prefs_detail)

    # --- CHECK 3: Meal files exist ---
    meal_files = list((meals_root / "meals").glob("*.md")) if (meals_root / "meals").exists() else []
    meal_names_found = [f.stem for f in meal_files]
    
    # Check for all 4 required meals (flexible naming)
    required_meal_keywords = [
        ["chicken", "stir"],
        ["lentil", "soup"],
        ["salmon"],
        ["black", "bean", "taco"],
    ]
    
    meals_found = []
    for keywords in required_meal_keywords:
        found = any(
            all(kw in name.lower() for kw in keywords)
            for name in meal_names_found
        )
        meals_found.append(found)
    
    all_meals_present = all(meals_found)
    add_check(
        "all_four_meal_files_exist",
        all_meals_present,
        f"Meal files found: {meal_names_found}. Required meal patterns matched: {meals_found}"
    )

    # --- CHECK 4: Meal files have required fields ---
    required_fields = ["prep", "cook", "serves", "ingredient"]
    meal_files_valid = 0
    meal_field_details = []
    
    for mf in meal_files:
        try:
            content = mf.read_text().lower()
            fields_present = [f in content for f in required_fields]
            if all(fields_present):
                meal_files_valid += 1
            meal_field_details.append(f"{mf.name}: {dict(zip(required_fields, fields_present))}")
        except Exception as e:
            meal_field_details.append(f"{mf.name}: ERROR {e}")
    
    meals_with_fields_ok = meal_files_valid >= 4
    add_check(
        "meal_files_have_required_fields",
        meals_with_fields_ok,
        f"Meals with all required fields: {meal_files_valid}/4. Details: {meal_field_details}"
    )

    # --- CHECK 5: Dietary tags in meal files ---
    tag_checks = []
    tag_detail = []
    for mf in meal_files:
        try:
            content = mf.read_text().lower()
            name = mf.stem.lower()
            # Check dairy-free tag in appropriate meals
            if "salmon" in name or "stir" in name or "lentil" in name or "black" in name or "taco" in name:
                has_dairy_free_tag = "dairy-free" in content or "dairy free" in content
                tag_checks.append(has_dairy_free_tag)
                tag_detail.append(f"{mf.name} dairy-free tag: {has_dairy_free_tag}")
        except Exception as e:
            tag_detail.append(f"ERROR: {e}")
    
    tags_ok = len(tag_checks) > 0 and sum(tag_checks) >= 3
    add_check(
        "dietary_tags_in_meal_files",
        tags_ok,
        f"Dairy-free tag checks: {tag_detail}"
    )

    # --- CHECK 6: Difficulty/time tags in meal files ---
    time_tag_keywords = ["quick", "under 30", "one-pot", "sheet pan", "make ahead", "freezer", "weeknight"]
    time_tag_hits = 0
    time_tag_detail = []
    for mf in meal_files:
        try:
            content = mf.read_text().lower()
            has_time_tag = any(kw in content for kw in time_tag_keywords)
            time_tag_hits += int(has_time_tag)
            time_tag_detail.append(f"{mf.name}: {has_time_tag}")
        except Exception as e:
            time_tag_detail.append(f"ERROR: {e}")
    
    time_tags_ok = time_tag_hits >= 3
    add_check(
        "time_difficulty_tags_in_meals",
        time_tags_ok,
        f"Meals with time/difficulty tags: {time_tag_hits}/4. Details: {time_tag_detail}"
    )

    # --- CHECK 7: Weekly plan file exists with correct path ---
    plan_files = list((meals_root / "plans").glob("*.md")) if (meals_root / "plans").exists() else []
    week11_plan = None
    for pf in plan_files:
        if "week-11" in pf.name or "week11" in pf.name or "2024" in pf.name:
            week11_plan = pf
            break
    # Also try exact path
    exact_plan = meals_root / "plans" / "2024-week-11.md"
    if exact_plan.exists():
        week11_plan = exact_plan

    plan_exists = week11_plan is not None
    add_check(
        "weekly_plan_file_exists",
        plan_exists,
        f"Plan files found: {[p.name for p in plan_files]}. Week-11 plan: {week11_plan}"
    )

    # --- CHECK 8: Weekly plan content correctness ---
    plan_content_ok = False
    plan_content_detail = "Plan file not found"
    if week11_plan and week11_plan.exists():
        try:
            plan_text = week11_plan.read_text().lower()
            checks_map = {
                "sunday_lentil": any(kw in plan_text for kw in ["lentil", "batch"]),
                "monday_leftovers": "leftover" in plan_text or "monday" in plan_text and "lentil" in plan_text,
                "tuesday_blackbean_or_veg": any(kw in plan_text for kw in ["black bean", "taco", "vegetarian"]),
                "wednesday_stirfry_or_quick": any(kw in plan_text for kw in ["stir", "chicken", "quick"]),
                "thursday_salmon": "salmon" in plan_text,
                "friday_takeout_or_busy": any(kw in plan_text for kw in ["takeout", "take out", "busy"]),
            }
            passed_count = sum(checks_map.values())
            plan_content_ok = passed_count >= 5
            plan_content_detail = f"Day checks: {checks_map}, passed: {passed_count}/6"
        except Exception as e:
            plan_content_detail = f"Error reading plan: {e}"
    add_check("weekly_plan_content_correct", plan_content_ok, plan_content_detail)

    # --- CHECK 9: Shopping list file exists with correct name ---
    shopping_dir = meals_root / "shopping"
    shopping_file = None
    shopping_name_ok = False
    
    if shopping_dir.exists():
        shopping_files = list(shopping_dir.glob("*.md"))
        for sf in shopping_files:
            if "week-11" in sf.name or "week11" in sf.name or "shopping" in sf.name:
                shopping_file = sf
                break
        # Try exact name
        exact_shopping = shopping_dir / "week-11-shopping.md"
        if exact_shopping.exists():
            shopping_file = exact_shopping
            shopping_name_ok = True
        elif shopping_file:
            shopping_name_ok = True  # any reasonable match
    
    add_check(
        "shopping_list_file_exists",
        shopping_file is not None and shopping_name_ok,
        f"Shopping files in dir: {[f.name for f in (shopping_dir.glob('*.md') if shopping_dir.exists() else [])]}. Found: {shopping_file}"
    )

    # --- CHECK 10: Shopping list grouped by store section ---
    shopping_grouped_ok = False
    shopping_grouped_detail = "Shopping file not found"
    if shopping_file and shopping_file.exists():
        try:
            shop_text = shopping_file.read_text().lower()
            section_keywords = {
                "produce": ["produce", "vegetable", "fruit", "fresh"],
                "meat_fish": ["meat", "fish", "protein", "seafood", "poultry"],
                "pantry": ["pantry", "dry", "canned", "staple"],
            }
            sections_found = {}
            for section, keywords in section_keywords.items():
                sections_found[section] = any(kw in shop_text for kw in keywords)
            
            grouped_count = sum(sections_found.values())
            shopping_grouped_ok = grouped_count >= 2
            shopping_grouped_detail = f"Sections found: {sections_found}"
        except Exception as e:
            shopping_grouped_detail = f"Error: {e}"
    add_check("shopping_list_grouped_by_section", shopping_grouped_ok, shopping_grouped_detail)

    # --- CHECK 11: Pantry staples EXCLUDED from shopping list ---
    pantry_staples_excluded = False
    pantry_exclusion_detail = "Shopping file not found"
    if shopping_file and shopping_file.exists():
        try:
            shop_text = shopping_file.read_text().lower()
            # These should NOT appear as line items in the shopping list
            # (they may appear in section headers or notes, but not as standalone items to buy)
            always_have = ["olive oil", "garlic", "cumin", "smoked paprika", "turmeric", 
                           "paprika", "soy sauce", "sesame oil", "cornstarch", "vegetable oil", "ginger"]
            
            lines = shop_text.split('\n')
            # Look for lines that are shopping items (start with -, *, bullet, or are short ingredient lines)
            item_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('-', '*', '•', '–')) or (len(stripped) > 0 and len(stripped) < 60 and not stripped.startswith('#')):
                    item_lines.append(stripped)
            
            item_text = ' '.join(item_lines)
            
            # Check that key pantry items are NOT in the shopping list as items to buy
            # We check the most distinct ones
            key_pantry = ["olive oil", "soy sauce", "sesame oil", "cumin", "turmeric"]
            found_pantry_in_list = [kp for kp in key_pantry if kp in item_text]
            
            # Also verify actual ingredients ARE present (chicken, lentils, salmon, etc.)
            actual_ingredients = ["chicken", "lentil", "salmon", "black bean", "avocado", "bell pepper", "broccoli"]
            found_actual = [ai for ai in actual_ingredients if ai in shop_text]
            
            pantry_staples_excluded = len(found_pantry_in_list) <= 1 and len(found_actual) >= 4
            pantry_exclusion_detail = (
                f"Pantry items found in shopping list: {found_pantry_in_list} (should be 0-1). "
                f"Actual ingredients found: {found_actual} (should be 4+)"
            )
        except Exception as e:
            pantry_exclusion_detail = f"Error: {e}"
    add_check("pantry_staples_excluded_from_shopping", pantry_staples_excluded, pantry_exclusion_detail)

    # --- CHECK 12: Quantities combined / aggregated correctly ---
    # Olive oil appears in multiple recipes (lentil soup: 2 tbsp, salmon: 3 tbsp, stir-fry: 2 tbsp)
    # Since olive oil is a pantry staple, it won't be in the list.
    # But onion appears in lentil soup (1 onion) and black bean tacos via red onion (1) → should show combined
    # Lemon appears in salmon (1) and lentil soup (2 tbsp juice) — might be combined or listed once
    # We check that the shopping list doesn't just list each meal's ingredients separately (no duplicate entries)
    quantity_combined_ok = False
    quantity_detail = "Shopping file not found"
    if shopping_file and shopping_file.exists():
        try:
            shop_text = shopping_file.read_text().lower()
            lines = [l.strip() for l in shop_text.split('\n') if l.strip()]
            
            # Count distinct onion references — should be combined, not listed twice
            onion_lines = [l for l in lines if 'onion' in l]
            # If there are multiple onion lines, they might be different (red onion vs regular), that's ok
            # But if "onion" appears 3+ times as separate items, that suggests no aggregation
            
            # More importantly: check that we don't see the same ingredient repeated as separate bullet points
            ingredient_counts = {}
            for line in lines:
                if line.startswith(('-', '*', '•')):
                    # Extract ingredient name (rough)
                    cleaned = re.sub(r'^[-*•]\s*', '', line)
                    cleaned = re.sub(r'\d+.*', '', cleaned).strip()
                    if len(cleaned) > 2:
                        ingredient_counts[cleaned[:20]] = ingredient_counts.get(cleaned[:20], 0) + 1
            
            # No ingredient should appear more than once (aggregated)
            duplicates = {k: v for k, v in ingredient_counts.items() if v > 1}
            quantity_combined_ok = len(duplicates) <= 2  # allow minor tolerance
            quantity_detail = f"Duplicate ingredient entries: {duplicates}. Total items: {len(ingredient_counts)}"
        except Exception as e:
            quantity_detail = f"Error: {e}"
    add_check("shopping_list_quantities_aggregated", quantity_combined_ok, quantity_detail)

    # --- FINAL SCORE ---
    total = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total, 3)
    overall_passed = passed_checks >= 9  # must pass at least 9/12

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))