import json
import os
import subprocess
import sys
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── Helper: read plan from the data store ──────────────────────────────
    plan_file = Path.home() / ".local/share/mealplan/plan.json"

    def load_plan():
        if not plan_file.exists():
            return {}
        return json.loads(plan_file.read_text())

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 1: Monday meals added correctly (all 3 meals present)
    # ─────────────────────────────────────────────────────────────────────
    def check_monday_meals():
        plan = load_plan()
        monday = plan.get("monday", [])
        if not monday:
            return False, "No meals found for monday in the plan store."
        meals_by_name = {m["meal"].lower().strip(): m for m in monday}
        expected = [
            ("oatmeal porridge", 320, "breakfast"),
            ("grilled chicken salad", 480, "lunch"),
            ("beef stir fry", 610, "dinner"),
        ]
        missing = []
        wrong = []
        for name, cal, typ in expected:
            match = None
            for k, v in meals_by_name.items():
                if name in k or k in name:
                    match = v
                    break
            if match is None:
                missing.append(name)
            else:
                if match["calories"] != cal:
                    wrong.append(f"{name}: expected {cal} cal, got {match['calories']}")
                if match["type"].lower() != typ:
                    wrong.append(f"{name}: expected type '{typ}', got '{match['type']}'")
        if missing:
            return False, f"Missing monday meals: {missing}"
        if wrong:
            return False, f"Incorrect meal data: {wrong}"
        return True, f"All 3 monday meals correctly added ({len(monday)} total)."

    checks.append(run_check("monday_meals_added", check_monday_meals))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 2: Tuesday meals added correctly
    # ─────────────────────────────────────────────────────────────────────
    def check_tuesday_meals():
        plan = load_plan()
        tuesday = plan.get("tuesday", [])
        if not tuesday:
            return False, "No meals found for tuesday in the plan store."
        meals_by_name = {m["meal"].lower().strip(): m for m in tuesday}
        expected = [
            ("scrambled eggs", 290, "breakfast"),
            ("veggie wrap", 410, "lunch"),
            ("salmon pasta", 700, "dinner"),
        ]
        missing = []
        wrong = []
        for name, cal, typ in expected:
            match = None
            for k, v in meals_by_name.items():
                if name in k or k in name:
                    match = v
                    break
            if match is None:
                missing.append(name)
            else:
                if match["calories"] != cal:
                    wrong.append(f"{name}: expected {cal} cal, got {match['calories']}")
                if match["type"].lower() != typ:
                    wrong.append(f"{name}: expected type '{typ}', got '{match['type']}'")
        if missing:
            return False, f"Missing tuesday meals: {missing}"
        if wrong:
            return False, f"Incorrect meal data: {wrong}"
        return True, f"All 3 tuesday meals correctly added."

    checks.append(run_check("tuesday_meals_added", check_tuesday_meals))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 3: Wednesday meals added correctly
    # ─────────────────────────────────────────────────────────────────────
    def check_wednesday_meals():
        plan = load_plan()
        wednesday = plan.get("wednesday", [])
        if not wednesday:
            return False, "No meals found for wednesday in the plan store."
        meals_by_name = {m["meal"].lower().strip(): m for m in wednesday}
        expected = [
            ("greek yogurt parfait", 250, "breakfast"),
            ("tomato soup", 180, "lunch"),
            ("chicken tikka masala", 720, "dinner"),
        ]
        missing = []
        wrong = []
        for name, cal, typ in expected:
            match = None
            for k, v in meals_by_name.items():
                if name in k or k in name:
                    match = v
                    break
            if match is None:
                missing.append(name)
            else:
                if match["calories"] != cal:
                    wrong.append(f"{name}: expected {cal} cal, got {match['calories']}")
                if match["type"].lower() != typ:
                    wrong.append(f"{name}: expected type '{typ}', got '{match['type']}'")
        if missing:
            return False, f"Missing wednesday meals: {missing}"
        if wrong:
            return False, f"Incorrect meal data: {wrong}"
        return True, f"All 3 wednesday meals correctly added."

    checks.append(run_check("wednesday_meals_added", check_wednesday_meals))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 4: monday_nutrition.txt exists and has correct content
    # ─────────────────────────────────────────────────────────────────────
    def check_monday_nutrition_file():
        candidates = list(workspace.rglob("monday_nutrition.txt"))
        if not candidates:
            return False, "monday_nutrition.txt not found anywhere in workspace."
        f = candidates[0]
        content = f.read_text()
        checks_inner = []
        # Must mention monday
        if "monday" not in content.lower():
            checks_inner.append("missing 'monday' reference")
        # Must have total calories = 320+480+610 = 1410
        if "1410" not in content:
            checks_inner.append("missing total calorie value 1410")
        # Must list each meal type
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type.lower() not in content.lower():
                checks_inner.append(f"missing meal type '{meal_type}'")
        if checks_inner:
            return False, f"monday_nutrition.txt is incomplete: {checks_inner}. Content snippet: {content[:300]}"
        return True, f"monday_nutrition.txt found at {f.relative_to(workspace)} with correct nutrition data (total 1410 cal)."

    checks.append(run_check("monday_nutrition_file", check_monday_nutrition_file))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 5: wednesday_nutrition.txt exists and has correct content
    # ─────────────────────────────────────────────────────────────────────
    def check_wednesday_nutrition_file():
        candidates = list(workspace.rglob("wednesday_nutrition.txt"))
        if not candidates:
            return False, "wednesday_nutrition.txt not found anywhere in workspace."
        f = candidates[0]
        content = f.read_text()
        checks_inner = []
        if "wednesday" not in content.lower():
            checks_inner.append("missing 'wednesday' reference")
        # Must have total calories = 250+180+720 = 1150
        if "1150" not in content:
            checks_inner.append("missing total calorie value 1150")
        for meal_type in ["breakfast", "lunch", "dinner"]:
            if meal_type.lower() not in content.lower():
                checks_inner.append(f"missing meal type '{meal_type}'")
        if checks_inner:
            return False, f"wednesday_nutrition.txt is incomplete: {checks_inner}. Content snippet: {content[:300]}"
        return True, f"wednesday_nutrition.txt found with correct nutrition data (total 1150 cal)."

    checks.append(run_check("wednesday_nutrition_file", check_wednesday_nutrition_file))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 6: shopping_list.txt exists and covers all 3 days (9 meals)
    # ─────────────────────────────────────────────────────────────────────
    def check_shopping_list_file():
        candidates = list(workspace.rglob("shopping_list.txt"))
        if not candidates:
            return False, "shopping_list.txt not found anywhere in workspace."
        f = candidates[0]
        content = f.read_text()
        # Must mention all 9 meals across monday, tuesday, wednesday
        expected_meals = [
            "oatmeal porridge",
            "grilled chicken salad",
            "beef stir fry",
            "scrambled eggs",
            "veggie wrap",
            "salmon pasta",
            "greek yogurt parfait",
            "tomato soup",
            "chicken tikka masala",
        ]
        missing = [m for m in expected_meals if m.lower() not in content.lower()]
        if missing:
            return False, f"shopping_list.txt missing items: {missing}. Content snippet: {content[:400]}"
        # Should mention "9 total" or have 9 items
        if "9" not in content:
            return False, f"shopping_list.txt does not reference 9 total items. Content: {content[:300]}"
        return True, f"shopping_list.txt found at {f.relative_to(workspace)} with all 9 items across 3 days."

    checks.append(run_check("shopping_list_file", check_shopping_list_file))

    # ─────────────────────────────────────────────────────────────────────
    # CHECK 7: shopping command used correct multi-day comma syntax
    # (validate by re-running the command and checking it produces sensible output)
    # ─────────────────────────────────────────────────────────────────────
    def check_shopping_command_correctness():
        script = workspace / "scripts" / "script.sh"
        if not script.exists():
            return False, "scripts/script.sh not found."
        result = subprocess.run(
            ["bash", str(script), "shopping", "monday,tuesday,wednesday"],
            capture_output=True, text=True, cwd=str(workspace)
        )
        if result.returncode != 0:
            return False, f"shopping command failed: {result.stderr}"
        out = result.stdout
        if "9" not in out:
            return False, f"shopping command for 3 days did not return 9 items. Got: {out[:300]}"
        return True, f"shopping command with comma-separated days works correctly: {out[:200]}"

    checks.append(run_check("shopping_command_multi_day", check_shopping_command_correctness))

    # ─────────────────────────────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()