import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import date

workspace = sys.argv[1]
today = date.today().isoformat()

checks = []
score_total = 0.0
max_checks = 7

def run_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# Helper: load JSON safely
def load_json(path):
    with open(path) as f:
        return json.load(f)

# ============================================================
# CHECK 1: All 5 meals are logged in ~/.diet/meals.json
# ============================================================
EXPECTED_MEALS = [
    {"food": "Oatmeal with Berries",              "calories": 320, "protein_g": 8,  "carbs_g": 58, "fat_g": 5,  "meal_type": "breakfast"},
    {"food": "Grilled Chicken Salad",             "calories": 380, "protein_g": 42, "carbs_g": 14, "fat_g": 12, "meal_type": "lunch"},
    {"food": "Greek Yogurt",                      "calories": 150, "protein_g": 17, "carbs_g": 20, "fat_g": 3,  "meal_type": "snack"},
    {"food": "Salmon with Quinoa",                "calories": 520, "protein_g": 39, "carbs_g": 35, "fat_g": 18, "meal_type": "dinner"},
    {"food": "Whole Wheat Toast with Peanut Butter","calories": 290,"protein_g": 12, "carbs_g": 28, "fat_g": 14, "meal_type": "breakfast"},
]

try:
    meals_path = Path.home() / ".diet" / "meals.json"
    meals_data = load_json(meals_path)
    
    # Filter to today's entries
    today_meals = [m for m in meals_data if m.get("date") == today]
    
    found_count = 0
    missing = []
    for expected in EXPECTED_MEALS:
        matched = False
        for actual in today_meals:
            if (actual.get("food", "").strip() == expected["food"] and
                abs(float(actual.get("calories", -999)) - expected["calories"]) < 1.0 and
                abs(float(actual.get("protein_g", -999)) - expected["protein_g"]) < 0.5 and
                abs(float(actual.get("carbs_g", -999)) - expected["carbs_g"]) < 0.5 and
                abs(float(actual.get("fat_g", -999)) - expected["fat_g"]) < 0.5 and
                actual.get("meal_type", "").strip() == expected["meal_type"]):
                matched = True
                break
        if matched:
            found_count += 1
        else:
            missing.append(expected["food"])
    
    all_found = found_count == len(EXPECTED_MEALS)
    score_total += run_check(
        "All 5 meals logged with correct macros and meal types",
        all_found,
        f"Found {found_count}/{len(EXPECTED_MEALS)} correct meals. Missing: {missing}" if not all_found else f"All 5 meals correctly logged for {today}."
    )
except Exception as e:
    score_total += run_check("All 5 meals logged with correct macros and meal types", False, f"Exception reading meals.json: {e}")

# ============================================================
# CHECK 2: Meal_type correctness specifically (catches swapped macro order)
# ============================================================
try:
    meals_path = Path.home() / ".diet" / "meals.json"
    meals_data = load_json(meals_path)
    today_meals = [m for m in meals_data if m.get("date") == today]
    
    # Specifically check that breakfast meals are not tagged as snack (default)
    breakfast_meals = [m for m in today_meals if m.get("meal_type") == "breakfast"]
    dinner_meals   = [m for m in today_meals if m.get("meal_type") == "dinner"]
    lunch_meals    = [m for m in today_meals if m.get("meal_type") == "lunch"]
    
    correct_types = (len(breakfast_meals) >= 2 and len(dinner_meals) >= 1 and len(lunch_meals) >= 1)
    score_total += run_check(
        "Meal types correctly assigned (not defaulted to 'snack')",
        correct_types,
        f"Breakfast: {len(breakfast_meals)}, Lunch: {len(lunch_meals)}, Dinner: {len(dinner_meals)}, expected >=2, >=1, >=1."
    )
except Exception as e:
    score_total += run_check("Meal types correctly assigned", False, f"Exception: {e}")

# ============================================================
# CHECK 3: Macro order not swapped (protein vs fat vs carbs)
# Specifically: Oatmeal should have protein=8, carbs=58, fat=5
# A naive agent might input CSV order: fat, protein, carbs -> protein=5, carbs=8(?), fat=58
# ============================================================
try:
    meals_path = Path.home() / ".diet" / "meals.json"
    meals_data = load_json(meals_path)
    today_meals = [m for m in meals_data if m.get("date") == today]
    
    oatmeal = next((m for m in today_meals if "Oatmeal" in m.get("food", "")), None)
    if oatmeal:
        protein_ok = abs(float(oatmeal.get("protein_g", 0)) - 8.0) < 0.5
        carbs_ok   = abs(float(oatmeal.get("carbs_g", 0)) - 58.0) < 0.5
        fat_ok     = abs(float(oatmeal.get("fat_g", 0)) - 5.0) < 0.5
        macro_correct = protein_ok and carbs_ok and fat_ok
        score_total += run_check(
            "Macro order correct for Oatmeal (protein=8, carbs=58, fat=5)",
            macro_correct,
            f"Oatmeal: protein={oatmeal.get('protein_g')}, carbs={oatmeal.get('carbs_g')}, fat={oatmeal.get('fat_g')}. Expected P=8, C=58, F=5."
        )
    else:
        score_total += run_check("Macro order correct for Oatmeal", False, "Oatmeal entry not found in meals.json")
except Exception as e:
    score_total += run_check("Macro order correct for Oatmeal", False, f"Exception: {e}")

# ============================================================
# CHECK 4: Water intake logged (2350 ml today)
# ============================================================
try:
    water_path = Path.home() / ".diet" / "water.json"
    water_data = load_json(water_path)
    
    today_water = [w for w in water_data if w.get("date") == today]
    total_water = sum(float(w.get("ml", 0)) for w in today_water)
    
    water_ok = abs(total_water - 2350.0) < 1.0
    score_total += run_check(
        "Water intake of 2350ml logged for today",
        water_ok,
        f"Total water logged today: {total_water}ml. Expected: 2350ml."
    )
except Exception as e:
    score_total += run_check("Water intake logged", False, f"Exception reading water.json: {e}")

# ============================================================
# CHECK 5: macros command runs and returns data for today
# ============================================================
try:
    result = subprocess.run(
        ["bash", "scripts/script.sh", "macros", today],
        cwd=workspace,
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    has_macros = ("Protein" in output or "protein" in output) and ("Carbs" in output or "carbs" in output)
    no_error = "No data" not in output and result.returncode == 0
    score_total += run_check(
        "macros command returns nutrition breakdown for today",
        has_macros and no_error,
        f"macros output: {output[:300].strip()}"
    )
except Exception as e:
    score_total += run_check("macros command produces output", False, f"Exception: {e}")

# ============================================================
# CHECK 6: weekly report is generated and saved to reports/meal_plan_output.txt
# Actually check: plan command ran and output file exists
# ============================================================
try:
    plan_output = Path(workspace) / "reports" / "meal_plan_output.txt"
    exists = plan_output.exists()
    if exists:
        content = plan_output.read_text()
        has_plan = "Meal Plan" in content or "Day 1" in content or "breakfast" in content.lower()
        has_4days = "Day 4" in content
        score_total += run_check(
            "Meal plan (4 days, 1800 kcal) saved to reports/meal_plan_output.txt",
            has_plan and has_4days,
            f"File found. Has plan content: {has_plan}. Has Day 4: {has_4days}. Preview: {content[:200].strip()}"
        )
    else:
        score_total += run_check(
            "Meal plan saved to reports/meal_plan_output.txt",
            False,
            "File not found at /workspace/reports/meal_plan_output.txt"
        )
except Exception as e:
    score_total += run_check("Meal plan output file", False, f"Exception: {e}")

# ============================================================
# CHECK 7: weekly report runs and shows 7 days of data
# ============================================================
try:
    result = subprocess.run(
        ["bash", "scripts/script.sh", "report", "weekly", today],
        cwd=workspace,
        capture_output=True, text=True, timeout=30
    )
    output = result.stdout + result.stderr
    is_weekly = "Weekly" in output or "7 day" in output.lower() or "7-day" in output.lower()
    has_today = today in output
    score_total += run_check(
        "weekly report command executes and includes today's date",
        is_weekly and has_today,
        f"Report output preview: {output[:400].strip()}"
    )
except Exception as e:
    score_total += run_check("weekly report command", False, f"Exception: {e}")

# ============================================================
# Final score
# ============================================================
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
final_score = score_total / max_checks

result = {
    "passed": passed_checks >= 5,  # Must pass at least 5/7 checks
    "score": round(final_score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2))