import os
import random
import json
import csv

random.seed(42)

workspace = "/workspace"

# === Directory Structure with Distractor Files ===
dirs = [
    "scripts",
    "docs",
    "reports/weekly",
    "reports/daily",
    "data/raw",
    "data/processed",
    "config",
    "logs/system",
    "logs/audit",
    "tmp",
    "archive/2024",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/nutrition_guidelines.txt": "Daily recommended intake: 2000 kcal. Protein: 50g. Carbs: 275g. Fat: 78g.\nThese are general guidelines and may vary.",
    "docs/pilot_program_brief.txt": "Corporate Wellness Pilot Q3 2025\nObjective: Validate nutrition tracking tooling for 50 employees.\nKey metrics: meal logging compliance, water intake, macro adherence.",
    "config/app_settings.json": json.dumps({"version": "3.4.0", "theme": "light", "notifications": True, "timezone": "UTC"}, indent=2),
    "config/user_profile.json": json.dumps({"name": "Test User", "age": 34, "weight_kg": 75, "height_cm": 178, "goal": "maintenance"}, indent=2),
    "logs/system/app.log": "2025-06-01 08:00:01 INFO  App started\n2025-06-01 08:00:02 INFO  Database connected\n2025-06-01 09:15:44 WARN  High memory usage detected\n",
    "logs/audit/access.log": "2025-06-01 08:01:00 USER=admin ACTION=login STATUS=success\n2025-06-01 08:05:22 USER=admin ACTION=view_report STATUS=success\n",
    "reports/weekly/sample_output.txt": "SAMPLE WEEKLY REPORT (DO NOT USE)\nThis is a placeholder report generated during system setup.",
    "reports/daily/sample_output.txt": "SAMPLE DAILY REPORT (DO NOT USE)\nPlaceholder daily report.",
    "data/processed/macros_summary_old.csv": "date,protein,carbs,fat\n2025-05-01,120,250,65\n2025-05-02,130,240,70\n",
    "archive/2024/meal_archive.json": json.dumps([{"date": "2024-12-31", "food": "New Year Cake", "calories": 450}], indent=2),
    "tmp/scratch.txt": "temp notes: check if log command accepts date param - IT DOES NOT\ncalories cmd date format: YYYY-MM-DD\n",
}
# Note: tmp/scratch.txt is intentionally misleading noise

for filepath, content in distractor_files.items():
    full = os.path.join(workspace, filepath)
    with open(full, "w") as f:
        f.write(content)

# === THE CORE PROBLEM FILE: messy meal intake CSV ===
# Columns are in a scrambled order (NOT matching CLI signature order)
# CLI order: <food_item> <calories> <protein_g> <carbs_g> <fat_g> [meal_type]
# CSV order: food_name, fat_g, protein_g, meal_type, calories, carbs_g
# The agent must reorder these to match the CLI

meal_data_raw = """\
food_name,fat_g,protein_g,meal_type,calories,carbs_g
Oatmeal with Berries,5,8,breakfast,320,58
Grilled Chicken Salad,12,42,lunch,380,14
Greek Yogurt,3,17,snack,150,20
Salmon with Quinoa,18,39,dinner,520,35
Whole Wheat Toast with Peanut Butter,14,12,breakfast,290,28
"""

with open(os.path.join(workspace, "data/raw/meal_intake_log.csv"), "w") as f:
    f.write(meal_data_raw)

# === Water intake instruction file ===
water_info = """\
WATER INTAKE RECORD - Corporate Wellness Pilot
Date: today
Employee: Test User
Total water consumed: 2350 ml
Notes: Recorded throughout the day (morning 600ml, noon 750ml, afternoon 500ml, evening 500ml).
"""
with open(os.path.join(workspace, "data/raw/water_intake.txt"), "w") as f:
    f.write(water_info)

# === Meal plan requirements file ===
plan_req = """\
Meal Plan Generation Requirements
==================================
Target: 1800 kcal per day
Duration: 4 days
Basis: Use only previously logged foods to generate the plan.
Output: Save the generated plan text to reports/meal_plan_output.txt
"""
with open(os.path.join(workspace, "data/raw/meal_plan_requirements.txt"), "w") as f:
    f.write(plan_req)

# === Additional distractors ===
with open(os.path.join(workspace, "config/macro_targets.json"), "w") as f:
    json.dump({"protein_g": 150, "carbs_g": 200, "fat_g": 60, "calories": 1800}, f, indent=2)

with open(os.path.join(workspace, "logs/system/nutrition_errors.log"), "w") as f:
    f.write("ERROR 2025-05-30: Macros report failed - no data for date\nERROR 2025-05-31: Water log missing\n")

print("Workspace initialized successfully.")
print("Key files created:")
print("  data/raw/meal_intake_log.csv  (scrambled column order)")
print("  data/raw/water_intake.txt")
print("  data/raw/meal_plan_requirements.txt")