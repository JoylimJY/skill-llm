import os
import stat
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor directory structure
distractor_dirs = [
    "corporate/wellness/reports/2023",
    "corporate/wellness/reports/2024",
    "corporate/hr/employees/onboarding",
    "corporate/hr/employees/active",
    "corporate/nutrition/guidelines",
    "corporate/nutrition/old_system",
    "tools/legacy/diet_planner",
    "tools/scripts/data_migration",
    "config/system",
    "config/user_profiles",
    "logs/2024/january",
    "logs/2024/february",
    "temp/imports",
    "temp/exports",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files with misleading content
distractors = {
    "corporate/wellness/reports/2023/annual_summary.txt": (
        "Annual Wellness Report 2023\n"
        "Total participants: 147\n"
        "Average BMI reduction: 1.2\n"
        "Program success rate: 78%\n"
    ),
    "corporate/wellness/reports/2024/q1_metrics.csv": (
        "employee_id,bmi,goal,compliance\n"
        "E001,24.5,lose,0.85\n"
        "E002,22.1,maintain,0.92\n"
        "E003,19.8,gain,0.71\n"
    ),
    "corporate/hr/employees/onboarding/checklist.txt": (
        "New Employee Onboarding Checklist:\n"
        "[ ] Badge issued\n"
        "[ ] IT setup complete\n"
        "[ ] Wellness program enrollment\n"
        "[ ] Nutrition plan setup\n"
    ),
    "corporate/hr/employees/active/roster.json": json.dumps({
        "employees": [
            {"id": "E001", "name": "Alice Wang", "department": "Engineering"},
            {"id": "E002", "name": "Bob Chen", "department": "Marketing"},
            {"id": "E003", "name": "Chen Mei", "department": "Data Science"}
        ]
    }, indent=2, ensure_ascii=False),
    "corporate/nutrition/guidelines/protein_guide.txt": (
        "Protein Requirements by Activity Level:\n"
        "Sedentary: 0.8g/kg\n"
        "Light: 1.0g/kg\n"
        "Moderate: 1.2g/kg\n"
        "Active: 1.5g/kg\n"
        "Very Active: 1.8g/kg\n"
    ),
    "corporate/nutrition/old_system/user_profiles.json": json.dumps({
        "profiles": [
            {
                "name": "Zhang Wei",
                "age": 32,
                "weight_kg": 75,
                "height_cm": 178,
                "activity": "medium",  # deliberately wrong/old format
                "objective": "weight_loss",  # deliberately wrong/old format
                "diet": "no_pork",
            }
        ]
    }, indent=2, ensure_ascii=False),
    "tools/legacy/diet_planner/README_old.txt": (
        "DEPRECATED - Legacy Diet Planner v0.3\n"
        "This system has been replaced. Do not use.\n"
        "Old commands:\n"
        "  diet-plan --user <name> --type standard\n"
        "  diet-plan --user <name> --type vegetarian\n"
        "  diet-plan --user <name> --export shopping\n"
    ),
    "tools/scripts/data_migration/migrate.py": (
        "#!/usr/bin/env python3\n"
        "# Migration script from legacy diet planner to new system\n"
        "# STATUS: incomplete\n"
        "import json\n"
        "import sys\n\n"
        "def migrate_profile(old_profile):\n"
        "    # TODO: map old fields to new format\n"
        "    pass\n\n"
        "if __name__ == '__main__':\n"
        "    print('Migration not yet implemented')\n"
    ),
    "config/system/settings.ini": (
        "[system]\n"
        "data_dir = ~/.openclaw/data\n"
        "log_level = INFO\n"
        "timezone = Asia/Shanghai\n\n"
        "[nutrition]\n"
        "default_days = 7\n"
        "currency = CNY\n"
    ),
    "config/user_profiles/template.json": json.dumps({
        "name": "TEMPLATE",
        "age": 0,
        "gender": "male|female",
        "weight": 0,
        "height": 0,
        "activity_level": "sedentary|light|moderate|active|very_active",
        "goal": "lose|maintain|gain",
        "dietary_restrictions": [],
        "allergies": []
    }, indent=2),
    "logs/2024/january/system.log": (
        "2024-01-01 08:00:00 INFO System started\n"
        "2024-01-01 08:01:23 INFO User profile created: Zhang Wei\n"
        "2024-01-01 08:02:45 INFO Plan generated: 7 days\n"
        "2024-01-01 08:03:12 INFO Shopping list exported\n"
    ),
    "logs/2024/february/system.log": (
        "2024-02-01 09:00:00 INFO System started\n"
        "2024-02-01 09:15:33 ERROR Profile creation failed: invalid activity level\n"
        "2024-02-01 09:16:01 INFO Retrying with corrected parameters\n"
        "2024-02-01 09:16:45 INFO User profile created: Li Xia\n"
    ),
    "temp/imports/new_employee_intake.txt": (
        "New Employee Nutrition Onboarding Request\n"
        "=========================================\n"
        "Employee Name: Chen Mei\n"
        "Date of Birth: 1996-03-15\n"
        "Current Age: 28\n"
        "Gender: Female\n"
        "Weight: 58 kg\n"
        "Height: 163 cm\n"
        "Activity Level: Very active (trains 6-7 days/week)\n"
        "Nutrition Goal: Build muscle mass\n"
        "Dietary Preference: Vegetarian\n"
        "Known Allergies: Peanuts, Dairy\n"
        "Requested Plan Duration: 14 days\n"
        "Shopping List Required: Yes (14 days)\n"
        "Output File: shopping_list_chen_mei.txt\n"
    ),
    "temp/exports/.gitkeep": "",
}

for filepath, content in distractors.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

print("Workspace distractor files created successfully.")
print(f"Total distractor files: {len(distractors)}")

# List all created files
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")